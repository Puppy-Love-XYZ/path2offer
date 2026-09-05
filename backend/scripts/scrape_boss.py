"""
BOSS直聘爬虫：产品相关岗位，目标 500 条，按最新时间排序。

策略：
  1. browser_cookie3 从本地 Edge/Chrome 读取 BOSS 登录 cookie（无需弹窗登录）
  2. 将 cookie 注入无头 Playwright Chromium → XHR 拦截 zpgeek/search/joblist.json
  3. 用 Playwright 导航后更新的 cookie → requests 并发调用 zpgeek/job/view.json 获取 JD
  4. jieba 分词 + 停用词过滤 → 写入 PostgreSQL jobs 表

前提：在本机 Edge（或 Chrome）里已登录 BOSS直聘，且浏览器保持开启状态。

用法：
  cd backend
  source venv/Scripts/activate
  python scripts/scrape_boss.py
"""

import sys, re, json, time, logging, random
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote

import requests
import browser_cookie3
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

sys.path.insert(0, str(Path(__file__).parent.parent))
import jieba
from app.database import SessionLocal
from app.models import Job

# ── 日志 ──────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("boss")

# ── jieba 初始化 ──────────────────────────────────────────────────────────────
_BASE      = Path(__file__).parent.parent / "dataclean"
_USER_DICT = _BASE / "user_dict.txt"
_STOP_FILE = _BASE / "stopwords.txt"
if _USER_DICT.exists():
    jieba.load_userdict(str(_USER_DICT))
STOPWORDS: set = (
    set(_STOP_FILE.read_text(encoding="utf-8").splitlines())
    if _STOP_FILE.exists() else set()
)

# ── 爬取配置 ──────────────────────────────────────────────────────────────────
TARGET = 500   # 目标岗位数（去重后）

# (关键词, 最大翻页数)  BOSS 每页 30 条
SEARCH_TASKS = [
    ("产品经理",      8),   # ≈240 条
    ("产品运营",      5),   # ≈150 条
    ("数据产品经理",  3),   # ≈90  条
    ("产品助理",      3),   # ≈90  条
    ("增长产品",      2),   # ≈60  条
    ("产品实习",      4),   # ≈120 条
    ("产品总监",      2),   # ≈60  条
    ("商业产品",      2),   # ≈60  条
]

BOSS_SEARCH_URL = "https://www.zhipin.com/web/geek/job"
BOSS_DETAIL_API = "https://www.zhipin.com/wapi/zpgeek/job/view.json"

DETAIL_WORKERS = 3      # 并发数（>5 易触发 BOSS 限流）
DETAIL_TIMEOUT = 15     # 秒
PAGE_WAIT      = 7.0    # BOSS XHR 触发约 3-5s，留 7s 余量

# ── 从本地浏览器提取 BOSS cookie ──────────────────────────────────────────────
def get_boss_cookies_for_playwright() -> list[dict]:
    """
    依次尝试 Edge / Chrome，返回可直接传给 context.add_cookies() 的列表。
    Chrome 在 Windows 上需要管理员权限；Edge 不需要。
    """
    for fn, name in [
        (browser_cookie3.edge,   "Edge"),
        (browser_cookie3.chrome, "Chrome"),
    ]:
        try:
            jar = fn(domain_name=".zhipin.com")
            cookies = []
            for c in jar:
                cookies.append({
                    "name":     c.name,
                    "value":    c.value,
                    "domain":   c.domain if c.domain else ".zhipin.com",
                    "path":     c.path   if c.path   else "/",
                    "secure":   bool(c.secure),
                    "httpOnly": False,
                    "sameSite": "None",
                })
            if cookies:
                log.info("从 %s 读取到 %d 个 BOSS cookie", name, len(cookies))
                return cookies
        except Exception as e:
            log.debug("%s cookie 读取失败: %s", name, e)
    return []

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
    """支持 '15-25K·14薪', '30K以上', '8K以下', '面议' 等格式"""
    if not s or "面议" in s:
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
        elif lo < 200:
            lo, hi = lo * 1000, hi * 1000
        if lo > 50000:
            lo, hi = lo / 12, hi / 12
        return int(lo), int(hi)
    except Exception:
        return None, None

def jobtype_to_worktype(job_type, title: str) -> str:
    title_l = (title or "").lower()
    if "实习" in title_l or "intern" in title_l:
        return "实习"
    if "兼职" in title_l:
        return "兼职"
    if str(job_type) == "1":
        return "实习"
    return "全职"

# ── requests session（Phase 2 详情用） ────────────────────────────────────────
def make_session(playwright_cookies: list[dict]) -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept":           "application/json, text/plain, */*",
        "Accept-Language":  "zh-CN,zh;q=0.9",
        "X-Requested-With": "XMLHttpRequest",
        "Referer":          "https://www.zhipin.com/",
    })
    for c in playwright_cookies:
        session.cookies.set(
            c["name"], c["value"],
            domain=c.get("domain", ".zhipin.com")
        )
    return session

def fetch_detail(encrypt_id: str, session: requests.Session) -> dict:
    """调用 BOSS 详情 API，返回 {summary, benefits}"""
    try:
        time.sleep(random.uniform(0.6, 1.4))
        url = (f"{BOSS_DETAIL_API}?encryptJobId={encrypt_id}"
               "&lid=&sourceType=0&city=&securityId=")
        r = session.get(
            url, timeout=DETAIL_TIMEOUT,
            headers={"Referer": f"https://www.zhipin.com/job_detail/{encrypt_id}.html"}
        )
        d = r.json()
        if d.get("code") != 0:
            log.debug("Detail API code=%s for %s", d.get("code"), encrypt_id)
            return {"summary": "", "benefits": ""}

        job_info = (d.get("zpData") or {}).get("jobInfo") or {}
        raw_desc = job_info.get("postDescription") or ""
        summary  = BeautifulSoup(raw_desc, "html.parser").get_text(
            separator="\n", strip=True
        )
        labels   = job_info.get("jobLabels") or []
        skills   = job_info.get("skills")    or []
        benefits = "；".join(str(x) for x in list(labels) + list(skills) if x)
        return {"summary": summary, "benefits": benefits}
    except Exception as e:
        log.debug("Detail fail %s: %s", encrypt_id, e)
        return {"summary": "", "benefits": ""}

# ── 列表爬取（playwright XHR 拦截） ──────────────────────────────────────────
def scrape_list(kw: str, max_pages: int, page) -> list[dict]:
    """XHR 拦截 BOSS 搜索结果，返回 jobList 原始列表"""
    collected: list[dict] = []

    def on_response(resp):
        if "zpgeek/search/joblist.json" in resp.url and resp.status == 200:
            try:
                b = resp.body()
                if b.startswith(b"<"):
                    return
                d    = json.loads(b.decode("utf-8"))
                zp   = d.get("zpData") or d.get("data") or {}
                jobs = zp.get("jobList") or []
                if jobs and isinstance(jobs, list):
                    collected.extend(jobs)
                    tc = zp.get("totalCount", "?")
                    log.info("  [%s] page %d → %d jobs (total=%s)",
                             kw, (len(collected) - 1) // 30 + 1, len(jobs), tc)
                elif d.get("code") not in (0, None):
                    log.warning("  [%s] API code=%s: %s",
                                kw, d.get("code"), d.get("message", ""))
            except Exception as e:
                log.debug("Parse error: %s", e)

    page.on("response", on_response)
    for p_idx in range(1, max_pages + 1):
        url = (f"{BOSS_SEARCH_URL}?query={quote(kw)}"
               f"&page={p_idx}&sortType=2")
        try:
            page.goto(url, wait_until="load", timeout=40000)
        except Exception:
            pass
        wait_ms = int((PAGE_WAIT + random.uniform(0.5, 1.5)) * 1000)
        page.wait_for_timeout(wait_ms)

    page.remove_listener("response", on_response)
    return collected

# ── 字段映射 ──────────────────────────────────────────────────────────────────
def map_job(raw: dict, detail: dict) -> dict | None:
    title     = (raw.get("jobName")   or "").strip()
    comp_name = (raw.get("brandName") or "").strip()
    if not title or not comp_name:
        return None

    city     = (raw.get("cityName")     or "").strip()
    district = (raw.get("areaDistrict") or "").strip()

    salary_str       = raw.get("salaryDesc") or ""
    sal_min, sal_max = parse_salary(salary_str)

    industry_raw = raw.get("brandIndustry") or ""
    ind_parts    = [p.strip() for p in re.split(r"[/|,，、]", industry_raw) if p.strip()]
    ind_str      = "|".join(dict.fromkeys(ind_parts))

    summary_clean  = clean_text(detail.get("summary")  or "")
    benefits_clean = clean_text(detail.get("benefits") or "")

    return {
        "job_name":                 title,
        "company_name":             comp_name,
        "job_salary":               salary_str,
        "salary_min":               sal_min,
        "salary_max":               sal_max,
        "industry_name":            ind_str,
        "industry_list":            ind_parts,
        "work_city":                city,
        "city_district":            district,
        "street_name":              "",
        "work_major":               "",
        "work_type":                jobtype_to_worktype(raw.get("jobType"), title),
        "your_education":           raw.get("jobDegree")      or "不限",
        "working_exp":              raw.get("jobExperience")  or "不限",
        "company_size":             raw.get("brandScaleName") or "",
        "job_summary":              summary_clean,
        "job_summary_cut":          cut_words(summary_clean),
        "job_summary_cut_filtered": remove_sw(cut_words(summary_clean)),
        "company_benefits":         benefits_clean,
        "company_benefits_cut":     cut_words(benefits_clean),
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
    log.info("=== BOSS直聘爬虫启动，目标 %d 条 ===", TARGET)

    # ── Phase 0: 读取本地浏览器 cookie ────────────────────────────────────
    boss_cookies = get_boss_cookies_for_playwright()
    if not boss_cookies:
        log.error("未能读取到 BOSS cookie，请确认已在 Edge/Chrome 登录 BOSS直聘。")
        print("\n[ERR] 请在 Edge 或 Chrome 浏览器中登录 BOSS直聘 后重新运行脚本。")
        return

    all_raw:  list[dict] = []
    seen_ids: set        = set()
    playwright_cookies:  list[dict] = []

    # ── Phase 1: 无头 Playwright + 注入 cookie，XHR 拦截搜索列表 ──────────
    log.info("Phase 1: 抓取搜索列表（无头浏览器，sortType=2 最新）...")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        # 注入从本地浏览器读取的 cookie
        context.add_cookies(boss_cookies)

        bpage = context.new_page()
        stealth_sync(bpage)

        # 验证登录态：访问搜索页看 XHR 是否正常返回
        log.info("验证登录态...")
        test_ok = False

        def on_test(resp):
            nonlocal test_ok
            if "zpgeek/search/joblist.json" in resp.url and resp.status == 200:
                try:
                    d  = json.loads(resp.body().decode())
                    zp = d.get("zpData") or {}
                    if zp.get("jobList"):
                        test_ok = True
                except Exception:
                    pass

        bpage.on("response", on_test)
        bpage.goto(
            f"{BOSS_SEARCH_URL}?query={quote('产品经理')}&page=1&sortType=2",
            wait_until="load", timeout=40000
        )
        bpage.wait_for_timeout(8000)
        bpage.remove_listener("response", on_test)

        if not test_ok:
            log.error("Cookie 已失效或 BOSS 拒绝请求，请在浏览器重新登录 BOSS 后再运行。")
            browser.close()
            return
        log.info("登录态验证成功，开始正式抓取")

        # 已经抓了第一页（产品经理 p1），把它加进来
        # 重新跑完整的搜索
        for kw, max_pg in SEARCH_TASKS:
            if len(seen_ids) >= TARGET:
                log.info("已达目标 %d 条，跳过剩余关键词", TARGET)
                break
            log.info("搜索关键词: [%s]  最多 %d 页", kw, max_pg)
            rows = scrape_list(kw, max_pg, bpage)
            added = 0
            for row in rows:
                eid = row.get("encryptJobId") or ""
                if eid and eid not in seen_ids:
                    seen_ids.add(eid)
                    all_raw.append(row)
                    added += 1
            log.info("  本轮新增 %d 条，累计唯一岗位: %d", added, len(all_raw))

        playwright_cookies = context.cookies(urls=["https://www.zhipin.com"])
        browser.close()

    log.info("Phase 1 完成：共 %d 条唯一岗位", len(all_raw))

    if not all_raw:
        log.error("未抓到任何岗位！")
        return

    # ── Phase 2: 并发抓取岗位详情 ─────────────────────────────────────────
    log.info("Phase 2: 并发抓取岗位详情（%d workers）...", DETAIL_WORKERS)
    session = make_session(playwright_cookies)
    details: dict[str, dict] = {}

    with ThreadPoolExecutor(max_workers=DETAIL_WORKERS) as ex:
        future_map = {
            ex.submit(fetch_detail, row["encryptJobId"], session): row["encryptJobId"]
            for row in all_raw if row.get("encryptJobId")
        }
        done = 0
        for fut in as_completed(future_map):
            eid = future_map[fut]
            try:
                details[eid] = fut.result()
            except Exception as e:
                details[eid] = {"summary": "", "benefits": ""}
                log.debug("Detail error %s: %s", eid, e)
            done += 1
            if done % 50 == 0:
                has_sum = sum(1 for v in details.values() if v.get("summary"))
                log.info("  详情进度: %d / %d（有描述: %d）",
                         done, len(future_map), has_sum)

    has_sum_total = sum(1 for v in details.values() if v.get("summary"))
    log.info("Phase 2 完成：%d / %d 条有岗位描述", has_sum_total, len(details))

    # ── Phase 3: 字段映射 + 入库 ─────────────────────────────────────────
    log.info("Phase 3: 字段映射 + 写入数据库...")
    job_dicts = []
    for raw in all_raw:
        eid    = raw.get("encryptJobId", "")
        detail = details.get(eid, {"summary": "", "benefits": ""})
        mapped = map_job(raw, detail)
        if mapped:
            job_dicts.append(mapped)

    log.info("有效岗位数: %d", len(job_dicts))

    total_inserted = 0
    for i in range(0, len(job_dicts), 200):
        total_inserted += insert_jobs(job_dicts[i: i + 200])
        log.info("已写入 %d / %d", total_inserted, len(job_dicts))

    log.info("=== BOSS爬虫完成，共插入 %d 条岗位 ===", total_inserted)
    print(f"\n[OK] 完成！共插入 {total_inserted} 条岗位到数据库。")
    print("提示：如需立即在岗位匹配中命中新数据，请删除 backend/app/chroma_db/ 并重启后端。")


if __name__ == "__main__":
    main()
