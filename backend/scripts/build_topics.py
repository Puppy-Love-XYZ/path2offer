r"""
构建岗位主题聚类 —— 独立执行脚本

用法:
  cd backend
  venv/Scripts/python.exe scripts/build_topics.py

流程:
  读取 jobs 表全量数据 -> BGE 向量化 -> UMAP 降维 ->
  HDBSCAN 聚类 -> TF-IDF 命名 -> 写入 job_topics / job_topic_relation 表

预计耗时: 5~15 分钟 (取决于机器性能和数据量)
"""
import sys
import os
import time
from pathlib import Path

# ── 路径 & 环境初始化 ─────────────────────────────────────────────────────
_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND))
os.chdir(_BACKEND)
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from dotenv import load_dotenv
load_dotenv(_BACKEND / ".env")

# ── 日志 ─────────────────────────────────────────────────────────────────
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger("build_topics")

# ── 主流程 ─────────────────────────────────────────────────────────────────
def main():
    logger.info("=" * 50)
    logger.info("开始构建岗位主题聚类")
    logger.info("=" * 50)

    from app.topic_discovery import build_topic_clusters

    result = build_topic_clusters()

    logger.info("=" * 50)
    logger.info("聚类完成!")
    logger.info("  主题数: %d", result["n_topics"])
    logger.info("  岗位数: %d", result["n_jobs"])
    logger.info("  总耗时: %.1f 秒 (%.1f 分钟)", result["elapsed"], result["elapsed"] / 60)
    logger.info("=" * 50)

    # 打印主题摘要
    print("\n主题列表:")
    print("-" * 60)
    for t in sorted(result["topics"], key=lambda x: -x["job_count"]):
        name = t["name"][:40]
        count = t["job_count"]
        top_kw = list(t["keywords"].keys())[:5]
        print(f"  [{t['cluster_id']:>3d}] {name:<42s} {count:>5d} 岗位  "
              f"关键词: {', '.join(top_kw)}")
    print("-" * 60)


if __name__ == "__main__":
    t_start = time.time()
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("用户中断")
    except Exception as e:
        logger.exception("聚类失败: %s", e)
        sys.exit(1)
    finally:
        elapsed = time.time() - t_start
        logger.info("脚本总耗时: %.1f 秒", elapsed)
