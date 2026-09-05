"""
构建岗位-技能关系表 job_skill_relation:
  遍历全量岗位 → 词库匹配技能 → 写入 (job_id, topic_id, 清洗后岗位名, 技能, 层级, 新兴标记, 权重)
供"新兴岗位发现"等岗位粒度分析使用。全量重建模式, 可重复执行。
"""
import os
import sys
import time
from sqlalchemy import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal, engine
from app.models import Base, Job, JobTopicRelation, JobSkillRelation
from app.topic_discovery import extract_skills, clean_job_name, _get_emerging_weight
from app.matching import build_job_text

EMERGING_TIERS = ("近年新兴", "前沿探索")
BATCH = 2000
FLUSH_EVERY = 5000


def main():
    t0 = time.time()
    db = SessionLocal()

    # 1. 建表 (幂等)
    Base.metadata.create_all(bind=engine)

    # 2. 清空旧数据
    db.execute(text("DELETE FROM job_skill_relation"))
    db.commit()
    print("已清空旧数据")

    # 3. 岗位 → 主题 映射
    rels = db.query(JobTopicRelation.job_id, JobTopicRelation.topic_id).all()
    topic_of = {job_id: topic_id for job_id, topic_id in rels}
    print(f"岗位-主题映射: {len(topic_of)} 条")

    # 4. 分批遍历岗位并匹配技能
    cols = (Job.id, Job.job_name, Job.industry_name, Job.company_name,
            Job.work_city, Job.your_education, Job.working_exp,
            Job.company_size, Job.job_summary)

    rows = []
    total_jobs = 0
    total_skills = 0
    last_id = 0
    while True:
        batch = db.query(*cols).filter(Job.id > last_id).order_by(Job.id).limit(BATCH).all()
        if not batch:
            break
        last_id = batch[-1].id
        for j in batch:
            total_jobs += 1
            text_ = build_job_text(j)
            skills = extract_skills(text_)
            if not any(skills.values()):
                continue
            cleaned = clean_job_name(j.job_name or "")
            topic_id = topic_of.get(j.id)
            for tier, lst in skills.items():
                is_emerging = tier in EMERGING_TIERS
                for s in lst:
                    rows.append({
                        "job_id": j.id,
                        "topic_id": topic_id,
                        "job_name": cleaned or (j.job_name or "")[:50],
                        "raw_job_name": (j.job_name or "")[:200],
                        "skill": s,
                        "tier": tier,
                        "is_emerging": is_emerging,
                        "weight": _get_emerging_weight(s) if is_emerging else 1.0,
                    })
                    total_skills += 1
        if len(rows) >= FLUSH_EVERY:
            db.execute(JobSkillRelation.__table__.insert(), rows)
            db.commit()
            print(f"  已写入 {len(rows)} 条 (累计岗位 {total_jobs})")
            rows.clear()

    if rows:
        db.execute(JobSkillRelation.__table__.insert(), rows)
        db.commit()

    elapsed = round(time.time() - t0, 1)
    print(f"完成: {total_jobs} 个岗位, 命中 {total_skills} 条技能关系, 耗时 {elapsed}s")
    db.close()


if __name__ == "__main__":
    main()
