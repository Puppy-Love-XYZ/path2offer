"""
将新增岗位（ID >= 88959）单独 upsert 到 ChromaDB 向量库。

背景：批量 _do_index 有 95% 阈值检测，新增 19 条岗位不会触发重建。
本脚本绕过该检测，直接对指定 ID 范围做 encode + upsert。
"""
import sys
import os
from pathlib import Path

# 把 backend 目录加入 sys.path，方便 import app.*
_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND))

os.chdir(_BACKEND)          # 工作目录切到 backend，确保 chroma_db/ 路径一致
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

# ── 读取 .env ────────────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv(_BACKEND / ".env")

# ── 数据库连接 ────────────────────────────────────────────────────────────────
from app.database import SessionLocal
from app.models import Job

# ── matching 模块内的工具函数 ────────────────────────────────────────────────
from app.matching import (
    get_model,
    build_job_text,
    COLLECTION_NAME,
    _CHROMA_PATH,
)

# ── ChromaDB ─────────────────────────────────────────────────────────────────
import chromadb
from chromadb.config import Settings

# ─────────────────────────────────────────────────────────────────────────────

NEW_JOB_ID_START = 88959    # 本次新增岗位的起始 ID（含）


def main():
    db = SessionLocal()
    try:
        jobs = db.query(Job).filter(Job.id >= NEW_JOB_ID_START).order_by(Job.id).all()
        if not jobs:
            print(f"[WARN] 数据库中没有 id >= {NEW_JOB_ID_START} 的岗位，请检查是否已正确插入。")
            return

        print(f"找到 {len(jobs)} 个新岗位（id {jobs[0].id} ~ {jobs[-1].id}），开始入库...")

        # 加载 SBERT 模型
        print("加载 SBERT 模型（首次约 3s）...")
        model = get_model()

        # 构建文本 & 编码
        texts = [build_job_text(j) for j in jobs]
        print("编码向量中...")
        embeddings = model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            normalize_embeddings=True,
        ).tolist()

        # 构建 metadata（与 _do_index 完全一致，额外加 featured="1" 标记）
        metadatas = [
            {
                "job_name":     j.job_name      or "",
                "company_name": j.company_name  or "",
                "work_city":    j.work_city     or "",
                "salary_min":   j.salary_min    or 0,
                "salary_max":   j.salary_max    or 0,
                "your_education": j.your_education or "",
                "working_exp":  j.working_exp   or "",
                "industry_name": j.industry_name or "",
                "job_salary":   j.job_salary    or "",
                "company_size": j.company_size  or "",
                "featured":     "1",            # 标记为精选岗位，auto_recommend 会额外强制包含
            }
            for j in jobs
        ]
        ids = [str(j.id) for j in jobs]

        # 连接 ChromaDB 并 upsert
        print(f"连接 ChromaDB: {_CHROMA_PATH}")
        _CHROMA_PATH.mkdir(exist_ok=True)
        client = chromadb.PersistentClient(
            path=str(_CHROMA_PATH),
            settings=Settings(anonymized_telemetry=False),
        )
        col = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

        before = col.count()
        col.upsert(ids=ids, embeddings=embeddings, metadatas=metadatas)
        after = col.count()

        print(f"\n[OK] upsert 完成！向量库条目数：{before} -> {after}")
        print("新增岗位列表：")
        for j in jobs:
            print(f"  id={j.id}  {j.company_name}  {j.job_name}  "
                  f"{j.work_city}  {j.your_education}  {j.working_exp}  "
                  f"{j.job_salary}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
