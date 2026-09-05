"""
手动添加岗位到数据库的脚本。
使用方法：
  cd backend
  source venv/Scripts/activate
  python scripts/add_product_jobs.py

注意：
  - 添加完成后需重启后端，向量匹配索引会在 24h 后自动重建，
    或删除 app/chroma_db/ 目录后重启立即重建（重建约需 15min）。
"""

import sys
import re
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import jieba
from pathlib import Path
from app.database import SessionLocal
from app.models import Job

# ─── 停用词加载 ──────────────────────────────────────────────────────────────
_STOPWORDS_PATH = Path(__file__).parent.parent / "dataclean" / "stopwords.txt"
_USER_DICT_PATH = Path(__file__).parent.parent / "dataclean" / "user_dict.txt"

if _USER_DICT_PATH.exists():
    jieba.load_userdict(str(_USER_DICT_PATH))

def _load_stopwords():
    if not _STOPWORDS_PATH.exists():
        return set()
    return set(l.strip() for l in _STOPWORDS_PATH.read_text(encoding="utf-8").splitlines() if l.strip())

STOPWORDS = _load_stopwords()


# ─── 工具函数（与 clean_jobs.py 保持一致）────────────────────────────────────

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'[^\u4e00-\u9fa5A-Za-z0-9，。；：、（）()\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def parse_salary(salary_str: str):
    if not salary_str or "面议" in salary_str:
        return None, None
    nums = re.findall(r"(\d+\.?\d*)", salary_str)
    if not nums:
        return None, None
    try:
        raw = [float(n) for n in nums]
        low, high = raw[0], raw[1] if len(raw) > 1 else raw[0]
        if "天" in salary_str:
            low, high = low * 21.75, high * 21.75
        elif "万" in salary_str or (low < 100 and high < 100):
            low, high = low * 10000, high * 10000
        if low > 50000:
            low, high = low / 12, high / 12
        return int(low), int(high)
    except Exception:
        return None, None

def clean_industry(industry: str):
    if not industry:
        return None, []
    for sep in ['/', '｜', '、', ',', '，', ';', '；']:
        industry = industry.replace(sep, '|')
    parts = list(dict.fromkeys(p.strip() for p in industry.split('|') if p.strip()))
    return '|'.join(parts), parts

def cut_words(text: str) -> str:
    return ' '.join(jieba.cut(text))

def remove_stopwords(text: str) -> str:
    return ' '.join(w for w in text.split() if w not in STOPWORDS)


# ════════════════════════════════════════════════════════════════════════════
# ★ 在这里填写你要添加的岗位数据 ★
#
# 字段说明：
#   job_name        岗位名称（必填）
#   company_name    公司名称（必填）
#   job_salary      薪资字符串，如 "15000-25000元" "15-25K" "面议"
#   industry_name   行业，多个用 | 分隔，如 "互联网|软件"
#   work_city       工作城市，如 "北京"
#   city_district   区县，如 "海淀区"（可留空 ""）
#   street_name     街道（可留空 ""）
#   work_major      专业要求（可留空 ""）
#   work_type       "全职" / "实习" / "兼职"
#   your_education  "本科" / "硕士" / "专科及以上" / "不限"
#   working_exp     "1-3年" / "3-5年" / "无经验" / "不限"
#   company_size    "100-499人" / "500-999人" / "1000-9999人" / "10000人以上"
#   job_summary     岗位描述（必填，越详细匹配越准）
#   company_benefits 福利待遇（可留空 ""）
# ════════════════════════════════════════════════════════════════════════════

RAW_JOBS = [

    # ══════════════════════════════════════════════════════════════════════
    # 【Group A】高匹配：技术转产品、应届/无经验、对 CS 背景非常友好
    # ══════════════════════════════════════════════════════════════════════

    {
        "job_name": "技术产品经理（校招/应届生）",
        "company_name": "字节跳动",
        "job_salary": "18000-28000元/月",
        "industry_name": "互联网|软件服务",
        "work_city": "北京",
        "city_district": "海淀区",
        "street_name": "知春路",
        "work_major": "计算机/软件工程/信息系统",
        "work_type": "全职",
        "your_education": "本科",
        "working_exp": "应届生",
        "company_size": "10000人以上",
        "job_summary": (
            "【岗位职责】\n"
            "1. 负责平台核心功能的产品规划与迭代设计，撰写清晰的PRD需求文档，推动研发测试按时上线；\n"
            "2. 深入理解用户需求，通过用户访谈、问卷调研、数据分析等方式挖掘产品机会点；\n"
            "3. 制定产品版本路线图，协调设计、研发、测试、运营等跨部门资源，保障项目按期交付；\n"
            "4. 关注核心业务指标（DAU、留存率、转化率），通过数据分析驱动产品优化；\n"
            "5. 持续追踪行业动态，进行竞品分析，输出竞品调研报告，保持产品竞争力。\n\n"
            "【任职要求】\n"
            "1. 计算机、软件工程、信息系统等相关专业本科及以上学历，应届生欢迎申请；\n"
            "2. 具备较强的逻辑思维能力和产品设计思维，有清晰的用户视角；\n"
            "3. 有一定的开发经验或技术背景者优先，能看懂代码、理解系统架构设计；\n"
            "4. 熟悉Axure、墨刀、Figma等原型设计工具，能独立绘制产品原型；\n"
            "5. 了解SQL及数据分析工具，有数据驱动产品决策的意识；\n"
            "6. 有产品/研发/运营相关实习经历优先；\n"
            "7. 英语四六级以上，具备基本英文文档阅读能力。\n\n"
            "【加分项】\n"
            "- 参与过完整的互联网产品/软件项目开发，有GitHub项目经验；\n"
            "- 熟悉Python/JavaScript等编程语言，了解前后端开发流程；\n"
            "- 有个人独立设计/开发App、小程序、网站等产品经历；\n"
            "- 了解机器学习、大数据、AI相关技术，对AI产品有浓厚兴趣。"
        ),
        "company_benefits": "六险一金；年终奖3-6个月；弹性工作时间；免费三餐；带薪年假15天；股票期权；健身房",
    },

    {
        "job_name": "AI产品经理（初级）",
        "company_name": "百度智能云",
        "job_salary": "16000-26000元/月",
        "industry_name": "互联网|人工智能|软件服务",
        "work_city": "北京",
        "city_district": "海淀区",
        "street_name": "西北旺东路",
        "work_major": "计算机/软件工程/人工智能",
        "work_type": "全职",
        "your_education": "本科",
        "working_exp": "经验不限",
        "company_size": "10000人以上",
        "job_summary": (
            "【岗位概述】\n"
            "加入百度智能云AI产品团队，负责AI大模型相关产品的规划与落地，将前沿AI技术转化为真实商业价值。\n\n"
            "【岗位职责】\n"
            "1. 负责AI相关产品（NLP、图像识别、语音交互、LLM应用）的需求分析、产品设计和版本规划；\n"
            "2. 深度理解AI技术能力边界，与算法团队紧密协作，将技术能力转化为可落地的产品功能；\n"
            "3. 面向B端/C端用户进行需求调研，撰写完整PRD文档，推动产品功能上线；\n"
            "4. 通过数据分析工具（SQL、Python）分析用户行为，持续优化产品体验和核心指标；\n"
            "5. 跟踪OpenAI、Anthropic、Google等国内外AI前沿动态，进行竞品分析和市场调研。\n\n"
            "【任职要求】\n"
            "1. 本科及以上学历，计算机/软件工程/人工智能/数学统计等相关专业；\n"
            "2. 对人工智能技术有浓厚兴趣和基础了解，了解机器学习、深度学习、NLP、大语言模型基本原理；\n"
            "3. 具备良好的需求分析能力，能独立撰写清晰完整的PRD/MRD文档；\n"
            "4. 熟悉Python编程语言，有一定的数据分析能力（SQL/Excel/Pandas）；\n"
            "5. 有产品经理实习经历、AI相关项目经历、或开源项目贡献者优先；\n"
            "6. 逻辑严密，表达清晰，具备出色的沟通协调和跨部门协作能力。\n\n"
            "【特别欢迎】\n"
            "- 有使用过LangChain、LlamaIndex、OpenAI API等AI开发框架经验者；\n"
            "- 有独立开发AI应用、AI Agent、RAG系统等项目经验者；\n"
            "- 熟悉向量数据库、Prompt Engineering、Fine-tuning等AI应用技术者。"
        ),
        "company_benefits": "六险一金；年终奖；弹性工作；免费班车；带薪年假；技术培训；股票期权",
    },

    {
        "job_name": "数据产品经理（应届生项目）",
        "company_name": "美团",
        "job_salary": "17000-25000元/月",
        "industry_name": "互联网|本地生活|软件服务",
        "work_city": "北京",
        "city_district": "朝阳区",
        "street_name": "望京",
        "work_major": "计算机/统计/数学/信息系统",
        "work_type": "全职",
        "your_education": "本科",
        "working_exp": "应届生",
        "company_size": "10000人以上",
        "job_summary": (
            "【岗位职责】\n"
            "1. 负责数据平台、数据工具、BI报表、数据大屏等数据产品的规划与设计；\n"
            "2. 收集业务方数据需求，进行需求分析与优先级排序，撰写数据产品PRD文档；\n"
            "3. 设计数据指标体系，搭建核心业务数据看板，支持业务决策；\n"
            "4. 结合业务场景，设计用户画像、推荐算法、A/B实验等数据应用产品；\n"
            "5. 与数据工程师、算法工程师、前端工程师协同工作，推动数据产品落地；\n"
            "6. 通过SQL查询和Python数据分析，深入理解数据，驱动产品迭代优化。\n\n"
            "【任职要求】\n"
            "1. 本科及以上学历，计算机、统计学、数学、信息系统等相关专业，应届生欢迎；\n"
            "2. 掌握SQL，能够独立进行数据查询与分析，了解数据仓库基本概念；\n"
            "3. 有Python数据分析经验（Pandas、NumPy、Matplotlib）者优先；\n"
            "4. 了解基本的数据分析方法（用户分层、漏斗分析、留存分析、A/B测试）；\n"
            "5. 熟悉Axure/墨刀/Figma原型设计工具，具备基本的产品思维；\n"
            "6. 有数据产品、BI分析、数据平台等相关实习经历者优先；\n"
            "7. 对数据分析和数据驱动决策有浓厚热情，具备较强的自驱力。\n\n"
            "【加分项】\n"
            "- 有Tableau、Power BI、Superset等BI工具使用经验；\n"
            "- 了解Spark、Hive、Flink等大数据处理技术；\n"
            "- 有ECharts、D3.js等数据可视化开发经验；\n"
            "- 有独立设计并实现数据分析系统/数据大屏等项目经历。"
        ),
        "company_benefits": "六险一金；年终奖；股票期权；弹性上下班；免费餐厅；健身中心；带薪年假",
    },

    {
        "job_name": "产品助理（技术方向）",
        "company_name": "腾讯",
        "job_salary": "14000-20000元/月",
        "industry_name": "互联网|软件服务|游戏",
        "work_city": "深圳",
        "city_district": "南山区",
        "street_name": "科技园",
        "work_major": "计算机/软件工程/信息技术",
        "work_type": "全职",
        "your_education": "本科",
        "working_exp": "经验不限",
        "company_size": "10000人以上",
        "job_summary": (
            "【岗位职责】\n"
            "1. 协助产品经理进行需求分析、功能设计，参与产品版本规划和迭代管理；\n"
            "2. 独立撰写产品需求文档（PRD）、功能设计文档，绘制产品原型；\n"
            "3. 协同设计师、研发工程师推进产品功能开发，跟踪需求实现质量；\n"
            "4. 收集用户反馈，进行用户行为数据分析，提出产品优化建议；\n"
            "5. 参与竞品分析、市场调研，输出竞品研究报告，为产品决策提供依据；\n"
            "6. 协助运营团队制定运营策略，通过产品手段提升用户活跃度和留存率。\n\n"
            "【任职要求】\n"
            "1. 本科及以上学历，计算机、软件工程、信息技术等相关专业；\n"
            "2. 对互联网产品设计有浓厚兴趣，具备基本的产品思维和用户思维；\n"
            "3. 有一定编程基础（Python/Java/JavaScript中任意一种），了解前后端开发流程；\n"
            "4. 会使用Axure/墨刀/Figma等原型设计工具，能绘制线框图和交互原型；\n"
            "5. 具备基本的数据分析能力，熟悉Excel/SQL数据处理；\n"
            "6. 有产品/研发/运营实习经验者优先，有个人App/小程序/网站开发经历者优先；\n"
            "7. 责任心强，执行力佳，沟通协调能力好，适应快节奏工作环境。"
        ),
        "company_benefits": "六险一金；年终奖；股票期权；弹性工作；免费三餐；健身房；内部晋升通道",
    },

    {
        "job_name": "B端产品经理（初级）",
        "company_name": "钉钉",
        "job_salary": "15000-22000元/月",
        "industry_name": "互联网|企业服务|SaaS软件",
        "work_city": "杭州",
        "city_district": "西湖区",
        "street_name": "文三路",
        "work_major": "计算机/软件工程/工商管理",
        "work_type": "全职",
        "your_education": "本科",
        "working_exp": "1年以下",
        "company_size": "10000人以上",
        "job_summary": (
            "【岗位职责】\n"
            "1. 负责企业协同办公产品（IM、工作流、组织管理、低代码平台）的产品规划与设计；\n"
            "2. 深入了解企业客户（SMB/中大型企业）的实际业务场景和痛点，进行需求分析；\n"
            "3. 独立撰写清晰完整的产品需求文档（PRD）、API接口文档、功能说明书；\n"
            "4. 与研发工程师、UX设计师紧密配合，推进功能开发，保障产品质量；\n"
            "5. 持续跟踪产品上线后的用户数据，通过数据分析发现问题并推动优化；\n"
            "6. 进行B端产品竞品调研（飞书、企业微信、Notion、Jira等），输出竞品分析报告。\n\n"
            "【任职要求】\n"
            "1. 本科及以上学历，计算机、软件工程、工商管理等相关专业；\n"
            "2. 1年以内工作经验，或有B端产品/企业软件相关实习经历；\n"
            "3. 理解B端产品设计逻辑（权限管理、工作流、多租户架构），对企业级软件有基础认知；\n"
            "4. 熟悉RESTful API设计规范，能与技术团队高效沟通，理解系统交互逻辑；\n"
            "5. 会使用Axure/墨刀进行高保真原型设计，能独立完成产品交互设计；\n"
            "6. 具备基本SQL查询能力，熟悉数据分析方法，能独立分析产品数据。\n\n"
            "【特别欢迎】\n"
            "- 有开发过企业管理系统、ERP、OA、CRM等B端系统项目经历者；\n"
            "- 了解低代码平台、工作流引擎、表单设计器等B端产品形态；\n"
            "- 有全栈开发经验，能理解后端逻辑设计和数据库架构设计者。"
        ),
        "company_benefits": "六险一金；年终奖；弹性工作；带薪年假；内部培训；阿里内网购物优惠",
    },

    # ══════════════════════════════════════════════════════════════════════
    # 【Group B】中等匹配：需要 1-3 年经验，有一定门槛
    # ══════════════════════════════════════════════════════════════════════

    {
        "job_name": "C端产品经理",
        "company_name": "小红书",
        "job_salary": "22000-38000元/月",
        "industry_name": "互联网|社交媒体|内容平台",
        "work_city": "上海",
        "city_district": "长宁区",
        "street_name": "古北路",
        "work_major": "",
        "work_type": "全职",
        "your_education": "本科",
        "working_exp": "1-3年",
        "company_size": "1000-9999人",
        "job_summary": (
            "【岗位职责】\n"
            "1. 负责小红书社区/电商/搜索/推荐等核心C端功能模块的产品设计与迭代；\n"
            "2. 深入研究用户行为，通过数据分析、用户调研、A/B测试等手段找到产品机会点；\n"
            "3. 制定产品功能优先级，撰写完整的产品需求文档（PRD），推动功能上线；\n"
            "4. 协同设计师进行交互设计评审，确保用户体验达到产品标准；\n"
            "5. 关注内容社区生态和电商转化数据，持续优化用户生命周期价值；\n"
            "6. 跟踪抖音、微博、B站等竞品动态，进行深度竞品分析，输出产品洞察报告。\n\n"
            "【任职要求】\n"
            "1. 本科及以上学历，1-3年产品经理工作经验；\n"
            "2. 有内容社区、社交、电商、搜索推荐等C端产品从业经验，有完整的0-1产品经历优先；\n"
            "3. 数据敏感度高，熟练使用SQL进行数据分析，有清晰的数据驱动决策思维；\n"
            "4. 精通Axure/Figma原型设计工具，具备优秀的产品交互设计能力；\n"
            "5. 对用户心理有深入洞察，具备从用户视角出发设计产品功能的能力；\n"
            "6. 出色的书面和口头表达能力，能清晰传递产品方案并有效推动执行。"
        ),
        "company_benefits": "六险一金；年终奖；股票期权；弹性工作；免费午餐；带薪年假；团队建设",
    },

    {
        "job_name": "增长产品经理",
        "company_name": "Keep",
        "job_salary": "20000-33000元/月",
        "industry_name": "互联网|健康运动|移动应用",
        "work_city": "北京",
        "city_district": "海淀区",
        "street_name": "中关村",
        "work_major": "",
        "work_type": "全职",
        "your_education": "本科",
        "working_exp": "1-3年",
        "company_size": "500-999人",
        "job_summary": (
            "【岗位职责】\n"
            "1. 负责用户增长、拉新、激活、留存、变现全链路的产品设计与增长实验；\n"
            "2. 设计并执行A/B测试方案，通过数据分析验证增长假设，优化关键转化漏斗；\n"
            "3. 搭建用户增长指标体系（新增用户、MAU、DAU、留存率、LTV、ARPU），监控核心数据；\n"
            "4. 设计用户激励体系、会员体系、社交裂变机制等增长产品功能；\n"
            "5. 结合用户画像和行为数据，推动个性化推送、智能推荐、用户分层运营产品落地；\n"
            "6. 与数据科学、算法、运营团队紧密配合，推动增长实验快速迭代。\n\n"
            "【任职要求】\n"
            "1. 本科及以上学历，1-3年产品经理或增长产品相关工作经验；\n"
            "2. 熟悉用户增长方法论（AARRR模型、北极星指标、增长飞轮），有完整增长项目经验；\n"
            "3. 强数据分析能力，精通SQL，熟悉Python数据分析（Pandas/NumPy），会设计A/B实验；\n"
            "4. 了解用户分层（RFM模型）、推送策略、召回机制等用户运营产品；\n"
            "5. 有C端App/小程序/H5产品经验，对移动端用户行为和心理有深入理解；\n"
            "6. 具备良好的数据感和商业意识，能够快速识别增长机会点并落地验证。"
        ),
        "company_benefits": "六险一金；年终奖；弹性工作；免费健身课程；带薪年假；运动福利",
    },

    {
        "job_name": "产品运营专员（产品方向）",
        "company_name": "网易",
        "job_salary": "12000-20000元/月",
        "industry_name": "互联网|游戏|教育",
        "work_city": "广州",
        "city_district": "天河区",
        "street_name": "珠江新城",
        "work_major": "",
        "work_type": "全职",
        "your_education": "本科",
        "working_exp": "1-3年",
        "company_size": "10000人以上",
        "job_summary": (
            "【岗位职责】\n"
            "1. 负责产品核心运营指标（DAU、MAU、付费率、次日留存）的分析与优化；\n"
            "2. 策划和执行用户增长活动，设计活动产品需求，联动产品经理推动落地；\n"
            "3. 分析用户行为数据，挖掘用户需求，向产品团队反馈用户问题和改进建议；\n"
            "4. 参与产品需求评审，从运营视角提供用户洞察，与产品经理协同优化产品体验；\n"
            "5. 建立和维护用户社区，通过内容运营和活动运营提升用户粘性；\n"
            "6. 跟进产品功能上线后的数据表现，撰写运营数据报告，复盘运营策略效果。\n\n"
            "【任职要求】\n"
            "1. 本科及以上学历，1-3年互联网产品运营相关经验；\n"
            "2. 具备较强的数据分析能力，熟悉SQL数据查询，能独立分析和解读业务数据；\n"
            "3. 熟悉互联网产品运营核心指标和分析框架，具备良好的用户思维；\n"
            "4. 了解基本的产品设计流程，有产品需求文档阅读和评审经验；\n"
            "5. 有较强的内容策划和文案撰写能力，具备创意思维和执行力；\n"
            "6. 有游戏/教育/社区/工具类产品运营经验者优先。"
        ),
        "company_benefits": "六险一金；年终奖；弹性工作；丰盛食堂；带薪年假；员工游戏福利",
    },

    {
        "job_name": "App产品经理（移动端）",
        "company_name": "BOSS直聘",
        "job_salary": "20000-32000元/月",
        "industry_name": "互联网|招聘|移动应用",
        "work_city": "北京",
        "city_district": "朝阳区",
        "street_name": "望京SOHO",
        "work_major": "",
        "work_type": "全职",
        "your_education": "本科",
        "working_exp": "1-3年",
        "company_size": "1000-9999人",
        "job_summary": (
            "【岗位职责】\n"
            "1. 负责招聘App（iOS/Android）核心功能（搜索、推荐、即时通讯、职位详情）的产品设计与迭代；\n"
            "2. 基于用户需求和业务目标，制定清晰的产品功能规划和版本迭代计划；\n"
            "3. 撰写高质量的PRD文档，与UI设计师、iOS/Android开发工程师、测试工程师协同推进开发；\n"
            "4. 设计用户引导、激励体系、消息推送策略等产品机制，提升用户活跃度和留存率；\n"
            "5. 监控产品核心数据（搜索转化率、简历投递率、匹配成功率），通过A/B测试优化产品体验；\n"
            "6. 研究LinkedIn、猎聘、拉勾等竞品，持续进行竞品分析，保持产品竞争优势。\n\n"
            "【任职要求】\n"
            "1. 本科及以上学历，1-3年移动端（App/小程序）产品经理工作经验；\n"
            "2. 熟悉iOS/Android移动端产品设计规范，了解App开发和发版流程；\n"
            "3. 数据敏感，会用SQL/埋点数据分析用户行为，有A/B测试设计和结果分析经验；\n"
            "4. 精通Figma/Axure原型设计，具备出色的交互设计能力；\n"
            "5. 有求职/招聘/社交类产品经验者优先，有推荐算法产品经验者加分。"
        ),
        "company_benefits": "六险一金；年终奖；股票期权；弹性工作；免费工作餐；带薪年假",
    },

    {
        "job_name": "教育科技产品经理",
        "company_name": "作业帮",
        "job_salary": "18000-28000元/月",
        "industry_name": "互联网|在线教育|EdTech",
        "work_city": "北京",
        "city_district": "海淀区",
        "street_name": "学院路",
        "work_major": "",
        "work_type": "全职",
        "your_education": "本科",
        "working_exp": "1-3年",
        "company_size": "1000-9999人",
        "job_summary": (
            "【岗位职责】\n"
            "1. 负责K12在线教育产品（AI辅导、题库、作业批改、学情分析）的产品规划与迭代设计；\n"
            "2. 深入理解学生、家长、老师等不同用户群体的学习需求，设计差异化的产品功能；\n"
            "3. 结合AI技术能力（OCR、NLP、知识图谱、自适应学习），设计智能化教育产品功能；\n"
            "4. 撰写清晰完整的PRD文档，推动算法团队、研发团队、内容团队协作落地；\n"
            "5. 通过数据分析追踪产品学习效果指标（完课率、知识点掌握度、用户留存），持续优化；\n"
            "6. 进行竞品分析（猿辅导、学而思、科大讯飞、讯飞星火），输出产品竞争策略。\n\n"
            "【任职要求】\n"
            "1. 本科及以上学历，1-3年产品经理工作经验，有在线教育/EdTech产品经验优先；\n"
            "2. 对教育有热情，了解在线教育行业生态和商业模式；\n"
            "3. 了解AI技术（NLP、机器学习、知识图谱）在教育领域的应用场景；\n"
            "4. 具备良好的数据分析能力（SQL/Python），能从数据中发现用户学习问题；\n"
            "5. 熟悉Axure/墨刀原型工具，能独立完成产品交互原型设计；\n"
            "6. 思维清晰，逻辑性强，有较强的产品文档撰写能力。"
        ),
        "company_benefits": "六险一金；年终奖；弹性工作；带薪年假；员工培训；内部知识库",
    },

    # ══════════════════════════════════════════════════════════════════════
    # 【Group C】部分场景匹配：不同行业/赛道
    # ══════════════════════════════════════════════════════════════════════

    {
        "job_name": "电商平台产品经理",
        "company_name": "阿里巴巴（淘天集团）",
        "job_salary": "20000-35000元/月",
        "industry_name": "互联网|电子商务|零售",
        "work_city": "杭州",
        "city_district": "余杭区",
        "street_name": "余杭塘路",
        "work_major": "",
        "work_type": "全职",
        "your_education": "本科",
        "working_exp": "1-3年",
        "company_size": "10000人以上",
        "job_summary": (
            "【岗位职责】\n"
            "1. 负责电商交易链路（商品详情、购物车、下单支付、售后评价）产品设计与迭代；\n"
            "2. 深入分析商家、消费者双边用户需求，设计平台产品功能，提升交易转化率；\n"
            "3. 与推荐算法团队协作，推进个性化推荐、搜索排序产品落地，提升用户GMV；\n"
            "4. 建立电商核心指标体系（GMV、转化率、客单价、复购率），通过数据分析优化产品；\n"
            "5. 进行竞品分析（京东、拼多多、抖音电商），输出竞争策略和产品优化方案；\n"
            "6. 撰写高质量PRD文档，推动研发测试按时交付。\n\n"
            "【任职要求】\n"
            "1. 本科及以上学历，1-3年电商平台产品经理工作经验；\n"
            "2. 熟悉电商交易完整链路，了解商品管理、订单管理、营销活动等电商系统；\n"
            "3. 强数据分析能力，熟悉SQL，了解A/B测试方法，具备数据驱动的产品决策能力；\n"
            "4. 了解推荐算法、搜索技术基本原理，能与算法团队有效沟通产品需求；\n"
            "5. 熟悉Axure/Figma原型工具，具备优秀的交互设计能力。"
        ),
        "company_benefits": "六险一金；年终奖；股票期权；弹性工作；阿里Park健身设施；带薪年假20天",
    },

    {
        "job_name": "用户研究员",
        "company_name": "滴滴出行",
        "job_salary": "18000-30000元/月",
        "industry_name": "互联网|出行|本地生活",
        "work_city": "北京",
        "city_district": "海淀区",
        "street_name": "中关村北大街",
        "work_major": "心理学/计算机/设计",
        "work_type": "全职",
        "your_education": "本科",
        "working_exp": "1-3年",
        "company_size": "10000人以上",
        "job_summary": (
            "【岗位职责】\n"
            "1. 规划并执行用户研究项目（用户访谈、可用性测试、问卷调研、焦点小组），挖掘用户深层需求；\n"
            "2. 设计用户画像、用户旅程地图、体验地图，为产品决策提供用户视角支撑；\n"
            "3. 结合定量数据分析和定性研究结果，输出完整的用户研究报告；\n"
            "4. 与产品经理、UX设计师、运营团队协同，将用户洞察转化为产品功能和设计优化；\n"
            "5. 建立用户研究方法论和标准化工具包，提升团队研究效率；\n"
            "6. 通过数据分析（SQL/Python）进行用户行为分析，识别体验问题和优化机会。\n\n"
            "【任职要求】\n"
            "1. 本科及以上学历，心理学、设计学、计算机、人机交互等相关专业；\n"
            "2. 1-3年用户研究工作经验，熟练掌握多种定性和定量研究方法；\n"
            "3. 具备基本的数据分析能力（SQL/Python），能进行大样本用户行为数据分析；\n"
            "4. 优秀的沟通表达能力，能将复杂的研究结论清晰传达给不同背景的受众；\n"
            "5. 对用户体验和人机交互有浓厚兴趣，具备同理心和用户视角；\n"
            "6. 有互联网产品、出行、O2O等行业的用户研究经验者优先。"
        ),
        "company_benefits": "六险一金；年终奖；弹性工作；带薪年假；出行折扣；技术培训资金",
    },

    {
        "job_name": "产品实习生（AI方向）",
        "company_name": "商汤科技",
        "job_salary": "5000-8000元/月",
        "industry_name": "人工智能|计算机视觉|软件服务",
        "work_city": "上海",
        "city_district": "徐汇区",
        "street_name": "云锦路",
        "work_major": "计算机/软件工程/人工智能",
        "work_type": "实习",
        "your_education": "本科",
        "working_exp": "在校生/应届生",
        "company_size": "1000-9999人",
        "job_summary": (
            "【岗位职责】\n"
            "1. 协助产品经理进行AI产品（计算机视觉、大模型应用、智能体）的需求分析和功能设计；\n"
            "2. 参与产品原型设计，使用Axure/Figma绘制产品线框图和交互稿；\n"
            "3. 撰写产品需求文档（PRD）初稿，参与产品评审会议；\n"
            "4. 协助进行竞品调研和市场分析，输出竞品分析报告；\n"
            "5. 配合运营团队进行用户反馈收集与整理，发现产品问题；\n"
            "6. 协助数据分析，追踪产品关键指标，支持产品迭代决策。\n\n"
            "【任职要求】\n"
            "1. 在读本科大三/大四或研究生，计算机、软件工程、人工智能等相关专业；\n"
            "2. 对人工智能技术有基础了解，熟悉常见AI应用场景（图像识别、NLP、大语言模型）；\n"
            "3. 有使用过GPT/Claude/文心一言等大语言模型的经验，有AI产品使用和思考者优先；\n"
            "4. 了解基本的产品设计流程，有产品/研发/运营实习经历者优先；\n"
            "5. 能使用Python进行基础数据处理和分析；\n"
            "6. 实习时间不少于3个月，每周到岗不少于4天；\n"
            "7. 思维活跃，对AI产品有浓厚的热情和独立思考能力。"
        ),
        "company_benefits": "实习补贴；餐费补贴；交通补贴；优秀实习生留用机会；导师带教",
    },

    # ══════════════════════════════════════════════════════════════════════
    # 【Group D】学历不足：要求硕士，本科会被打折
    # ══════════════════════════════════════════════════════════════════════

    {
        "job_name": "AI产品研究员",
        "company_name": "阿里达摩院",
        "job_salary": "28000-45000元/月",
        "industry_name": "人工智能|互联网|研究院",
        "work_city": "杭州",
        "city_district": "余杭区",
        "street_name": "余杭塘路",
        "work_major": "计算机/人工智能/数学/统计",
        "work_type": "全职",
        "your_education": "硕士",
        "working_exp": "1-3年",
        "company_size": "10000人以上",
        "job_summary": (
            "【岗位职责】\n"
            "1. 负责前沿AI技术（大语言模型、多模态、Agents）在产品中的应用研究和落地规划；\n"
            "2. 结合技术研究成果进行产品可行性分析，设计AI能力产品化路径和商业落地方案；\n"
            "3. 深入理解AI模型能力和局限性，与算法科学家协同，将研究成果转化为产品功能；\n"
            "4. 进行行业调研和学术跟踪（顶会论文、技术报告），识别AI产品创新机会；\n"
            "5. 撰写高质量的AI产品白皮书、技术方案文档，推动产品商业化。\n\n"
            "【任职要求】\n"
            "1. 硕士及以上学历（博士优先），计算机、人工智能、数学、统计等专业；\n"
            "2. 1-3年AI相关产品/研究工作经验，有顶级会议（NeurIPS/ICML/ACL/ICLR）发表论文者优先；\n"
            "3. 深入了解主流AI技术栈（Transformer、RLHF、RAG、Multi-agent），有实际AI项目经验；\n"
            "4. 熟练使用Python/PyTorch/TensorFlow，能独立进行算法原型验证；\n"
            "5. 具备从技术视角设计产品的能力，能将复杂技术能力转化为用户价值；\n"
            "6. 有OpenAI API、LangChain、向量数据库等AI应用开发经验者优先。"
        ),
        "company_benefits": "六险一金；年终奖；科研经费；顶会参会资助；股票期权；带薪年假20天",
    },

    {
        "job_name": "用户体验研究专家（UXR）",
        "company_name": "华为消费者BG",
        "job_salary": "25000-42000元/月",
        "industry_name": "消费电子|互联网|软件服务",
        "work_city": "深圳",
        "city_district": "龙岗区",
        "street_name": "坂田",
        "work_major": "心理学/设计学/人机交互/计算机",
        "work_type": "全职",
        "your_education": "硕士",
        "working_exp": "3-5年",
        "company_size": "10000人以上",
        "job_summary": (
            "【岗位职责】\n"
            "1. 主导消费者产品（手机/平板/可穿戴设备）的用户研究项目规划和执行；\n"
            "2. 综合运用定性研究（深度访谈、民族志研究、日记研究）和定量研究方法；\n"
            "3. 建立用户研究方法论体系，指导团队成员开展规范化用户研究；\n"
            "4. 通过数据分析（Python/R语言）处理大规模用户行为数据，挖掘体验问题；\n"
            "5. 向产品管理层输出战略性用户洞察报告，驱动产品战略决策；\n"
            "6. 与设计团队、产品团队深度协作，将用户研究成果融入产品设计过程。\n\n"
            "【任职要求】\n"
            "1. 硕士及以上学历，心理学、设计学、HCI、计算机等相关专业，UXR方向研究生优先；\n"
            "2. 3-5年用户体验研究相关工作经验，有消费电子/互联网行业经验优先；\n"
            "3. 系统掌握用户研究方法（访谈、问卷、可用性测试、眼动追踪、情感计算）；\n"
            "4. 熟悉统计分析方法（SPSS/R/Python），有大样本数据分析和显著性检验经验；\n"
            "5. 出色的研究报告撰写和演讲呈现能力，能向非专业受众清晰传递研究结论；\n"
            "6. 有SCI论文发表或UX研究学术背景者加分。"
        ),
        "company_benefits": "六险一金；年终奖；带薪年假；科研经费；住房补贴；班车；内部培训",
    },

    {
        "job_name": "量化策略产品经理",
        "company_name": "蚂蚁集团",
        "job_salary": "35000-60000元/月",
        "industry_name": "金融科技|互联网金融|软件服务",
        "work_city": "上海",
        "city_district": "浦东新区",
        "street_name": "陆家嘴",
        "work_major": "计算机/金融数学/统计/数量金融",
        "work_type": "全职",
        "your_education": "硕士",
        "working_exp": "3-5年",
        "company_size": "10000人以上",
        "job_summary": (
            "【岗位职责】\n"
            "1. 负责量化投资策略平台（因子库、回测平台、实时交易引擎）的产品规划与设计；\n"
            "2. 深入理解量化投资业务逻辑（多因子模型、统计套利、高频交易、风控），翻译为产品需求；\n"
            "3. 设计金融数据产品（行情数据、另类数据、因子数据服务），满足量化研究员需求；\n"
            "4. 撰写清晰的系统设计文档，与量化研究员、数据工程师、算法工程师高效协作；\n"
            "5. 进行金融科技产品竞品研究，跟踪行业前沿趋势（AI量化、大模型在金融领域的应用）；\n"
            "6. 通过数据分析评估产品效果，持续优化量化研究效率和策略收益。\n\n"
            "【任职要求】\n"
            "1. 硕士及以上学历（博士优先），金融数学、统计、计算机、数量金融等专业；\n"
            "2. 3-5年金融科技/量化投资产品经验，有量化策略研究或系统开发经验优先；\n"
            "3. 深入理解量化投资策略（Alpha因子、风险模型、组合优化、高频交易）；\n"
            "4. 熟练掌握Python（Pandas/NumPy/Statsmodels），具备金融数据分析能力；\n"
            "5. 了解大数据技术（Kafka/Flink/Spark）和分布式系统设计；\n"
            "6. CFA/FRM持证人或有相关备考经验者加分。"
        ),
        "company_benefits": "六险一金；高额年终奖；股票期权；弹性工作；免费食堂；带薪年假20天",
    },

    # ══════════════════════════════════════════════════════════════════════
    # 【Group E】经验不足：高级/总监职位，打分会因经验差距被扣分
    # ══════════════════════════════════════════════════════════════════════

    {
        "job_name": "高级产品经理（平台方向）",
        "company_name": "京东集团",
        "job_salary": "35000-55000元/月",
        "industry_name": "互联网|电子商务|物流科技",
        "work_city": "北京",
        "city_district": "朝阳区",
        "street_name": "东四环中路",
        "work_major": "",
        "work_type": "全职",
        "your_education": "本科",
        "working_exp": "3-5年",
        "company_size": "10000人以上",
        "job_summary": (
            "【岗位职责】\n"
            "1. 主导电商/物流/供应链平台级产品的顶层设计和长期规划，输出完整的产品战略文档；\n"
            "2. 独立负责复杂系统（交易中台、商品中台、履约系统）的架构设计和迭代管理；\n"
            "3. 带领初级产品经理完成需求分析、方案设计、文档撰写，指导团队成员成长；\n"
            "4. 与业务方（采购、销售、运营）深度对话，准确识别核心痛点，形成高ROI的产品方案；\n"
            "5. 主导跨BU、跨部门的复杂项目协调，确保多方资源的协同配合和目标达成；\n"
            "6. 建立产品数据指标体系，定期向高级管理层汇报产品健康度和业务进展。\n\n"
            "【任职要求】\n"
            "1. 本科及以上学历，3-5年电商/平台/供应链方向产品经理经验；\n"
            "2. 有从0到1独立完成中大型产品项目的完整经历，有平台型/中台型产品经验优先；\n"
            "3. 具备优秀的系统思维和业务理解能力，能处理高复杂度的产品架构问题；\n"
            "4. 掌握数据分析方法（SQL/Python），有基于数据驱动产品决策的丰富经验；\n"
            "5. 出色的沟通表达和向上管理能力，能有效推动跨组织的协同和资源争取；\n"
            "6. 有带团队管理经验者优先，具备产品经理的leadership和mentoring能力。"
        ),
        "company_benefits": "六险一金；高额年终奖；股票期权；弹性工作；班车接送；食堂补贴；带薪年假",
    },

    {
        "job_name": "产品总监（智能化方向）",
        "company_name": "快手",
        "job_salary": "60000-100000元/月",
        "industry_name": "互联网|短视频|社交媒体",
        "work_city": "北京",
        "city_district": "海淀区",
        "street_name": "西二旗",
        "work_major": "",
        "work_type": "全职",
        "your_education": "本科",
        "working_exp": "5年以上",
        "company_size": "10000人以上",
        "job_summary": (
            "【岗位职责】\n"
            "1. 负责快手智能化产品线（推荐系统、搜索产品、内容理解、创作工具AI化）的整体战略规划；\n"
            "2. 统领产品经理团队（5-10人），建立产品研发流程和团队文化，打造高效协作的产品团队；\n"
            "3. 主导算法、数据、工程等多个技术团队的跨团队协同，推动AI能力规模化落地；\n"
            "4. 把握行业技术趋势（AIGC、多模态、大语言模型），制定AI产品能力长期路线图；\n"
            "5. 直接向副总裁汇报，参与公司级产品战略讨论，输出具有前瞻性的产品策略；\n"
            "6. 负责团队建设和人才培养，招聘优秀产品人才，建立人才梯队。\n\n"
            "【任职要求】\n"
            "1. 本科及以上学历，5年以上互联网产品工作经验，其中3年以上产品管理/总监经验；\n"
            "2. 有主导智能化/AI产品的丰富经验，对推荐系统、搜索产品、AIGC工具有深刻理解；\n"
            "3. 出色的团队领导力，有成功组建和管理10人以上产品团队的经验；\n"
            "4. 深厚的商业洞察力和产品战略思维，能准确识别市场机会并制定产品路线图；\n"
            "5. 在短视频/内容/社交平台有丰富的产品经验，对内容生态和用户增长有深入理解；\n"
            "6. 优秀的跨团队沟通协调能力，具备强大的影响力和推动力。"
        ),
        "company_benefits": "六险一金；高额年终奖；股票期权；弹性工作；免费三餐；健身房；带薪年假20天",
    },

    {
        "job_name": "SaaS产品负责人",
        "company_name": "有赞",
        "job_salary": "40000-70000元/月",
        "industry_name": "互联网|SaaS软件|电子商务",
        "work_city": "上海",
        "city_district": "长宁区",
        "street_name": "仙霞路",
        "work_major": "",
        "work_type": "全职",
        "your_education": "本科",
        "working_exp": "5年以上",
        "company_size": "1000-9999人",
        "job_summary": (
            "【岗位职责】\n"
            "1. 全权负责有赞SaaS电商产品线（商城/零售/美业/教育）的产品规划与商业化落地；\n"
            "2. 建立和维护产品-市场契合度（PMF），深度理解客户业务场景，定义产品核心价值主张；\n"
            "3. 带领5-8人产品团队，负责产品路线图制定、需求优先级排序和团队日常管理；\n"
            "4. 主导与销售、市场、实施、客户成功团队的协作，推动产品商业化和客户成功；\n"
            "5. 跟踪SaaS行业趋势和竞品动态（Shopify、微盟、Salesforce），制定差异化产品策略；\n"
            "6. 建立完善的产品数据体系，分析SaaS核心健康指标（MRR、NRR、Churn Rate）。\n\n"
            "【任职要求】\n"
            "1. 本科及以上学历，5年以上产品经理经验，其中2年以上SaaS产品经验；\n"
            "2. 深刻理解SaaS商业模式（订阅制、私有化、增值服务），有PLG产品增长经验者加分；\n"
            "3. 有完整的产品从0到1和1到100的经历，有主导过千万级营收SaaS产品经验优先；\n"
            "4. 具备出色的商业思维和客户导向意识，能有效平衡产品通用性和客户个性化需求；\n"
            "5. 熟悉企业级软件架构（多租户、权限管理、API开放平台），具备B端产品设计深度；\n"
            "6. 有团队管理经验，具备良好的领导力和人才发展能力。"
        ),
        "company_benefits": "六险一金；年终奖；弹性工作；带薪年假；技术培训；内部晋升；期权激励",
    },

]


# ─── 插入逻辑（无需修改）──────────────────────────────────────────────────────

def process_and_insert(raw_jobs: list[dict]) -> int:
    db = SessionLocal()
    inserted = 0
    try:
        for item in raw_jobs:
            industry_str, industry_list = clean_industry(item.get("industry_name", ""))
            raw_salary = item.get("job_salary", "").strip()
            salary_min, salary_max = parse_salary(raw_salary)

            summary_clean = clean_text(item.get("job_summary", ""))
            summary_cut = cut_words(summary_clean)
            summary_cut_filtered = remove_stopwords(summary_cut)

            benefits_clean = clean_text(item.get("company_benefits", ""))
            benefits_cut = cut_words(benefits_clean)

            job = Job(
                job_name=item.get("job_name"),
                company_name=item.get("company_name"),
                job_salary=raw_salary,
                salary_min=salary_min,
                salary_max=salary_max,
                industry_name=industry_str,
                industry_list=industry_list,
                work_city=item.get("work_city"),
                city_district=item.get("city_district") or "",
                street_name=item.get("street_name") or "",
                work_major=item.get("work_major") or "",
                work_type=item.get("work_type", "全职"),
                your_education=item.get("your_education", "不限"),
                working_exp=item.get("working_exp", "不限"),
                company_size=item.get("company_size", ""),
                job_summary=summary_clean,
                job_summary_cut=summary_cut,
                job_summary_cut_filtered=summary_cut_filtered,
                company_benefits=benefits_clean,
                company_benefits_cut=benefits_cut,
            )
            db.add(job)
            inserted += 1
            print(f"  准备插入: [{item.get('job_name')}] @ {item.get('company_name')}")

        db.commit()
        print(f"\n[OK] 成功插入 {inserted} 条岗位数据。")
    except Exception as e:
        db.rollback()
        print(f"\n[FAIL] 插入失败，已回滚: {e}")
        raise
    finally:
        db.close()
    return inserted


if __name__ == "__main__":
    print(f"准备插入 {len(RAW_JOBS)} 条岗位...\n")
    process_and_insert(RAW_JOBS)
    print("\n提示：添加完成后，如需立即在「岗位匹配」中命中新岗位，")
    print("      请删除 backend/app/chroma_db/ 目录后重启后端（重建向量索引约需 15 分钟）。")
    print("      或等待 24 小时后索引自动重建。")
