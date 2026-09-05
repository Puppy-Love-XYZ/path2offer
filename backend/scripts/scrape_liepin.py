"""
猎聘网爬虫：互联网产品/运营/技术岗位，目标 1000 条。

策略：
  1. Playwright 导航搜索页 → XHR 拦截 pc-search-job API → 获取 jobCardList
  2. requests + BeautifulSoup 并发抓取详情页 → job_summary + 福利标签
  3. jieba 分词 + 停用词过滤 → 写入 PostgreSQL jobs 表

用法：
  cd backend
  source venv/Scripts/activate
  python scripts/scrape_liepin.py
"""

import sys, os, re, json, time, logging, random
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

sys.path.insert(0, str(Path(__file__).parent.parent))
import jieba
from app.database import SessionLocal
from app.models import Job

# ── 日志 ──────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("liepin")

# ── jieba 初始化 ──────────────────────────────────────────────────────────────
_BASE = Path(__file__).parent.parent / "dataclean"
_USER_DICT = _BASE / "user_dict.txt"
_STOP_FILE = _BASE / "stopwords.txt"
if _USER_DICT.exists():
    jieba.load_userdict(str(_USER_DICT))
STOPWORDS: set = set(_STOP_FILE.read_text(encoding="utf-8").splitlines()) if _STOP_FILE.exists() else set()

# ── 爬取配置 ──────────────────────────────────────────────────────────────────
# (关键词, 最大翻页数)  每页 42 条
SEARCH_TASKS = [
    ("产品经理",        6),
    ("产品运营",        4),
    ("数据产品经理",    3),
    ("产品助理",        3),
    ("运营专员",        3),
    ("数据分析",        4),
    ("UI设计师",        3),
    ("前端工程师",      3),
    ("算法工程师",      3),
    ("测试工程师",      3),
    ("项目经理",        3),
    ("产品实习",        3),
    ("运营实习",        2),
    ("校招产品",        2),
    ("互联网运营",      2),
]

LIEPIN_SEARCH_URL = "https://www.liepin.com/zhaopin/"
DETAIL_WORKERS = 3          # 并发抓详情线程数（>5 会触发猎聘限流导致空内容）
DETAIL_TIMEOUT  = 15        # 秒
PAGE_WAIT       = 11.0      # 翻页等待（秒）——猎聘 XHR 约 8-10s 触发

# ── 文本工具 ──────────────────────────────────────────────────────────────────
def clean_text(t: str) -> str:
    if not t:
        return ""
    t = re.sub(r"<.*?>", "", t)
    t = re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9，。；：、（）()\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def cut_words(t: str) -> str:
    return " ".join(jieba.cut(t))

def remove_sw(t: str) -> str:
    return " ".join(w for w in t.split() if w not in STOPWORDS)

def parse_salary(s: str):
    """支持 '15-25k', '15k·14薪', '8000-12000元', '面议' 等格式，返回 (min_yuan, max_yuan)"""
    if not s or "面议" in s or "议" in s:
        return None, None
    s_lower = s.lower()
    nums = re.findall(r"(\d+\.?\d*)", s)
    if not nums:
        return None, None
    try:
        vals = [float(x) for x in nums[:2]]
        lo, hi = vals[0], vals[-1]
        if "k" in s_lower:
            lo, hi = lo * 1000, hi * 1000
        elif "万" in s:
            lo, hi = lo * 10000, hi * 10000
        elif lo < 200:                      # 可能是 K 简写未标注
            lo, hi = lo * 1000, hi * 1000
        if lo > 50000:                      # 年薪 → 月薪
            lo, hi = lo / 12, hi / 12
        return int(lo), int(hi)
    except Exception:
        return None, None

def jobkind_to_worktype(title: str) -> str:
    """猎聘 jobKind='2' 实为社招全职，不代表兼职；仅通过标题关键词判断。"""
    title_l = (title or "").lower()
    if "实习" in title_l or "intern" in title_l:
        return "实习"
    if "兼职" in title_l:
        return "兼职"
    return "全职"

# ── 详情页抓取 ────────────────────────────────────────────────────────────────
_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://www.liepin.com/",
})

def fetch_detail(url: str) -> dict:
    """返回 {summary, benefits, company_size}；失败时返回空字符串。
    url 直接来自 API 卡片的 job.link 字段（已含正确 ID 前缀）。
    """
    try:
        time.sleep(random.uniform(0.5, 1.5))   # 避免触发猎聘并发限流
        r = _SESSION.get(url, timeout=DETAIL_TIMEOUT)
        soup = BeautifulSoup(r.content, "html.parser")

        # 职位描述（已验证 class 有效）
        intro_el = soup.find(class_="job-intro-container")
        summary = intro_el.get_text(separator="\n", strip=True) if intro_el else ""

        # 公司规模：company-tags-box 内容如 "保险 | 100-499人"
        company_size = ""
        tags_el = soup.find(class_="company-tags-box")
        if tags_el:
            for part in tags_el.get_text(separator="|", strip=True).split("|"):
                part = part.strip()
                if "人" in part and any(c.isdigit() for c in part):
                    company_size = part
                    break

        # 福利标签（job-labels-box）
        labels_el = soup.find(class_="job-labels-box")
        benefits = "；".join(
            t.get_text(strip=True) for t in labels_el.find_all(["span", "em", "i"])
            if t.get_text(strip=True)
        ) if labels_el else ""

        return {"summary": summary, "benefits": benefits, "company_size": company_size}
    except Exception as e:
        log.debug("Detail fetch fail %s: %s", url, e)
        return {"summary": "", "benefits": "", "company_size": ""}

# ── 列表爬取（playwright 翻页） ────────────────────────────────────────────────
def scrape_list(kw: str, max_pages: int, page) -> list[dict]:
    """在已打开的 playwright page 上爬取多页，返回 jobCardList 列表"""
    collected: list[dict] = []

    def on_response(resp):
        if "pc-search-job" in resp.url and "cond-init" not in resp.url and resp.status == 200:
            try:
                b = resp.body()
                if b.startswith(b"<"):
                    return
                d = json.loads(b.decode("utf-8"))
                jobs = d.get("data", {}).get("data", {}).get("jobCardList", [])
                if jobs:
                    collected.extend(jobs)
                    tc = d.get("data", {}).get("data", {}).get("totalCount", "?")
                    log.info("  [%s] page %d → %d jobs (total=%s)",
                             kw, len(collected) // 42, len(jobs), tc)
            except Exception as e:
                log.debug("Parse error: %s", e)

    page.on("response", on_response)
    for p_idx in range(max_pages):
        url = f"{LIEPIN_SEARCH_URL}?kw={quote(kw)}&curPage={p_idx}"
        try:
            page.goto(url, wait_until="load", timeout=40000)
        except Exception:
            pass
        # 必须用 wait_for_timeout，不能用 time.sleep：
        # time.sleep 会阻塞主线程，导致 Playwright 事件循环无法分发 on_response 回调
        wait_ms = int((PAGE_WAIT + random.uniform(0.5, 1.5)) * 1000)
        page.wait_for_timeout(wait_ms)

    page.remove_listener("response", on_response)
    return collected

# ── 字段映射 ──────────────────────────────────────────────────────────────────
def map_job(raw: dict, detail: dict) -> dict | None:
    job  = raw.get("job", {})
    comp = raw.get("comp", {})

    title     = (job.get("title") or "").strip()
    comp_name = (comp.get("compName") or "").strip()
    if not title or not comp_name:
        return None

    dq       = job.get("dq") or ""
    parts    = dq.split("-", 1)
    city     = parts[0].strip()
    district = parts[1].strip() if len(parts) > 1 else ""

    salary_str          = job.get("salary") or ""
    sal_min, sal_max    = parse_salary(salary_str)

    industry_raw  = comp.get("compIndustry") or ""
    ind_parts     = [p.strip() for p in re.split(r"[/|,，、]", industry_raw) if p.strip()]
    ind_str       = "|".join(dict.fromkeys(ind_parts))   # 去重保序

    summary_raw   = detail.get("summary") or ""
    summary_clean = clean_text(summary_raw)
    benefits_raw  = detail.get("benefits") or ""
    benefits_clean = clean_text(benefits_raw)

    return {
        "job_name":                title,
        "company_name":            comp_name,
        "job_salary":              salary_str,
        "salary_min":              sal_min,
        "salary_max":              sal_max,
        "industry_name":           ind_str,
        "industry_list":           ind_parts,
        "work_city":               city,
        "city_district":           district,
        "street_name":             "",
        "work_major":              "",
        "work_type":               jobkind_to_worktype(title),
        "your_education":          job.get("requireEduLevel") or "不限",
        "working_exp":             job.get("requireWorkYears") or "不限",
        "company_size":            detail.get("company_size") or comp.get("compScale") or "",
        "job_summary":             summary_clean,
        "job_summary_cut":         cut_words(summary_clean),
        "job_summary_cut_filtered": remove_sw(cut_words(summary_clean)),
        "company_benefits":        benefits_clean,
        "company_benefits_cut":    cut_words(benefits_clean),
    }

# ── 写入数据库 ────────────────────────────────────────────────────────────────
def insert_jobs(job_dicts: list[dict]) -> int:
    db = SessionLocal()
    inserted = 0
    try:
        for jd in job_dicts:
            db.add(Job(**jd))
            inserted += 1
        db.commit()
        log.info("DB: inserted %d jobs", inserted)
    except Exception as e:
        db.rollback()
        log.error("DB insert error: %s", e)
        raise
    finally:
        db.close()
    return inserted

# ── 主流程 ────────────────────────────────────────────────────────────────────
def main():
    log.info("=== 猎聘爬虫启动 ===")
    all_raw: list[dict] = []
    seen_ids: set = set()

    # ── Phase 1: 收集列表数据 ──────────────────────────────────────────────
    log.info("Phase 1: 抓取搜索列表...")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        bpage = browser.new_page()
        stealth_sync(bpage)

        for kw, max_pg in SEARCH_TASKS:
            log.info("搜索关键词: 【%s】 最多 %d 页", kw, max_pg)
            rows = scrape_list(kw, max_pg, bpage)
            for row in rows:
                jid = row.get("job", {}).get("jobId", "")
                if jid and jid not in seen_ids:
                    seen_ids.add(jid)
                    all_raw.append(row)
            log.info("  累计唯一岗位: %d", len(all_raw))

        browser.close()

    log.info("Phase 1 完成：共 %d 条唯一岗位", len(all_raw))

    # ── Phase 2: 并发抓取详情页 ──────────────────────────────────────────
    log.info("Phase 2: 并发抓取详情页（%d workers）...", DETAIL_WORKERS)
    details: dict[str, dict] = {}  # jobId → {summary, benefits, company_size}

    # 构建 jobId → detail URL 映射（link 字段含正确 ID 前缀，不能用 jobId 拼接）
    job_detail_urls: dict[str, str] = {}
    for r in all_raw:
        jid  = r.get("job", {}).get("jobId", "")
        link = r.get("job", {}).get("link", "")
        if jid and link:
            job_detail_urls[jid] = link

    with ThreadPoolExecutor(max_workers=DETAIL_WORKERS) as ex:
        future_map = {ex.submit(fetch_detail, url): jid
                      for jid, url in job_detail_urls.items()}
        done_count = 0
        for fut in as_completed(future_map):
            jid = future_map[fut]
            try:
                details[jid] = fut.result()
            except Exception as e:
                details[jid] = {"summary": "", "benefits": "", "company_size": ""}
                log.debug("Detail error %s: %s", jid, e)
            done_count += 1
            if done_count % 50 == 0:
                log.info("  详情进度: %d / %d", done_count, len(job_detail_urls))

    log.info("Phase 2 完成")

    # ── Phase 3: 字段映射 + 入库 ─────────────────────────────────────────
    log.info("Phase 3: 字段映射 + 写入数据库...")
    job_dicts = []
    for raw in all_raw:
        jid = raw.get("job", {}).get("jobId", "")
        detail = details.get(jid, {"summary": "", "benefits": ""})
        mapped = map_job(raw, detail)
        if mapped:
            job_dicts.append(mapped)

    log.info("有效岗位数: %d", len(job_dicts))

    # 分批写入，每批 200 条
    batch_size = 200
    total_inserted = 0
    for i in range(0, len(job_dicts), batch_size):
        batch = job_dicts[i: i + batch_size]
        total_inserted += insert_jobs(batch)
        log.info("已写入 %d / %d", total_inserted, len(job_dicts))

    log.info("=== 爬虫完成，共插入 %d 条岗位 ===", total_inserted)
    print(f"\n[OK] 完成！共插入 {total_inserted} 条岗位到数据库。")
    print("提示：如需立即在岗位匹配中命中新数据，请删除 backend/app/chroma_db/ 并重启后端。")


if __name__ == "__main__":
    main()
