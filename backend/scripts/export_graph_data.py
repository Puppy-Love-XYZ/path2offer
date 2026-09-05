"""导出主题聚类/新兴岗位/技能-岗位 三份数据为 JSON, 存入 backend/graph_base_data/"""
import json
import os
import sys
import time
sys.path.insert(0, ".")

from sqlalchemy import text
from app.database import SessionLocal
from app.models import JobTopic
from app.topic_discovery import (
    compute_emerging_jobs, TOPIC_FAMILY_MAP,
    FINE_DOMAIN_TOPICS, _assign_fine_domain,
)

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "graph_base_data")
os.makedirs(OUT_DIR, exist_ok=True)

db = SessionLocal()
t0 = time.time()

# ---------- 0. 主题领域: 细粒度主题按岗位粒度统计领域分布, 其余主题按映射表单值 ----------
from collections import Counter, defaultdict
fam_rows = db.execute(text("""
    SELECT topic_id, job_id, job_name, skill FROM job_skill_relation
""")).fetchall()
_fam_skills = defaultdict(set)
_fam_topic = {}
_fam_name = {}
for tid, jid, jn, skill in fam_rows:
    _fam_skills[jid].add(skill)
    _fam_topic[jid] = tid
    _fam_name[jid] = jn or ""
_domain_counter = defaultdict(Counter)
for jid, tid in _fam_topic.items():
    if tid in FINE_DOMAIN_TOPICS:
        _domain_counter[tid][_assign_fine_domain(_fam_name[jid], _fam_skills[jid])] += 1
    else:
        _domain_counter[tid][TOPIC_FAMILY_MAP.get(tid, "未分类")] += 1
topic_family = {}
topic_domains = {}
for tid, c in _domain_counter.items():
    total = sum(c.values()) or 1
    topic_family[tid] = c.most_common(1)[0][0]
    topic_domains[tid] = [
        {"name": k, "count": v, "ratio": round(v / total, 4)}
        for k, v in c.most_common()
    ]
print("== 0. 细粒度主题领域 (岗位多数投票) ==")
for tid in FINE_DOMAIN_TOPICS:
    print(f"  主题 {tid}: {topic_family.get(tid, '?')} -> "
          f"{[d['name'] for d in topic_domains.get(tid, [])]}")

# ---------- 1. 主题聚类表 ----------
print("== 1. 导出主题聚类表 ==")
topics = []
for t in db.query(JobTopic).order_by(JobTopic.job_count.desc()).all():
    try:
        keywords = json.loads(t.keywords_json) if t.keywords_json else {}
    except json.JSONDecodeError:
        keywords = {}
    topics.append({
        "id": t.id,
        "name": t.name,
        "job_family": topic_family.get(t.id, TOPIC_FAMILY_MAP.get(t.id, "未分类")),
        "domains": topic_domains.get(t.id, [{
            "name": TOPIC_FAMILY_MAP.get(t.id, "未分类"),
            "count": t.job_count, "ratio": 1.0,
        }]),
        "keywords": keywords,
        "job_count": t.job_count,
        "positions": (t.positions or "").split(", "),
        "skills": (t.skills_text or "").split(", "),
    })
with open(os.path.join(OUT_DIR, "topics.json"), "w", encoding="utf-8") as f:
    json.dump(topics, f, ensure_ascii=False, indent=1)
print(f"  主题 {len(topics)} 个 -> topics.json")

# ---------- 2. 新兴岗位榜单 ----------
print("== 2. 导出新兴岗位榜单 ==")
ranking = compute_emerging_jobs(db, top_n=50, min_jobs=3, min_emerging_score=1.5)
with open(os.path.join(OUT_DIR, "emerging_jobs.json"), "w", encoding="utf-8") as f:
    json.dump(ranking, f, ensure_ascii=False, indent=1)
print(f"  新兴岗位分组 {ranking['total_groups']} 个, 榜单 {len(ranking['items'])} 条 -> emerging_jobs.json")

# ---------- 3. 技能-岗位表 ----------
print("== 3. 导出技能-岗位表 ==")
rows = db.execute(text("""
    SELECT job_id, topic_id, job_name, skill, tier, is_emerging, weight
    FROM job_skill_relation
""")).fetchall()

# 每条记录的岗位领域 (与主题/榜单同口径: 细粒度主题按岗位判定, 其余按映射表)
job_family_map = {}
for jid, tid in _fam_topic.items():
    if tid in FINE_DOMAIN_TOPICS:
        job_family_map[jid] = _assign_fine_domain(_fam_name[jid], _fam_skills[jid])
    else:
        job_family_map[jid] = TOPIC_FAMILY_MAP.get(tid, "未分类")

# 仅对以下领域计算计数, 其余领域填空(0)
FAMILY_TARGET = {"技术开发", "人工智能", "大数据", "物联网", "智能系统", "工程与制造"}
# 岗位数量: 该领域下同名岗位(job_name)的岗位数
_pos_cnt = Counter((job_family_map[jid], _fam_name[jid]) for jid in _fam_topic)
# 技术数量: 该领域下该技能被使用的次数 (每岗位一条记录)
_skl_cnt = Counter()
for jid, skills in _fam_skills.items():
    for sk in skills:
        _skl_cnt[(job_family_map[jid], sk)] += 1

job_skills = []
for r in rows:
    jid, jn, sk = r[0], r[2], r[3]
    fam = job_family_map[jid]
    if fam in FAMILY_TARGET:
        position_count = _pos_cnt[(fam, jn)]
        skill_count = _skl_cnt[(fam, sk)]
    else:
        position_count = skill_count = 0
    job_skills.append({
        "job_id": r[0], "topic_id": r[1], "job_name": r[2],
        "skill": r[3], "tier": r[4],
        "is_emerging": bool(r[5]), "weight": r[6],
        "job_family": fam,
        "position_count": position_count,
        "skill_count": skill_count,
    })
with open(os.path.join(OUT_DIR, "job_skills.json"), "w", encoding="utf-8") as f:
    json.dump(job_skills, f, ensure_ascii=False, indent=1)
print(f"  技能-岗位关系 {len(job_skills)} 条 -> job_skills.json")

db.close()
print(f"\n== 完成, 耗时 {round(time.time()-t0,1)}s, 输出目录: {OUT_DIR} ==")
