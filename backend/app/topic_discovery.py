"""
新兴主题发现 —— 主题建模模块
阶段 1: BGE 向量化 + UMAP 降维 + HDBSCAN 聚类 + TF-IDF 命名
"""

import json
import logging
import numpy as np
from collections import Counter, defaultdict
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ============================================================
# 常量
# ============================================================

MODEL_NAME = "BAAI/bge-small-zh-v1.5"
UMAP_N_COMPONENTS = 5          # 最终降维目标维度
UMAP_INTERMEDIATE = 50         # 中间维度 (768→50→5, 两段降维更稳定)
HDBSCAN_MIN_CLUSTER_SIZE = 300 # 最小簇大小 → 减少碎片化
HDBSCAN_MIN_SAMPLES = 10       # 核心点邻域样本数
HDBSCAN_CLUSTER_SELECTION_EPSILON = 1.0  # 更大 → 更激进地合并相邻簇
BATCH_SIZE = 512               # 向量化批大小, 避免 OOM
MERGE_COSINE_THRESHOLD = 0.05  # 只合并 cos_sim > 0.95 的簇 (0.05=余弦距离)


# ============================================================
# 模型加载 (复用 matching.py 的 bge 模型)
# ============================================================

def _get_embedding_model():
    """获取全局 bge-small-zh 嵌入模型实例"""
    from .matching import get_model as _get_bge_model
    return _get_bge_model()


# ============================================================
# 阶段 1: 数据加载
# ============================================================

def load_job_texts(db: Session) -> List[dict]:
    """
    从 jobs 表读取全量岗位的文本和元数据。
    返回: [{"id": int, "text": str, "job_name": str, "industry": str}, ...]
    """
    from sqlalchemy import text

    rows = db.execute(text("""
        SELECT id, job_name, industry_name, company_name, work_city,
               your_education, working_exp, company_size, job_summary
        FROM bigdata_recruit_job
        WHERE job_name IS NOT NULL AND job_summary IS NOT NULL
    """)).fetchall()

    results = []
    for row in rows:
        # 复用 matching.py 的 build_job_text 逻辑, 构造统一的文本
        from .matching import build_job_text as _build
        # 构造一个简易对象传给 build_job_text
        class _J:
            pass
        j = _J()
        j.job_name = row.job_name
        j.industry_name = row.industry_name
        j.company_name = row.company_name
        j.work_city = row.work_city
        j.your_education = row.your_education
        j.working_exp = row.working_exp
        j.company_size = row.company_size
        j.job_summary = row.job_summary
        text = _build(j)
        results.append({
            "id": row.id,
            "text": text,
            "job_name": row.job_name or "",
            "industry": row.industry_name or "",
        })

    logger.info("加载岗位文本: %d 条", len(results))
    return results


# ============================================================
# 阶段 1: 向量化
# ============================================================

def encode_texts(texts: List[str]) -> np.ndarray:
    """
    批量向量化, 返回 (N, 768) 的 float32 矩阵。
    分批编码避免一次性加载过多数据到 GPU/内存。
    """
    model = _get_embedding_model()
    all_vectors = []

    total = len(texts)
    for start in range(0, total, BATCH_SIZE):
        batch = texts[start : start + BATCH_SIZE]
        vecs = model.encode(batch, show_progress_bar=False, normalize_embeddings=True)
        all_vectors.append(vecs)
        pct = min(100, round((start + len(batch)) / total * 100))
        logger.info("向量化进度: %d/%d (%d%%)", start + len(batch), total, pct)

    result = np.vstack(all_vectors).astype(np.float32)
    logger.info("向量化完成, 形状: %s", result.shape)
    return result


# ============================================================
# 阶段 1: 降维
# ============================================================

def reduce_dimensions(vectors: np.ndarray) -> np.ndarray:
    """
    UMAP 两段降维: 768 → 50 → 5。
    两段降维比直接到 5 维保留更多结构信息。
    """
    import umap

    n = vectors.shape[0]
    # uber关小参数加速大数据集
    if n > 10000:
        n_neighbors = 30
        n_epochs = 200
    else:
        n_neighbors = 15
        n_epochs = 500

    logger.info("UMAP 第一段: %d → %d", vectors.shape[1], UMAP_INTERMEDIATE)
    reducer1 = umap.UMAP(
        n_components=UMAP_INTERMEDIATE,
        n_neighbors=n_neighbors,
        min_dist=0.1,
        metric="cosine",
        random_state=42,
        n_epochs=n_epochs,
        verbose=True,
    )
    intermediate = reducer1.fit_transform(vectors)
    logger.info("UMAP 中间结果形状: %s", intermediate.shape)

    logger.info("UMAP 第二段: %d → %d", UMAP_INTERMEDIATE, UMAP_N_COMPONENTS)
    reducer2 = umap.UMAP(
        n_components=UMAP_N_COMPONENTS,
        n_neighbors=min(15, n_neighbors),
        min_dist=0.05,
        metric="euclidean",
        random_state=42,
        verbose=True,
    )
    reduced = reducer2.fit_transform(intermediate)
    logger.info("UMAP 降维完成, 最终形状: %s", reduced.shape)
    return reduced.astype(np.float32)


# ============================================================
# 阶段 1: 聚类
# ============================================================

def cluster_jobs(reduced: np.ndarray) -> Tuple[np.ndarray, dict]:
    """
    HDBSCAN 聚类。
    返回:
      labels: (N,) 整数标签数组, -1 表示噪音点
      info: {"n_clusters": int, "n_noise": int, "cluster_sizes": dict}
    """
    import hdbscan

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=HDBSCAN_MIN_CLUSTER_SIZE,
        min_samples=HDBSCAN_MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_epsilon=HDBSCAN_CLUSTER_SELECTION_EPSILON,
        core_dist_n_jobs=-1,
    )
    labels = clusterer.fit_predict(reduced)

    # 统计
    unique, counts = np.unique(labels, return_counts=True)
    n_noise = counts[unique == -1].sum() if -1 in unique else 0
    n_clusters = len([u for u in unique if u >= 0])
    cluster_sizes = {int(u): int(c) for u, c in zip(unique, counts) if u >= 0}

    logger.info("HDBSCAN 聚类完成: %d 个簇, %d 个噪音点", n_clusters, n_noise)
    logger.info("簇大小分布: %s",
                sorted(cluster_sizes.items(), key=lambda x: -x[1])[:10])

    return labels, {
        "n_clusters": n_clusters,
        "n_noise": int(n_noise),
        "cluster_sizes": cluster_sizes,
    }


# ============================================================
# 阶段 1: 噪音点处理
# ============================================================

def assign_noise_to_clusters(
    labels: np.ndarray, vectors: np.ndarray
) -> np.ndarray:
    """
    将 HDBSCAN 标记为 -1 的噪音点, 用余弦相似度分配到最近的合法簇。
    同时降低这些点的置信度。
    返回: 修正后的 labels (无 -1)
    """
    from sklearn.neighbors import NearestNeighbors

    labels = labels.copy()
    noise_mask = labels == -1
    n_noise = noise_mask.sum()
    if n_noise == 0:
        return labels

    valid_labels = labels[~noise_mask]
    valid_vectors = vectors[~noise_mask]
    noise_vectors = vectors[noise_mask]

    logger.info("将 %d 个噪音点分配到最近簇...", n_noise)
    nn = NearestNeighbors(n_neighbors=1, metric="cosine")
    nn.fit(valid_vectors)
    _, indices = nn.kneighbors(noise_vectors)

    labels[noise_mask] = valid_labels[indices.flatten()]
    logger.info("噪音点分配完成, 剩余噪音: %d", (labels == -1).sum())
    return labels


# ============================================================
# 阶段 1: 簇合并 (post-merge)
# ============================================================

def merge_similar_clusters(
    labels: np.ndarray, vectors: np.ndarray,
    cosine_threshold: float = MERGE_COSINE_THRESHOLD,
) -> np.ndarray:
    """
    小簇 → 大簇 单向合并。不连锁：大簇作为合并目标后不再作为源继续合并。
    阈值: 簇中心 cos_sim > (1-threshold) → 合并。
    """
    labels = labels.copy()
    unique = sorted(set(labels))

    centroids = {}
    sizes = {}
    for cid in unique:
        mask = labels == cid
        centroids[cid] = vectors[mask].mean(axis=0)
        sizes[cid] = mask.sum()

    sorted_clusters = sorted(unique, key=lambda c: sizes[c])
    merge_map = {}
    used_as_target = set()  # 已作为合并目标的簇, 不能再作为源

    for cid in sorted_clusters:
        if cid in merge_map or cid in used_as_target:
            continue
        best_target = None
        best_sim = -1.0
        for other in unique:
            if other == cid or other in merge_map:
                continue
            cos_sim = float(np.dot(centroids[cid], centroids[other]) /
                            (np.linalg.norm(centroids[cid]) * np.linalg.norm(centroids[other]) + 1e-8))
            if cos_sim > best_sim:
                best_sim = cos_sim
                best_target = other

        if best_sim > (1.0 - cosine_threshold) and best_target is not None:
            merge_map[cid] = best_target
            used_as_target.add(best_target)
            logger.info("合并: 簇%d(%d岗) → 簇%d(%d岗), cos_sim=%.3f",
                        cid, sizes[cid], best_target, sizes[best_target], best_sim)

    for src, dst in merge_map.items():
        labels[labels == src] = dst

    if merge_map:
        new_unique = len(set(labels))
        logger.info("合并完成: %d→%d 个簇", len(unique), new_unique)

    return labels


# ============================================================
# 阶段 1: TF-IDF 主题命名
# ============================================================

def _tokenize_chinese(text: str) -> List[str]:
    """jieba 分词, 过滤单字和纯数字"""
    import jieba
    words = jieba.lcut(text)
    return [w.strip() for w in words
            if len(w.strip()) >= 2 and not w.strip().isdigit()]


# 各层级展示配额: 传统基础(各领域代表词)为主, 主流成熟次之, 新兴/前沿 各留少量坑位
# 避免"主流成熟先填满"导致非 IT 主题被 IT 词污染
SKILL_TIER_QUOTAS = {"传统基础": 8, "主流成熟": 4, "近年新兴": 2, "前沿探索": 1}


def select_topic_skills(cluster_jobs: List[dict], top_n: int = 15) -> str:
    """
    对主题内所有岗位做技能"对号入座"统计, 返回 top-N 技能串 (逗号分隔)。
    规则:
      1. extract_skills 已过滤黑名单词 (C/Go/CV 等易误匹配词)
      2. 最低命中数门槛: 每个技能至少出现在 max(5, 1%岗位数) 条岗位中,
         过滤极少数岗位(如个别编程教师)带来的 IT 噪音
      3. 各层级按配额取 top, 各领域代表词(教育/医疗等)不会被 IT 词挤掉
    """
    from collections import Counter

    skill_counter: Dict[str, Counter] = {
        "传统基础": Counter(),
        "主流成熟": Counter(),
        "近年新兴": Counter(),
        "前沿探索": Counter(),
    }
    for j in cluster_jobs:
        skills = extract_skills(j.get("text", ""))
        for tier in skill_counter:
            for s in set(skills.get(tier, [])):
                skill_counter[tier][s] += 1

    n_jobs = len(cluster_jobs)
    min_hits = max(5, int(n_jobs * 0.01))  # 至少 5 条, 且 ≥1% 岗位

    top_skills = []
    for tier, quota in SKILL_TIER_QUOTAS.items():
        for skill, cnt in skill_counter[tier].most_common():
            if cnt < min_hits:
                break  # most_common 降序, 后续技能只会更少
            top_skills.append(skill)
            if len(top_skills) >= quota:
                break

    return ", ".join(top_skills[:top_n])


# ============================================================
# 岗位名清洗 (用于岗位粒度聚合, 如新兴岗位发现)
# ============================================================

# 常见城市名, 用于去除岗位名中的"城市-xxx"或"xxx-城市"噪音
_CITY_LIST = (
    "北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "南京", "苏州", "重庆",
    "西安", "天津", "长沙", "郑州", "东莞", "青岛", "沈阳", "大连", "厦门", "福州",
    "济南", "合肥", "昆明", "哈尔滨", "佛山", "无锡", "宁波", "温州", "泉州", "南昌",
    "贵阳", "兰州", "太原", "石家庄", "南宁", "乌鲁木齐", "呼和浩特", "长春", "徐州",
    "常州", "南通", "嘉兴", "金华", "台州", "绍兴", "湖州", "中山", "珠海", "惠州",
    "扬州", "盐城", "泰州", "镇江", "淮安", "潍坊", "烟台", "临沂", "济宁", "淄博",
    "唐山", "保定", "洛阳", "南阳", "宜昌", "襄阳", "桂林", "柳州", "遵义", "绵阳",
    "德阳", "马鞍山", "芜湖", "蚌埠", "五家渠",
)


def clean_job_name(name: str) -> str:
    """清洗岗位名: 去括号备注/年份/远程/双休/薪资/城市等噪音, 保留核心岗位词"""
    import re
    if not name:
        return ""
    # 1. 括号备注 (全半角 + 方头括号)
    name = re.sub(r"[（(【\[][^（）()【\]\]]*?[)）】\]]", "", name)
    # 2. 年份校招/批次
    name = re.sub(r"\d{4}\s*[届校招批]*", "", name)
    # 3. 办公方式
    name = re.sub(r"(远程|居家|线上|自由)?办公", "", name)
    # 4. 福利/作息
    name = re.sub(r"(双休|单休|周末双休|五险一金|六险一金|包吃住|包食宿)", "", name)
    # 5. 薪资/招聘修饰
    name = re.sub(r"(急招|诚聘|高薪|月入[一二两三四五六七八九十百千0-9]+万)", "", name)
    # 6. 城市前后缀 (破折号后可带空格, 如 "算法工程师 - AI方向 - 上海")
    city = "|".join(_CITY_LIST)
    name = re.sub(rf"^(?:{city})市?[-·—]\s*", "", name)
    name = re.sub(rf"[-·—]\s*(?:{city})市?$", "", name)
    # 7. 清理残留的"的/等/及"前缀和分隔符
    name = re.sub(r"^[的及等]+", "", name)
    return name.strip(" ·,，-—_|、/ ")


def name_topics(
    labels: np.ndarray,
    job_data: List[dict],
    top_n_name: int = 5,
    top_n_skill: int = 10,
    top_n_positions: int = 10,
    top_n_tech_skills: int = 15,
) -> List[dict]:
    """
    对每个簇:
    - 主题名: TF-IDF top-5 职位关键词
    - keywords: TF-IDF top-10 描述关键词
    - positions_str: 最高频的 top-N 岗位名称 (逗号分隔)
    - skills_str: 从技能词库匹配到的 top-N 技能 (逗号分隔)
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from collections import Counter

    unique_labels = sorted(set(labels))
    topics = []

    for cid in unique_labels:
        indices = np.where(labels == cid)[0]
        cluster_jobs = [job_data[i] for i in indices]

        # 主题名
        job_names = [" ".join(_tokenize_chinese(j["job_name"]))
                     for j in cluster_jobs]
        try:
            vec = TfidfVectorizer(max_features=top_n_name, token_pattern=r"(?u)\b\w+\b")
            vec.fit_transform(job_names)
            name_words = {w: round(s, 4) for w, s in
                          zip(vec.get_feature_names_out(), vec.idf_)}
            name_sorted = sorted(name_words.items(), key=lambda x: x[1])
            cluster_name = " · ".join([w for w, _ in name_sorted[:top_n_name]])
        except Exception:
            cluster_name = cluster_jobs[0]["job_name"][:30]

        # 最高频岗位名称
        raw_job_names = [j["job_name"] for j in cluster_jobs if j["job_name"]]
        job_counter = Counter(raw_job_names)
        top_positions = [name for name, _ in job_counter.most_common(top_n_positions)]
        positions_str = ", ".join(top_positions)

        # 从技能词库匹配技能 (黑名单过滤 + 最低命中数门槛 + 各层级配额)
        skills_str = select_topic_skills(cluster_jobs, top_n=top_n_tech_skills)

        # 原有关键词
        full_texts = [" ".join(_tokenize_chinese(j["text"]))
                      for j in cluster_jobs]
        try:
            vec2 = TfidfVectorizer(
                max_features=top_n_skill * 2,
                token_pattern=r"(?u)\b\w+\b",
                max_df=0.8,
                min_df=2,
            )
            vec2.fit_transform(full_texts)
            skill_words = {w: round(s, 4) for w, s in
                           zip(vec2.get_feature_names_out(), vec2.idf_)}
            skill_sorted = sorted(skill_words.items(), key=lambda x: x[1])[:top_n_skill]
            keywords = {w: s for w, s in skill_sorted}
        except Exception:
            keywords = {}

        topics.append({
            "cluster_id": int(cid),
            "name": cluster_name,
            "keywords": keywords,
            "job_count": len(indices),
            "positions_str": positions_str,
            "skills_str": skills_str,
        })

        logger.info("主题 [%d] %s (%d 岗位), 岗位: %s",
                     cid, cluster_name, len(indices), positions_str[:60])

    return topics


# ============================================================
# 阶段 1: 计算簇中心向量
# ============================================================

def compute_centroids(
    labels: np.ndarray, vectors: np.ndarray
) -> Dict[int, np.ndarray]:
    """计算每个簇的中心向量 (768维)"""
    centroids = {}
    for cid in sorted(set(labels)):
        mask = labels == cid
        centroids[int(cid)] = vectors[mask].mean(axis=0)
    return centroids


# ============================================================
# 阶段 1: 结果入库
# ============================================================

def save_topics_to_db(
    db: Session,
    topics_data: List[dict],
    labels: np.ndarray,
    job_data: List[dict],
    centroids: Dict[int, np.ndarray],
):
    """
    将聚类结果写入 job_topics 和 job_topic_relation 表。
    先清空旧数据再插入新数据 (全量重建模式)。
    """
    from .models import JobTopic, JobTopicRelation
    from sqlalchemy import text

    logger.info("清空旧主题数据...")
    # job_skill_relation 外键引用了 job_topics.topic_id, 需先解除引用
    # (该表后续会由 build_job_skills.py 用新主题 id 重建)
    db.execute(text("UPDATE job_skill_relation SET topic_id = NULL"))
    db.execute(text("DELETE FROM job_topic_relation"))
    db.execute(text("DELETE FROM job_topics"))
    db.commit()

    # 写主题
    cluster_to_topic_id = {}
    for t in topics_data:
        cid = t["cluster_id"]
        centroid = centroids.get(cid)
        centroid_json = json.dumps(
            [round(float(v), 6) for v in centroid], ensure_ascii=False
        ) if centroid is not None else None

        topic = JobTopic(
            name=t["name"],
            keywords_json=json.dumps(t["keywords"], ensure_ascii=False),
            job_count=t["job_count"],
            centroid_json=centroid_json,
            positions=t.get("positions_str", ""),
            skills_text=t.get("skills_str", ""),
        )
        db.add(topic)
        db.flush()  # 获取自增 id
        cluster_to_topic_id[cid] = topic.id

    logger.info("主题写入完成: %d 条", len(topics_data))

    # 写关联 (批量插入)
    relations = []
    for i, job_dict in enumerate(job_data):
        cid = int(labels[i])
        relations.append({
            "job_id": job_dict["id"],
            "topic_id": cluster_to_topic_id[cid],
        })
        # 每 5000 条 flush 一次, 避免内存膨胀
        if len(relations) >= 5000:
            db.execute(JobTopicRelation.__table__.insert(), relations)
            db.commit()
            relations.clear()

    if relations:
        db.execute(JobTopicRelation.__table__.insert(), relations)
    db.commit()
    logger.info("岗位-主题关联写入完成: %d 条", len(job_data))


# ============================================================
# 阶段 1: 主流程入口
# ============================================================

def build_topic_clusters(db: Optional[Session] = None) -> dict:
    """
    完整聚类流程:
      读取岗位 → 向量化 → UMAP降维 → HDBSCAN聚类 → 噪音处理 →
      TF-IDF命名 → 计算质心 → 入库

    参数:
      db: 可选, 传入已有的数据库 session; 不传则自行创建
    返回:
      {"n_topics": int, "n_jobs": int, "topics": [...], "elapsed": float}
    """
    import time
    from .database import SessionLocal

    t0 = time.time()
    own_db = db is None
    if own_db:
        db = SessionLocal()

    try:
        # 1. 加载数据
        logger.info("=== 步骤 1/6: 加载岗位数据 ===")
        job_data = load_job_texts(db)
        if len(job_data) < 100:
            raise ValueError(f"岗位数据不足 ({len(job_data)} 条), 无法聚类")

        texts = [j["text"] for j in job_data]

        # 2. 向量化
        logger.info("=== 步骤 2/6: BGE 向量化 ===")
        vectors = encode_texts(texts)

        # 3. 降维
        logger.info("=== 步骤 3/6: UMAP 降维 ===")
        reduced = reduce_dimensions(vectors)

        # 4. 聚类
        logger.info("=== 步骤 4/6: HDBSCAN 聚类 ===")
        labels, cluster_info = cluster_jobs(reduced)

        # 5. 噪音点处理
        logger.info("=== 步骤 5/7: 噪音点处理 ===")
        labels = assign_noise_to_clusters(labels, vectors)

        # 5.5. 合并相似小簇
        logger.info("=== 步骤 5.5/7: 合并相似小簇 (阈值=%.2f) ===", MERGE_COSINE_THRESHOLD)
        labels_before = len(set(labels))
        labels = merge_similar_clusters(labels, vectors)
        logger.info("合并后簇数: %d → %d", labels_before, len(set(labels)))

        # 6. 命名
        topics_data = name_topics(labels, job_data)

        # 7. 质心
        centroids = compute_centroids(labels, vectors)

        # 8. 入库
        logger.info("=== 步骤 6/7: 结果入库 ===")
        save_topics_to_db(db, topics_data, labels, job_data, centroids)

        elapsed = round(time.time() - t0, 1)
        logger.info("=== 聚类全部完成! 耗时 %.1f 秒, %d 个主题 ===",
                     elapsed, len(topics_data))

        return {
            "n_topics": len(topics_data),
            "n_jobs": len(job_data),
            "topics": topics_data,
            "elapsed": elapsed,
        }

    finally:
        if own_db:
            db.close()


# ============================================================
# 查询辅助函数 (供 API 使用)
# ============================================================

def get_all_topics(db: Session, page: int = 1, page_size: int = 20) -> dict:
    """分页获取所有主题"""
    from .models import JobTopic
    total = db.query(JobTopic).count()
    topics = (
        db.query(JobTopic)
        .order_by(JobTopic.job_count.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_topic_to_dict(t) for t in topics],
    }


def get_topic_detail(db: Session, topic_id: int) -> dict:
    """获取主题详情, 含薪资/城市/学历/经验分布"""
    from .models import JobTopic, JobTopicRelation, Job
    from sqlalchemy import text, func

    topic = db.query(JobTopic).filter(JobTopic.id == topic_id).first()
    if not topic:
        raise ValueError(f"主题 {topic_id} 不存在")

    result = _topic_to_dict(topic)

    # 关联查询分布统计
    job_ids_subq = (
        db.query(JobTopicRelation.job_id)
        .filter(JobTopicRelation.topic_id == topic_id)
        .subquery()
    )

    # 薪资分布
    salary_row = db.query(
        func.avg((Job.salary_max + Job.salary_min) / 2.0).label("avg_salary"),
        func.min(Job.salary_min).label("min_salary"),
        func.max(Job.salary_max).label("max_salary"),
    ).filter(Job.id.in_(job_ids_subq)).first()
    result["salary_distribution"] = {
        "min": salary_row.min_salary,
        "max": salary_row.max_salary,
        "avg": round(salary_row.avg_salary) if salary_row.avg_salary else None,
    }

    # 城市分布 (top 10)
    city_rows = db.execute(text("""
        SELECT work_city, COUNT(*) AS cnt
        FROM bigdata_recruit_job WHERE id IN (
            SELECT job_id FROM job_topic_relation WHERE topic_id = :tid
        )
        GROUP BY work_city ORDER BY cnt DESC LIMIT 10
    """), {"tid": topic_id}).fetchall()
    result["city_distribution"] = [
        {"city": r.work_city or "未知", "count": r.cnt} for r in city_rows
    ]

    # 学历分布
    edu_rows = db.execute(text("""
        SELECT your_education, COUNT(*) AS cnt
        FROM bigdata_recruit_job WHERE id IN (
            SELECT job_id FROM job_topic_relation WHERE topic_id = :tid
        )
        GROUP BY your_education ORDER BY cnt DESC
    """), {"tid": topic_id}).fetchall()
    result["education_distribution"] = [
        {"level": r.your_education or "不限", "count": r.cnt} for r in edu_rows
    ]

    # 经验分布
    exp_rows = db.execute(text("""
        SELECT working_exp, COUNT(*) AS cnt
        FROM bigdata_recruit_job WHERE id IN (
            SELECT job_id FROM job_topic_relation WHERE topic_id = :tid
        )
        GROUP BY working_exp ORDER BY cnt DESC
    """), {"tid": topic_id}).fetchall()
    result["experience_distribution"] = [
        {"level": r.working_exp or "不限", "count": r.cnt} for r in exp_rows
    ]

    return result


def get_topic_jobs(
    db: Session, topic_id: int, page: int = 1, page_size: int = 20
) -> dict:
    """分页获取某主题下的岗位列表"""
    from .models import JobTopicRelation, Job

    total = (
        db.query(JobTopicRelation)
        .filter(JobTopicRelation.topic_id == topic_id)
        .count()
    )
    job_ids = (
        db.query(JobTopicRelation.job_id)
        .filter(JobTopicRelation.topic_id == topic_id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .subquery()
    )
    jobs = db.query(Job).filter(Job.id.in_(job_ids)).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [j.to_dict() for j in jobs],
    }


def _topic_to_dict(topic) -> dict:
    """JobTopic ORM 对象 → 字典"""
    keywords = {}
    if topic.keywords_json:
        try:
            keywords = json.loads(topic.keywords_json)
        except json.JSONDecodeError:
            pass
    return {
        "id": topic.id,
        "name": topic.name,
        "keywords": keywords,
        "job_count": topic.job_count,
        "positions": topic.positions or "",
        "skills_text": topic.skills_text or "",
    }


# ============================================================
# 阶段 2: 技能画像与新颖性度量
# ============================================================

_LEXICON_CACHE: Optional[dict] = None


def _load_lexicon() -> dict:
    """加载技能时效词库 (模块级缓存)"""
    global _LEXICON_CACHE
    if _LEXICON_CACHE is not None:
        return _LEXICON_CACHE
    import os as _os
    _path = _os.path.join(_os.path.dirname(__file__), "skill_lexicon.json")
    with open(_path, "r", encoding="utf-8") as f:
        _LEXICON_CACHE = json.load(f)
    logger.info("技能词库加载完成, 四级共 %d 个技能",
                sum(len(v) for v in _LEXICON_CACHE.values()))
    return _LEXICON_CACHE


# 黑名单: 过短/易误匹配的英文技能词, 子串匹配时极易产生噪音
# (如 "C" 匹配任意含 c 的文本, "Go" 匹配 "going", "CV" 匹配任意 cv)
SKILL_BLACKLIST = {"C", "Go", "CV", "AE", "VB"}


def extract_skills(text: str) -> Dict[str, List[str]]:
    """
    从岗位描述文本中提取标准化技能关键词，按四级分类返回。
    先过滤黑名单词 (过短/易误匹配)，再做双重匹配。
    """
    import jieba
    lexicon = _load_lexicon()
    words = set(jieba.lcut(text))
    text_lower = text.lower()
    # 也做原文子串匹配，兜底 jieba 切碎的情况（如"向量数据库" → ["向量","数据库"]）
    result = {}
    for tier, skill_list in lexicon.items():
        if tier.startswith("_"):
            continue  # 跳过 "_新兴权重" 等配置键, 防止被当成技能匹配
        matched = []
        for skill in skill_list:
            if skill in SKILL_BLACKLIST or len(skill.strip()) <= 1:
                continue
            # 双重匹配: 分词结果包含 或 原文子串
            if skill in words or skill.lower() in text_lower:
                matched.append(skill)
        result[tier] = list(dict.fromkeys(matched))  # 去重保序
    return result


def _get_emerging_weight(skill: str) -> float:
    """获取新兴技能的分级权重: 强新兴=2.0, 弱新兴=0.5, 其他/未知=1.0"""
    lexicon = _load_lexicon()
    weights = lexicon.get("_新兴权重", {})
    if skill in weights.get("强新兴", []):
        return 2.0
    if skill in weights.get("弱新兴", []):
        return 0.5
    return 1.0


def compute_skill_profile(topic_id: int, db: Session, sample_size: int = 200) -> dict:
    """
    计算一个主题的技能画像（人均频次密度版）。
    新兴技能密度 = 新兴技能加权总频次 / 岗位总数量
    """
    from collections import Counter
    from .models import JobTopic, JobTopicRelation, Job
    import random

    topic = db.query(JobTopic).filter(JobTopic.id == topic_id).first()
    if not topic:
        raise ValueError(f"主题 {topic_id} 不存在")

    job_rows = (
        db.query(JobTopicRelation.job_id)
        .filter(JobTopicRelation.topic_id == topic_id)
        .all()
    )
    job_ids = [r.job_id for r in job_rows]

    if len(job_ids) > sample_size:
        sampled = random.sample(job_ids, sample_size)
    else:
        sampled = job_ids

    jobs = db.query(Job).filter(Job.id.in_(sampled)).all()
    texts = [j.job_summary or "" for j in jobs if j.job_summary]
    n_jobs = len(texts)
    if n_jobs == 0:
        return {"topic_id": topic_id, "name": topic.name, "emerging_skill_density": 0.0,
                "emerging_skills": [], "skills": {}, "skill_counts": {},
                "total_jobs": topic.job_count, "n_jobs_sampled": 0,
                "emerging_hits_raw": 0, "emerging_hits_weighted": 0.0}

    # 频率加权汇总
    all_skills: Dict[str, Counter] = {
        "传统基础": Counter(), "主流成熟": Counter(),
        "近年新兴": Counter(), "前沿探索": Counter(),
    }
    for text in texts:
        skills = extract_skills(text)
        for tier in all_skills:
            for skill in set(skills.get(tier, [])):
                all_skills[tier][skill] += 1

    # 新兴技能加权频次
    emerging_hits_weighted = 0.0
    emerging_hits_raw = 0
    for tier in ("近年新兴", "前沿探索"):
        for skill, count in all_skills[tier].items():
            w = _get_emerging_weight(skill)
            emerging_hits_weighted += count * w
            emerging_hits_raw += count

    # 人均频次密度 (推到全量岗位)
    total_jobs = topic.job_count
    density = round(emerging_hits_weighted / n_jobs, 4)

    skill_sets = {tier: sorted(c.keys()) for tier, c in all_skills.items()}

    return {
        "topic_id": topic_id,
        "name": topic.name,
        "skills": skill_sets,
        "skill_counts": {tier: dict(c.most_common(20)) for tier, c in all_skills.items()},
        "emerging_skill_density": density,
        "emerging_skills": sorted(set(skill_sets["近年新兴"]) | set(skill_sets["前沿探索"])),
        "total_jobs": total_jobs,
        "n_jobs_sampled": n_jobs,
        "emerging_hits_raw": emerging_hits_raw,
        "emerging_hits_weighted": emerging_hits_weighted,
    }


def compute_uniqueness(topic_id: int, db: Session) -> float:
    """
    计算该主题的「技能组合独特性」。
    获取该主题的向量中心，与所有其他主题中心的平均余弦距离，
    Min-Max 归一化到 0~1。距离越大 → 越独特。
    """
    from .models import JobTopic

    topic = db.query(JobTopic).filter(JobTopic.id == topic_id).first()
    if not topic or not topic.centroid_json:
        return 0.0

    target = np.array(json.loads(topic.centroid_json), dtype=np.float32)
    all_others = (
        db.query(JobTopic)
        .filter(JobTopic.id != topic_id, JobTopic.centroid_json.isnot(None))
        .all()
    )

    if not all_others:
        return 1.0

    distances = []
    for other in all_others:
        other_vec = np.array(json.loads(other.centroid_json), dtype=np.float32)
        # 余弦距离 = 1 - 余弦相似度
        cos_sim = np.dot(target, other_vec) / (
            np.linalg.norm(target) * np.linalg.norm(other_vec) + 1e-8
        )
        distances.append(1.0 - float(cos_sim))

    avg_dist = float(np.mean(distances))

    # Min-Max 归一化
    d_min = min(distances)
    d_max = max(distances)
    if d_max - d_min < 1e-8:
        norm = 0.5
    else:
        norm = round((avg_dist - d_min) / (d_max - d_min), 4)

    return norm


# ============================================================
# 阶段 3: 新兴综合评分
# ============================================================

def compute_emerging_score(topic_id: int, db: Session) -> dict:
    """
    计算单个主题的原始评分（不做归一化和CES，仅采集原始值）。
    """
    profile = compute_skill_profile(topic_id, db)
    uniqueness = compute_uniqueness(topic_id, db)

    from .models import JobTopic
    topic_obj = db.query(JobTopic).filter(JobTopic.id == topic_id).first()
    keywords = {}
    if topic_obj and topic_obj.keywords_json:
        try:
            keywords = json.loads(topic_obj.keywords_json)
        except json.JSONDecodeError:
            pass

    return {
        "topic_id": topic_id,
        "name": profile["name"],
        "keywords": keywords,
        "raw_density": profile["emerging_skill_density"],
        "raw_uniqueness": uniqueness,
        "total_jobs": profile["total_jobs"],
        "n_jobs_sampled": profile["n_jobs_sampled"],
        "emerging_hits_raw": profile["emerging_hits_raw"],
        "emerging_hits_weighted": profile["emerging_hits_weighted"],
        "emerging_skills": profile["emerging_skills"],
        "skills": profile["skills"],
        "skill_counts": profile.get("skill_counts", {}),
        "passed_gate": False,  # 暂未判定，由 ranking 函数统一判定
    }


def compute_emerging_ranking(db: Session, top_n: int = 20,
                              min_jobs: int = 100, min_emerging_hits: int = 20) -> List[dict]:
    """
    计算所有主题的新兴评分并排序:
      1. 门槛过滤: 岗位数 < min_jobs 或 新兴命中 < min_emerging_hits → 排除
      2. 对通过门槛的主题, 密度和独特性分别 0-1 归一化
      3. CES = 归一化密度 × 0.6 + 归一化独特性 × 0.4
    """
    from .models import JobTopic

    topics = db.query(JobTopic).all()
    raw_scores = []
    skipped = 0
    for t in topics:
        try:
            s = compute_emerging_score(t.id, db)
            # 两道门槛
            if s["total_jobs"] < min_jobs:
                skipped += 1
                continue
            if s["emerging_hits_weighted"] < min_emerging_hits:
                skipped += 1
                continue
            s["passed_gate"] = True
            raw_scores.append(s)
        except Exception as e:
            logger.warning("主题 %d (%s) 评分计算失败: %s", t.id, t.name, e)

    logger.info("通过门槛: %d 个主题, 跳过: %d 个 (min_jobs=%d, min_hits=%d)",
                len(raw_scores), skipped, min_jobs, min_emerging_hits)

    if not raw_scores:
        return []

    # 0-1 归一化
    densities = [s["raw_density"] for s in raw_scores]
    uniques = [s["raw_uniqueness"] for s in raw_scores]
    d_min, d_max = min(densities), max(densities)
    u_min, u_max = min(uniques), max(uniques)

    for s in raw_scores:
        norm_d = (s["raw_density"] - d_min) / (d_max - d_min + 1e-8)
        norm_u = (s["raw_uniqueness"] - u_min) / (u_max - u_min + 1e-8)
        s["norm_density"] = round(norm_d, 4)
        s["norm_uniqueness"] = round(norm_u, 4)
        s["ces_score"] = round(norm_d * 0.6 + norm_u * 0.4, 4)

    raw_scores.sort(key=lambda x: -x["ces_score"])
    for i, s in enumerate(raw_scores):
        s["rank"] = i + 1

    return raw_scores[:top_n]


# ============================================================
# 阶段 3.5: 新兴岗位发现 (基于岗位-技能表 job_skill_relation)
# ============================================================

# 学位词/非岗位词: 即使出现在清洗后的岗位名中, 也不作为岗位聚合单元
# (如 "博士(人工智能方向)" 清洗后为 "博士", 但博士是学位而非岗位)
NON_POSITION_NAMES = {"博士", "博士后", "硕士", "本科", "大专", "研究生", "学士"}

# 主题 → 领域 (job_family) 映射: 2026-08-16 无监督聚类后, 8 个主题簇按簇内岗位领域多数投票映射
# 数据整体偏向 AI, 多数簇归人工智能; 仅嵌入式簇(217)归物联网
TOPIC_FAMILY_MAP = {
    213: "人工智能",
    214: "人工智能",
    215: "人工智能",
    216: "人工智能",
    217: "物联网",
    218: "人工智能",
    219: "人工智能",
    220: "人工智能",
}

# 主题已与领域一一对应, 无需岗位粒度细拆
FINE_DOMAIN_TOPICS = set()

# 各细粒度领域的判定关键词 (命中岗位名或技能即计分)
FINE_DOMAIN_KEYWORDS = {
    "大数据": ["大数据", "hadoop", "spark", "flink", "hive", "hbase", "kafka",
               "数据仓库", "数仓", "etl", "数据中台", "数据开发", "数据工程",
               "clickhouse", "doris", "数据湖"],
    "物联网": ["物联网", "iot", "嵌入式", "传感器", "智能硬件", "单片机", "stm32",
               "arm", "智能终端", "射频", "zigbee", "蓝牙", "wifi模组", "iot网关"],
    "人工智能": ["ai", "人工智能", "机器学习", "深度学习", "算法", "pytorch",
                 "tensorflow", "nlp", "计算机视觉", "大模型", "llm", "自然语言",
                 "推荐算法", "知识图谱", "cv", "gpt", "aigc", "大语言模型",
                 "多模态", "强化学习", "扩散模型", "stable diffusion", "标注"],
    "智能系统": ["智能体", "agent", "智能系统", "机器人", "自动化", "智能控制",
                 "智能驾驶", "自动驾驶", "具身智能", "智能应用", "智能运维",
                 "无人系统", "智能决策", "系统集成"],
}
# 命中数相同时的优先级 (靠前优先)
# 智能系统置前: "AI Agent研发工程师"等既含 AI 又含 Agent 的岗位按语义归入智能系统
FINE_DOMAIN_PRIORITY = ["智能系统", "人工智能", "大数据", "物联网"]


def _fine_kw_in_text(kw: str, lower_text: str) -> bool:
    """关键词匹配: ASCII 短词用自定义词边界(避免 'ai' 误命中 'domain',
    同时避免 Python \b 把汉字当单词字符导致 'agent开发' 匹配失败), 中文直接包含"""
    import re
    if kw.isascii() and kw.isalpha():
        k = re.escape(kw.lower())
        return re.search(rf"(?<![a-z0-9]){k}(?![a-z0-9])", lower_text) is not None
    return kw.lower() in lower_text


def _assign_fine_domain(job_name: str, skills) -> str:
    """按岗位名+技能关键词判定四个细粒度领域之一;
    无法匹配任何领域时兜底返回 '技术开发' (传统技术栈/无信号)"""
    if not job_name and not skills:
        return "技术开发"
    lower = ((job_name or "") + " " + " ".join(skills or [])).lower()
    best, best_n = "技术开发", 0
    for dom in FINE_DOMAIN_PRIORITY:
        n = sum(1 for kw in FINE_DOMAIN_KEYWORDS[dom] if _fine_kw_in_text(kw, lower))
        if n > best_n:
            best, best_n = dom, n
    return best

# 岗位名新兴特征词: 岗位名包含这些词 → 该岗位本身就是围绕新兴技术设置的(强信号)
# 如 "大模型应用开发工程师" "AIGC数据分析师" "AI开发工程师" 直接判定为新兴岗位
EMERGING_NAME_MARKERS = (
    "大模型", "大语言模型", "AIGC", "智能体", "多模态", "LLM", "Agent",
    "深度学习", "机器学习", "生成式", "AI", "自动驾驶", "机器人",
    "语音识别", "RAG", "ChatGPT", "图像生成", "数字人", "脑机接口", "具身智能",
)


def _job_has_emerging_name(name: str) -> bool:
    """岗位名是否含新兴特征词 (大小写不敏感)"""
    if not name:
        return False
    lower = name.lower()
    return any(m.lower() in lower for m in EMERGING_NAME_MARKERS)


def _levenshtein(a: str, b: str) -> int:
    """编辑距离 (Levenshtein)"""
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _similar_job_names(a: str, b: str, threshold: float = 0.8) -> bool:
    """岗位名是否相似: 小写+去空格/连字符后, 编辑距离相似度 >= 阈值
    如 "AI Agent研发工程师" vs "AI Agent开发工程师" (相似度≈0.83) → 合并"""
    import re as _re
    if not a or not b:
        return False
    x = _re.sub(r"[\s\-_·]", "", a).lower()
    y = _re.sub(r"[\s\-_·]", "", b).lower()
    if x == y:
        return True
    if abs(len(x) - len(y)) > 4:
        return False
    dist = _levenshtein(x, y)
    return (1 - dist / max(len(x), len(y))) >= threshold


def _group_job_family(topic_id: int, job_name: str, job_ids, job_skills) -> str:
    """榜单分组领域: 细粒度主题按岗位多数投票, 其余主题按映射表"""
    if topic_id not in FINE_DOMAIN_TOPICS:
        return TOPIC_FAMILY_MAP.get(topic_id, "未分类")
    fam = Counter()
    for jid in job_ids:
        fam[_assign_fine_domain(job_name, list(job_skills[jid]))] += 1
    return fam.most_common(1)[0][0]


def _merge_similar_job_items(items: List[dict], threshold: float) -> List[dict]:
    """同主题内相似岗位名合并: 处理顺序即排名序, 低排名并入先出现(高排名)的组"""
    merged: List[dict] = []
    for it in items:
        target = None
        for m in merged:
            if m["topic_id"] == it["topic_id"] and _similar_job_names(
                    m["job_name"], it["job_name"], threshold):
                target = m
                break
        if target is None:
            merged.append(dict(it))
            continue
        # 低排名并入高排名
        t_total = target["total_jobs"] + it["total_jobs"]
        t_emg = target["emerging_jobs"] + it["emerging_jobs"]
        target["total_jobs"] = t_total
        target["emerging_jobs"] = t_emg
        target["emerging_ratio"] = round(t_emg / t_total, 4)
        prev_total = t_total - it["total_jobs"]
        w_avg = (target["avg_emerging_score"] * prev_total +
                 it["avg_emerging_score"] * it["total_jobs"]) / t_total
        target["avg_emerging_score"] = round(w_avg, 4)
        target["_skills"].update(it["_skills"])
        target["_sources"].extend(it["_sources"])   # 留痕: 记录被并入的细粒度岗位
    return merged


def compute_emerging_jobs(db: Session, top_n: int = 20, min_jobs: int = 2,
                          min_emerging_score: float = 1.5,
                          merge_similar: bool = True,
                          similarity_threshold: float = 0.8) -> dict:
    """
    新兴岗位发现: 基于岗位-技能表按"岗位名"粒度聚合。
      1. 单岗位新兴判定 (满足任一即新兴岗位):
         a) 岗位名含新兴特征词 (大模型/AIGC/AI/智能体等, 强信号)
         b) 新兴分 >= min_emerging_score 且 命中新兴技能数 >= 2 (二次验证:
            仅偶然提及一个新兴词不算, 需要描述里实质出现多个新兴技能)
      2. 按 (主题, 清洗后岗位名) 分组, 计算 新兴岗位占比 / 平均新兴分 / 高频新兴技能
      3. 过滤: 组内岗位数 < min_jobs 或 新兴岗位数 < 1 → 排除
      4. 按 新兴占比 降序返回榜单
    说明: total_jobs 统计的是词库有技能命中的岗位, 极少无命中岗位不计入。
    """
    from collections import defaultdict, Counter
    from .models import JobSkillRelation, JobTopic

    # 只取需要的列, 避免加载整行对象
    rows = db.query(
        JobSkillRelation.job_id, JobSkillRelation.topic_id,
        JobSkillRelation.job_name, JobSkillRelation.skill,
        JobSkillRelation.is_emerging, JobSkillRelation.weight,
    ).all()

    # 1. 单岗位新兴画像 + 分组聚合 (一次遍历)
    job_emerging = defaultdict(float)   # job_id -> 新兴分
    job_n_emerging = defaultdict(int)   # job_id -> 命中新兴技能数
    job_skills = defaultdict(set)       # job_id -> 全部技能(细粒度领域判定用)
    job_topic = {}                      # job_id -> 主题
    job_name_map = {}                   # job_id -> 岗位名
    groups = defaultdict(lambda: {
        "jobs": set(),          # 岗位id集合
        "skills": Counter(),    # 新兴技能 -> 命中岗位数
    })
    for job_id, topic_id, job_name, skill, is_emerging, weight in rows:
        if is_emerging:
            job_emerging[job_id] += weight
            job_n_emerging[job_id] += 1
        job_skills[job_id].add(skill)
        job_topic[job_id] = topic_id
        job_name_map[job_id] = job_name
        key = (topic_id, job_name)
        g = groups[key]
        g["jobs"].add(job_id)
        if is_emerging:
            g["skills"][skill] += 1

    # 1.5 岗位领域 + 全领域技能使用次数 (供 top_emerging_skill_counts 用)
    job_family_map = {}
    for jid, tid in job_topic.items():
        if tid in FINE_DOMAIN_TOPICS:
            job_family_map[jid] = _assign_fine_domain(job_name_map[jid], job_skills[jid])
        else:
            job_family_map[jid] = TOPIC_FAMILY_MAP.get(tid, "未分类")
    domain_skill_count = Counter()
    for job_id, topic_id, job_name, skill, is_emerging, weight in rows:
        domain_skill_count[(job_family_map[job_id], skill)] += 1

    # 2. 组内新兴岗位判定
    for (topic_id, job_name), g in groups.items():
        name_emerging = _job_has_emerging_name(job_name)
        g["emerging_jobs"] = set()
        for jid in g["jobs"]:
            if name_emerging:
                g["emerging_jobs"].add(jid)   # 岗位名自带新兴特征 → 直接算新兴
            elif (job_emerging[jid] >= min_emerging_score
                  and job_n_emerging[jid] >= 2):  # 分数达标 + 二次验证
                g["emerging_jobs"].add(jid)

    topic_names = {t.id: t.name for t in db.query(JobTopic).all()}

    # 3. 汇总榜单
    items = []
    for (topic_id, job_name), g in groups.items():
        if not job_name or job_name in NON_POSITION_NAMES:
            continue
        total = len(g["jobs"])
        emg = len(g["emerging_jobs"])
        if total < min_jobs or emg < 1:
            continue
        items.append({
            "job_name": job_name,
            "topic_id": topic_id,
            "topic_name": topic_names.get(topic_id, "未分类"),
            "job_family": _group_job_family(topic_id, job_name, g["jobs"], job_skills),
            "total_jobs": total,
            "emerging_jobs": emg,
            "emerging_ratio": round(emg / total, 4),
            "avg_emerging_score": round(
                sum(job_emerging[j] for j in g["jobs"]) / total, 4),
            "_skills": g["skills"],   # 内部计数, 供相似合并后重算 top 技能, 返回前移除
            "_sources": [{"name": job_name, "total_jobs": total,
                          "emerging_jobs": emg}],  # 合并留痕, 返回前转 merged_from
        })

    items.sort(key=lambda x: (-x["emerging_ratio"], -x["avg_emerging_score"], -x["total_jobs"]))

    # 4. 合并相似岗位名 (同主题, 低排名并入高排名)
    if merge_similar:
        items = _merge_similar_job_items(items, similarity_threshold)

    result_items = []
    for i, it in enumerate(items[:top_n]):
        it["rank"] = i + 1
        it["top_emerging_skills"] = [s for s, _ in it["_skills"].most_common(10)]
        # 技术栈中每个技术在当前领域(job_family)所有岗位中的使用次数
        it["top_emerging_skill_counts"] = [
            {"name": s, "count": domain_skill_count[(it["job_family"], s)]}
            for s in it["top_emerging_skills"]
        ]
        it.pop("_skills", None)
        # 留痕: 仅当该组由多个细粒度岗位合并而来时才输出 merged_from
        if len(it["_sources"]) > 1:
            it["merged_from"] = it["_sources"]
        it.pop("_sources", None)
        result_items.append(it)

    logger.info("新兴岗位榜单: 合并前 %d 个岗位名分组, 返回 top %d (min_jobs=%d, min_emerging_score=%s, merge=%s)",
                len(items), len(result_items), min_jobs, min_emerging_score, merge_similar)

    return {
        "total_groups": len(items),
        "params": {
            "min_jobs": min_jobs,
            "min_emerging_score": min_emerging_score,
            "merge_similar": merge_similar,
            "similarity_threshold": similarity_threshold,
        },
        "items": result_items,
    }
