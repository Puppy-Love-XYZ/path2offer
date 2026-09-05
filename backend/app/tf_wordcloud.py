
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="jieba")
import os
import re
import json
import time
import logging
from collections import Counter
from pathlib import Path
from typing import List, Dict, Optional

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import jieba
import jieba.posseg as pseg

logger = logging.getLogger(__name__)


_HERE = Path(__file__).parent
_STOP_PATH = (_HERE / "../dataclean/stopwords.txt").resolve()
_DICT_PATH = (_HERE / "../dataclean/user_dict.txt").resolve()
_PRECOMPUTED_DIR = _HERE / "wc_precomputed"
_PRECOMPUTED_TTL = 24 * 3600

_SKILL_POS = frozenset({"n", "ng", "nr", "nt", "nz", "eng", "j"})


_IT_SKILLS: frozenset = frozenset({

    "Python", "Java", "JavaScript", "TypeScript", "Go", "Golang",
    "Rust", "C", "C++", "C#", "Swift", "Kotlin", "PHP", "Ruby",
    "Scala", "Perl", "Matlab", "Julia", "Lua", "Shell", "Bash",
    "PowerShell", "Groovy", "Elixir", "Haskell", "Clojure", "Erlang",
    "Dart", "R", "COBOL", "Fortran", "Assembly",

    # ── 前端框架/库 ───────────────────────────────────────────────────
    "React", "Vue", "Angular", "Svelte", "jQuery", "Bootstrap",
    "Tailwind", "Webpack", "Vite", "Rollup", "Babel", "ESLint",
    "Redux", "Vuex", "Pinia", "MobX", "Zustand", "Next.js", "Nuxt.js",
    "Gatsby", "Remix", "Astro", "HTML", "CSS", "SCSS", "Less",
    "HTML5", "CSS3", "ES6", "WebGL", "Three.js", "D3.js",
    "Electron", "Tauri",

    # ── 后端框架 ──────────────────────────────────────────────────────
    "Spring", "SpringBoot", "SpringCloud", "MyBatis", "Hibernate",
    "Django", "Flask", "FastAPI", "Tornado", "Celery",
    "Express", "Koa", "NestJS", "Fastify", "Hapi",
    "Laravel", "Symfony", "CodeIgniter", "Lumen",
    "Rails", "Sinatra", "Hanami",
    "ASP.NET", "Blazor",
    "Gin", "Echo", "Beego", "Fiber",
    "Actix", "Rocket", "Axum",
    "gRPC", "Thrift", "Dubbo", "Feign",

    # ── 数据库 ────────────────────────────────────────────────────────
    "MySQL", "PostgreSQL", "Oracle", "SQLServer", "SQLite", "MariaDB",
    "MongoDB", "Redis", "Elasticsearch", "HBase", "Cassandra",
    "Neo4j", "InfluxDB", "TimescaleDB", "CockroachDB",
    "ClickHouse", "Doris", "Druid", "Presto", "Trino",
    "TiDB", "OceanBase", "PolarDB",
    "DynamoDB", "Firestore", "Supabase",
    "Memcached", "Aerospike",

    # ── 大数据 / 流处理 ───────────────────────────────────────────────
    "Hadoop", "Spark", "Flink", "Hive", "Kafka", "Storm",
    "PySpark", "Flume", "Sqoop", "Airflow", "DataX",
    "Presto", "Zookeeper", "HDFS", "Yarn", "Impala",
    "Debezium", "Pulsar", "RabbitMQ", "RocketMQ", "ActiveMQ",

    # ── AI / ML / 深度学习 ────────────────────────────────────────────
    "TensorFlow", "PyTorch", "Keras", "MXNet", "PaddlePaddle",
    "scikit-learn", "XGBoost", "LightGBM", "CatBoost",
    "Pandas", "NumPy", "SciPy", "Matplotlib", "Seaborn", "Plotly",
    "OpenCV", "PIL", "Pillow",
    "BERT", "GPT", "Transformer", "LangChain", "LlamaIndex",
    "HuggingFace", "ONNX", "TensorRT", "CUDA", "cuDNN",
    "MLflow", "Kubeflow", "Ray", "Dask",
    "Jupyter", "JupyterLab",

    # ── 云计算 / 运维 / DevOps ────────────────────────────────────────
    "Docker", "Kubernetes", "Helm", "Istio", "Envoy",
    "Terraform", "Ansible", "Puppet", "Chef", "SaltStack",
    "Jenkins", "GitLab", "GitHub", "ArgoCD", "Tekton",
    "AWS", "Azure", "GCP", "阿里云", "腾讯云", "华为云",
    "Nginx", "Apache", "Tomcat", "HAProxy",
    "Linux", "Unix", "CentOS", "Ubuntu", "Debian",
    "Prometheus", "Grafana", "ELK", "Loki", "Jaeger",
    "Vault", "Consul", "Etcd", "Nacos",

    # ── 测试 ──────────────────────────────────────────────────────────
    "Selenium", "Playwright", "Cypress", "Puppeteer",
    "JUnit", "TestNG", "Mockito", "Jest", "Mocha", "Vitest",
    "Pytest", "Unittest", "Postman", "JMeter", "LoadRunner",
    "Appium", "XCTest",

    # ── 移动端 ────────────────────────────────────────────────────────
    "Android", "iOS", "Flutter", "ReactNative", "Xamarin",
    "uniapp", "Cordova", "Ionic",

    # ── 数据分析 / BI 工具 ────────────────────────────────────────────
    "Tableau", "PowerBI", "Qlik", "Superset", "Metabase",
    "Excel", "SQL", "SPSS", "SAS",

    # ── 安全 ──────────────────────────────────────────────────────────
    "OAuth", "JWT", "SSL", "TLS", "HTTPS", "Keycloak",
    "WAF", "IDS", "IPS", "SIEM",

    # ── 设计 / 产品工具 ───────────────────────────────────────────────
    "Figma", "Sketch", "Axure", "InVision", "Zeplin",
    "Photoshop", "Illustrator", "AfterEffects", "Blender",
    "Jira", "Confluence", "Notion", "Trello", "Asana",

    # ── 版本控制 / 协作 ───────────────────────────────────────────────
    "Git", "SVN", "Mercurial",
    "Maven", "Gradle", "Ant", "NPM", "Yarn", "PNPM",
    "Poetry", "Pip", "Cargo",

    # ── 常用英文缩写（jieba 标为 j/eng，保底确保展示）────────────────
    "AI", "ML", "DL", "NLP", "CV", "BI", "ETL", "ELT",
    "API", "SDK", "CLI", "GUI", "IDE", "ORM", "MVC", "MVP", "MVVM",
    "REST", "HTTP", "TCP", "UDP", "DNS", "CDN", "VPN",
    "IoT", "AR", "VR", "XR",
    "SaaS", "PaaS", "IaaS", "ERP", "CRM", "CMS", "SCM",
    "CI", "CD", "SRE",

    # ── 中文技能词（user_dict.txt 已有，此处保底）────────────────────
    "机器学习", "深度学习", "自然语言处理", "计算机视觉",
    "强化学习", "迁移学习", "联邦学习", "大语言模型",
    "神经网络", "卷积神经网络", "循环神经网络",
    "目标检测", "图像识别", "语音识别",
    "知识图谱", "推荐系统", "特征工程",
    "数据挖掘", "数据治理", "数据仓库", "数据建模",
    "数据清洗", "数据采集", "数据分析", "数据可视化",
    "大数据", "实时计算", "流式处理", "分布式计算",
    "分布式系统", "微服务", "容器化", "服务网格", "云原生",
    "持续集成", "持续部署", "敏捷开发", "测试驱动",
    "代码审查", "版本控制", "设计模式", "领域驱动",
    "前端开发", "后端开发", "全栈开发", "移动开发",
    "高并发", "高可用", "负载均衡", "消息队列", "缓存优化",
    "系统架构", "软件架构", "性能调优",
    "数据产品", "用户画像", "量化交易", "风险控制",
    "金融科技", "区块链", "供应链管理",
    "产品经理", "需求分析", "原型设计", "交互设计", "视觉设计",
    "用户体验", "用户研究",
})

_IT_SKILLS_UPPER: frozenset = frozenset(s.upper() for s in _IT_SKILLS)


_SKILL_FLOOR_RATIO = 0.12

_SECTION_HEADERS = re.compile(
    r"(岗位职责|任职要求|任职资格|岗位要求|工作职责|工作内容|"
    r"工作描述|基本要求|能力要求|专业要求|加分项|福利待遇|"
    r"职位描述|职责描述|职位要求|主要职责|核心职责|岗位说明)"
    r"\s*[：:：]?\s*"
)


_LIST_MARKER = re.compile(
    r"(?m)^\s*[\d一二三四五六七八九十]{1,2}\s*[、。.)\]）】：:]\s*"   # 1、 一、
    r"|(?<=[；;])\s*[\d]{1,2}\s*[、.）]\s*"                         # ;1、
    r"|[①②③④⑤⑥⑦⑧⑨⑩]\s*"                                        # ①②③
)


_CET_PATTERN = re.compile(r"CET\s*[-\s]?\s*\d+", re.IGNORECASE)

_WHITESPACE = re.compile(r"\s{2,}")


def _preprocess_text(raw: str) -> str:

    text = _SECTION_HEADERS.sub(" ", raw)   
    text = _LIST_MARKER.sub(" ", text)      
    text = _CET_PATTERN.sub(" ", text)       
    text = _WHITESPACE.sub(" ", text)       
    return text.strip()


_BUILTIN_STOPWORDS = {
    
    "岗位职责", "任职要求", "任职资格", "岗位要求", "工作职责",
    "工作内容", "工作描述", "基本要求", "能力要求", "专业要求",
    "职位描述", "职责描述", "职位要求", "主要职责", "核心职责",
    
    "学历", "本科", "硕士", "博士", "大专", "专科", "研究生", "学士",
    "学生", "在校", "应届", "应届生", "毕业", "毕业生", "全日制",
    "专业背景", "专业相关", "相关专业",
    "年", "月", "日", "年以上", "年以下", "年工作经验", "年限",
    "工作年限", "工作经验", "以上", "以下", "左右", "之间",
    "负责", "参与", "协助", "配合", "支持", "推进", "推动", "开展",
    "组织", "整理", "汇报", "跟进", "协调", "执行", "完成", "处理",
    "解决", "制定", "维护", "建立", "提供", "实施", "落实", "推行",
    "协同", "对接", "统筹", "梳理", "收集", "整合", "输出", "反馈",
    "跟踪", "监控", "审核", "把控", "制作", "撰写", "编写", "拟定",
    "进行", "开发", "完善",
    "优先", "良好", "较强", "一定", "具备", "具有", "熟悉", "了解",
    "掌握", "相关", "积极", "主动", "认真", "细心", "严谨", "高效",
    "灵活", "扎实", "丰富", "独立", "全面", "系统", "深入", "专业",
    "工作", "岗位", "职位", "职责", "要求", "条件", "任职", "任职要求",
    "能力", "经验", "技能", "知识", "意识", "思维", "精神", "态度",
    "责任心", "执行力", "沟通", "协作", "团队", "部门", "公司",
    "业务", "项目", "目标", "计划", "流程", "方案", "基础", "水平",
    "招聘", "入职", "简历", "面试", "笔试", "试用期", "转正", "培训",
    "晋升", "发展", "空间", "机会", "薪资", "待遇", "福利", "工资",
    "绩效", "奖金", "提成", "社保", "保险", "五险一金", "年假",
    "节假日", "假期", "全职", "兼职", "实习", "上班", "工时",
    "性别", "年龄", "户籍", "国籍", "男女", "男", "女",
    "互联网", "行业", "领域", "市场", "用户", "客户", "服务",
    "方向", "产品", "平台", "模块", "功能", "系统",
    "总监", "经理", "主管", "专员", "助理", "助手", "顾问",
    "负责人", "人员", "工程师",
    "以上学历", "本科专业", "相关专业", "熟练掌握", "工作经验",
    "相关经验", "具备一定", "良好的", "较强的",
    "人数", "各类", "从事", "应聘", "主要", "形式", "支撑",
    "描述", "资料", "文件", "改进", "指导", "建设", "报告",
    "熟练", "学习", "运行", "建立", "整体", "现场", "特别",
    # 通用虚词
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
    "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
    "你", "会", "着", "没有", "看", "好", "自己", "这", "那", "他",
    "她", "它", "我们", "你们", "他们", "这个", "那个", "这些",
    "那些", "一些", "什么", "怎么", "为什么", "如何", "可以",
    "应该", "需要", "能够", "通过", "实现", "使用", "包括",
    "以及", "或者", "并且", "同时", "因此", "所以", "但是",
    "然而", "虽然", "如果", "当然", "其他", "具体", "情况",
    "问题", "内容", "时间", "方式", "过程", "结果", "根据",
    "基于", "对于", "关于", "确保", "保证", "提升", "优化",
    "改善", "及其", "及以上", "等等", "之内", "之外",
    "一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
    "第一", "第二", "第三", "①", "②", "③", "④", "⑤",
}

_stopwords: set = set()
_resources_loaded = False


def _load_resources() -> None:
   
    global _stopwords, _resources_loaded
    if _resources_loaded:
        return

    _stopwords = set(_BUILTIN_STOPWORDS)

    try:
        with open(_STOP_PATH, encoding="utf-8") as f:
            for line in f:
                w = line.strip()
                if w:
                    _stopwords.add(w)
        logger.info("停用词加载完成，共 %d 条", len(_stopwords))
    except FileNotFoundError:
        logger.warning("stopwords.txt 未找到，仅使用内置停用词")

    
    try:
        jieba.load_userdict(str(_DICT_PATH))
        logger.info("jieba 用户词典加载完成")
    except FileNotFoundError:
        logger.warning("user_dict.txt 未找到，使用默认分词")

   
    for skill in _IT_SKILLS:
        if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.#+\-]*", skill) and len(skill) >= 2:
            jieba.add_word(skill, freq=500, tag="eng")

    logger.info("IT技能词库已注入 jieba，共 %d 词", len(_IT_SKILLS))
    _resources_loaded = True


def _is_it_skill(word: str) -> bool:
    
    return word.upper() in _IT_SKILLS_UPPER


def _tokenize(raw: str) -> List[str]:
   
    preprocessed = _preprocess_text(raw)
    
    cleaned = re.sub(r"[^\w\u4e00-\u9fff+#.]+", " ", preprocessed).strip()
    if not cleaned:
        return []

    result = []
    for word, flag in pseg.lcut(cleaned):
        w = word.strip()
        if len(w) < 2:
            continue
        if w in _stopwords:
            continue
        if re.fullmatch(r"[\d\s]+", w):
            continue
       
        if flag in _SKILL_POS or _is_it_skill(w):
            result.append(w)

    return result




def _precomputed_path(category: str) -> Path:
    _PRECOMPUTED_DIR.mkdir(exist_ok=True)
    safe = re.sub(r"[^\w\u4e00-\u9fff]", "_", category)
    return _PRECOMPUTED_DIR / f"cat_{safe}_v2.json"   


def load_precomputed(category: str) -> Optional[List[Dict]]:
    path = _precomputed_path(category)
    if not path.exists():
        return None
    if time.time() - path.stat().st_mtime > _PRECOMPUTED_TTL:
        logger.info("预计算缓存已过期: %s", category)
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        logger.info("命中磁盘预计算缓存: %s (%d词)", category, len(data))
        return data
    except Exception as e:
        logger.warning("读取预计算缓存失败: %s - %s", category, e)
        return None


def save_precomputed(category: str, data: List[Dict]) -> None:
    path = _precomputed_path(category)
    try:
        _PRECOMPUTED_DIR.mkdir(exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        logger.info("预计算缓存已保存: %s (%d词)", category, len(data))
    except Exception as e:
        logger.warning("保存预计算缓存失败: %s - %s", category, e)




def build_lda_wordcloud(
    texts: List[str],
    num_words: int = 60,
    max_docs: int = 3000,
) -> List[Dict]:

    _load_resources()

    if not texts:
        return []


    if len(texts) > max_docs:
        import random
        random.seed(42)
        texts = random.sample(texts, max_docs)

    
    tokenized_docs: List[str] = []
    raw_token_lists: List[List[str]] = []   

    for raw in texts:
        if not raw:
            continue
        words = _tokenize(raw)
        if words:
            tokenized_docs.append(" ".join(words))
            raw_token_lists.append(words)

    logger.info("词性过滤完成：%d/%d 篇有效文档", len(tokenized_docs), len(texts))

    if len(tokenized_docs) < 5:
        logger.warning("文档数不足，退回词频统计")
        counter = Counter(w for wl in raw_token_lists for w in wl)
        if not counter:
            return []
        max_cnt = max(counter.values())
        return [
            {"name": w, "value": round(c / max_cnt * 1000)}
            for w, c in counter.most_common(num_words)
        ]

    
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np

    vectorizer = TfidfVectorizer(
        analyzer="word",
        token_pattern=r"(?u)\S+",
        max_features=8000,
        min_df=3,          
        max_df=0.65,
    )

    try:
        X = vectorizer.fit_transform(tokenized_docs)
    except ValueError as e:
        logger.warning("TF-IDF 向量化失败: %s", e)
        return []

    scores = np.asarray(X.mean(axis=0)).flatten()
    vocab = vectorizer.get_feature_names_out()

    word_scores: Dict[str, float] = {}
    for w, s in zip(vocab, scores):
        if s > 0 and len(w) >= 2 and w not in _stopwords:
            word_scores[w] = float(s)

    
    if word_scores:
        max_tfidf = max(word_scores.values())
        floor_score = max_tfidf * _SKILL_FLOOR_RATIO

        
        for w in list(word_scores):
            if _is_it_skill(w):
                word_scores[w] = max(word_scores[w], floor_score)

       
        skill_counter: Counter = Counter()
        for wl in raw_token_lists:
            seen = set()
            for w in wl:
                if _is_it_skill(w) and w not in word_scores and w not in seen:
                    skill_counter[w] += 1
                    seen.add(w)

        for w, cnt in skill_counter.items():
            if cnt >= 2:   
                word_scores[w] = floor_score * (cnt / max(len(tokenized_docs), 1) * 20 + 1)
                word_scores[w] = min(word_scores[w], floor_score * 1.5)  

        logger.info(
            "IT技能保底处理完成：已有词提升 %d 个，补充低频技能词 %d 个",
            sum(1 for w in word_scores if _is_it_skill(w)),
            len(skill_counter),
        )

    if not word_scores:
        logger.warning("TF-IDF 无有效词，退回词频统计")
        counter = Counter(w for wl in raw_token_lists for w in wl)
        if not counter:
            return []
        max_cnt = max(counter.values())
        return [
            {"name": w, "value": round(c / max_cnt * 1000)}
            for w, c in counter.most_common(num_words)
        ]

    
    sorted_words = sorted(word_scores.items(), key=lambda x: -x[1])
    sorted_words = sorted_words[:num_words]

    
    max_s = sorted_words[0][1]
    min_s = sorted_words[-1][1]
    span = max_s - min_s if max_s > min_s else max_s or 1.0

    result = [
        {
            "name": w,
            "value": round(10 + (s - min_s) / span * 990),
        }
        for w, s in sorted_words
    ]

    logger.info(
        "词云生成完成，共 %d 个词（最高: %s %d | 最低: %s %d）",
        len(result),
        result[0]["name"], result[0]["value"],
        result[-1]["name"], result[-1]["value"],
    )
    return result
