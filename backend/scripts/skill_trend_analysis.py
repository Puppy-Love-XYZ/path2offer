"""技能时间趋势分析: 基于 publish_time 校准新兴技能词库
1. 月度命中率 = 该月命中技能的岗位数 / 该月总岗位数 (按发布月, 消除爬取量差异)
2. 增长率 = (近期3月均值 - 早期3月均值) / 早期均值
3. 分类: 增长↑ / 略增↗ / 平稳→ / 下降↓
4. 词库外候选新词: 高频技术词(未在词库) 的增长率
"""
import sys
import json
import re
from collections import defaultdict, Counter
from pathlib import Path
sys.path.insert(0, ".")

from sqlalchemy import text
from app.database import SessionLocal
from app.topic_discovery import _load_lexicon

db = SessionLocal()

BASE_MONTHS = ["2026-02", "2026-03", "2026-04"]   # 早期窗口
RECENT_MONTHS = ["2026-06", "2026-07", "2026-08"] # 近期窗口
MIN_MONTH_JOBS = 100    # 月度样本量下限
MIN_TOTAL_HITS = 30     # 技能总命中下限(低于此算不出可靠趋势)


def classify(growth):
    if growth >= 0.5:
        return "增长↑"
    if growth >= 0.2:
        return "略增↗"
    if growth > -0.2:
        return "平稳→"
    return "下降↓"


# 1. 月度总岗位数 (有 publish_time 的 zhilian 岗位)
month_totals = Counter()
rows = db.execute(text("""
    SELECT to_char(publish_time, 'YYYY-MM') AS m, COUNT(*)
    FROM jobs WHERE publish_time IS NOT NULL GROUP BY m
""")).fetchall()
for m, c in rows:
    month_totals[m] = c
print("== 月度岗位总量 (仅 publish_time 非空) ==")
for m in sorted(month_totals):
    print(f"  {m}: {month_totals[m]}")
valid_months = {m for m, c in month_totals.items() if c >= MIN_MONTH_JOBS}

# 2. 词库技能逐月命中岗位数
skill_month = defaultdict(Counter)
skill_tier = {}
lexicon = _load_lexicon()
all_skill_names = set()
for tier, skills in lexicon.items():
    if tier.startswith("_"):
        continue
    for s in skills:
        all_skill_names.add(s)
        skill_tier[s] = tier

rows = db.execute(text("""
    SELECT sr.skill, to_char(j.publish_time, 'YYYY-MM') AS m, COUNT(DISTINCT sr.job_id)
    FROM job_skill_relation sr
    JOIN jobs j ON j.id = sr.job_id
    WHERE j.publish_time IS NOT NULL
    GROUP BY sr.skill, m
""")).fetchall()
for s, m, c in rows:
    skill_month[s][m] = c

# 3. 计算每个新兴层级技能的趋势
def calc_trend(skill):
    hits = skill_month.get(skill, {})
    total = sum(hits.values())
    base = [hits[m] / month_totals[m] for m in BASE_MONTHS
            if m in month_totals and m in valid_months and m in hits]
    recent = [hits[m] / month_totals[m] for m in RECENT_MONTHS
              if m in month_totals and m in valid_months and m in hits]
    if total < MIN_TOTAL_HITS or not base or not recent:
        return None
    b = sum(base) / len(base)
    r = sum(recent) / len(recent)
    growth = (r - b) / max(b, 1e-6)
    return {"total": total, "base_rate": round(b, 4), "recent_rate": round(r, 4),
            "growth": round(growth, 3), "class": classify(growth)}


print("\n== 新兴层级技能趋势 (近年新兴 + 前沿探索, 按增长率降序) ==")
print(f"{'技能':<16} {'层级':<6} {'总命中':<6} {'早期率':<8} {'近期率':<8} {'增长率':<8} 分类")
trends = {}
for s in all_skill_names:
    if skill_tier.get(s) not in ("近年新兴", "前沿探索"):
        continue
    t = calc_trend(s)
    if not t:
        continue
    trends[s] = t
    print(f"{s:<16} {skill_tier[s]:<6} {t['total']:<6} {t['base_rate']:<8} {t['recent_rate']:<8} {t['growth']:<8} {t['class']}")

# 4. 词库外候选新词: 从岗位描述提取高频技术词, 算趋势
print("\n== 词库外候选新兴词 (高频且增长, 前 30) ==")
import jieba
cand_hits = defaultdict(Counter)
stopwords = set("""的 了 和 与 或 在 及 等 我们 公司 岗位 职责 要求 相关 负责 工作 经验 能力 以上 本科 学历 优先 熟练 掌握 熟悉 了解 具备 良好 具有 进行 完成 能够 使用 相关 方面 主要 内容 提供 需要 包括 以及 通过 项目 技术 产品 业务 用户 数据 系统 平台 信息 管理 开发 设计 测试 维护 支持 服务 流程 方案 团队 时间 部门 相关 专业 行业 领域 背景 一年 三年 五年 以上 学历 大学 大专 硕士 博士 毕业 应届 校招 全职 实习 工作制 双休 五险一金 薪资 待遇 福利 负责 任职 条件 优先 考虑 加分 项""".split())
# 技术词后缀启发式
TECH_SUFFIX = ("模型", "框架", "引擎", "平台", "系统", "数据库", "算法", "网络", "技术", "开发", "识别",
               "生成", "理解", "推理", "训练", "优化", "部署", "计算", "数据", "分析", "学习", "Agent",
               "GPT", "BERT", "LLM", "LLaMA", "Lang", "Prompt", "RAG", "MCP", "LoRA")
TECH_RE = re.compile(r"^[A-Za-z][A-Za-z0-9.-]{2,}$|[\u4e00-\u9fa5]{2,}")

# 抽取候选: 只扫有 publish_time 的岗位描述
all_jobs = db.execute(text("""
    SELECT j.id, to_char(j.publish_time, 'YYYY-MM') AS m, j.job_summary
    FROM jobs j WHERE j.publish_time IS NOT NULL AND j.job_summary IS NOT NULL
""")).fetchall()
print(f"参与新词挖掘的岗位: {len(all_jobs)}")
cand_month = defaultdict(Counter)   # 候选词 -> {month: 岗位数}
for jid, m, summary in all_jobs:
    if m not in valid_months:
        continue
    words = set(jieba.lcut(summary))
    for w in words:
        w = w.strip()
        if len(w) < 2 or w in stopwords or w in all_skill_names:
            continue
        if not TECH_RE.match(w):
            continue
        # 启发式: 纯英文技术词 或 中文且含技术后缀
        if w.isascii() and w.isalpha() and len(w) >= 3:
            pass  # 英文词直接当候选
        elif not any(w.endswith(suf) or suf in w for suf in TECH_SUFFIX):
            continue
        cand_month[w][m] += 1

# 筛掉总命中过低的, 算趋势
cand_trends = []
for w, hits in cand_month.items():
    total = sum(hits.values())
    if total < MIN_TOTAL_HITS:
        continue
    base = [hits[m] / month_totals[m] for m in BASE_MONTHS if m in hits and m in valid_months]
    recent = [hits[m] / month_totals[m] for m in RECENT_MONTHS if m in hits and m in valid_months]
    if not base or not recent:
        continue
    b = sum(base) / len(base)
    r = sum(recent) / len(recent)
    growth = (r - b) / max(b, 1e-6)
    cand_trends.append((w, total, round(b, 4), round(r, 4), round(growth, 3), classify(growth)))

cand_trends.sort(key=lambda x: -x[4])
for w, total, b, r, g, cls in cand_trends[:30]:
    print(f"  {w:<20} 总命中{total:<5} 早期率{b:<8} 近期率{r:<8} 增长率{g:<8} {cls}")

db.close()
