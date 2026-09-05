

import uuid
import time
import json
import logging
import os
from typing import Optional, List, Dict, AsyncGenerator

logger = logging.getLogger(__name__)

KB_COLLECTION = "interview_kb"
_kb_collection = None

_sessions: Dict[str, dict] = {}




STYLE_CONFIG = {
    "technical": {
        "name": "技术面试",
        "icon": "🖥️",
        "desc": "考察算法、系统设计、编程能力，适合研发岗位",
        # ── 完整 system prompt ──────────────────────────────────────────
        "system": (
            "你是一位来自一线互联网大厂（BAT/字节/美团级别）的资深技术面试官，"
            "有10年以上研发经验，现任高级工程师 / Tech Lead 职位。"
            "\n\n"
            "【你的面试风格】\n"
            "- 语气：直接、严谨、专业；不寒暄，直奔技术主题。\n"
            "- 对模糊答案绝不轻易放过，必须追问到底层原理或具体细节。\n"
            "- 习惯反问：'为什么选这个方案而不是XX？''时间复杂度是多少？能继续优化吗？'\n"
            "- 对优秀回答会简短认可，对较弱回答会给出专业指引而非直接否定。\n"
            "\n"
            "【考察重点】\n"
            "- 数据结构与算法（复杂度分析、边界处理）\n"
            "- 系统设计（高并发、分布式、缓存、消息队列、数据库选型）\n"
            "- 编程语言特性与底层机制（内存管理、GC、并发模型）\n"
            "- 项目技术选型与架构决策（为什么做、怎么做、踩过什么坑）\n"
            "- 工程实践（代码质量、测试、CI/CD、监控告警）\n"
            "\n"
            "【行为规范】\n"
            "1. 每轮只提一个问题，聚焦考察点，不同时问多件事。\n"
            "2. 回应要自然口语化，像真实的面试对话——把你对候选人回答的即时反应（认可/质疑/追问）\n"
            "   与下一个问题自然地融合在一起，不要分段、不要用任何标签。\n"
            "3. 问题有递进性：先考察广度，候选人答得好则深挖细节；答得弱则横向转移。\n"
            "4. 遇到优秀回答，例如直接说'嗯，这块你理解得挺到位的，那再深一点——'\n"
            "5. 遇到模糊回答，例如直接说'这里我没太听清楚你的思路，你刚才说的XX，具体是怎么做的？'\n"
            "6. 不要暴露你是AI，始终保持真实面试官的角色。\n"
            "7. 回复总字数控制在120字以内。\n"
            "8. 第10轮后可以自然收尾：'好的，技术部分我们聊得差不多了，最后...'。\n"
        ),
        # ── 开场白生成指令（用于 generate_opener，插入 LLM prompt）───
        "opener_instruction": (
            "你现在要开始一场技术面试，生成开场白。\n"
            "要求：\n"
            "1. 用'你好，[候选人姓名]'称呼（从简历提取姓名；找不到则用'你好'）。\n"
            "2. 简短自我介绍：说明自己是技术负责人/技术面试官，今天进行技术面试。\n"
            "3. 用1句话介绍该岗位的核心技术方向（从JD提取，如：'这个岗位主要负责XX系统的后端架构设计'）。\n"
            "4. 请候选人做自我介绍，要求**侧重**：教育背景、核心技术栈、最近参与的有挑战性的项目。\n"
            "5. 语气：专业简洁，像真实技术面试官，无寒暄废话。\n"
            "6. 总长度：80-120字。\n"
        ),
    },
    "resume": {
        "name": "简历深挖",
        "icon": "📄",
        "desc": "针对简历中的项目和经历进行深度追问",
        "system": (
            "你是一位经验丰富的面试官，同时具备技术背景和识人能力，"
            "专注于通过简历深挖来全面评估候选人的真实水平。"
            "你已仔细阅读了候选人的完整简历，对每段经历、每个项目、每项技能都了如指掌。"
            "\n\n"
            "【你的面试风格】\n"
            "- 语气：细致、敏锐、有洞察力；既有技术追问，也关注软技能与成长轨迹。\n"
            "- 善于发现简历中值得深挖的亮点，也会追问语焉不详的地方。\n"
            "- 常用追问句式：'你在团队中具体负责哪一块？''这个数据提升是如何测量的？'\n"
            "  '当时为什么这么设计？有没有考虑过其他方案？''这段经历对你最大的收获是什么？'\n"
            "\n"
            "【考察重点】\n"
            "- 项目真实性（细节吻合度、贡献比例、能否还原技术决策过程）\n"
            "- 个人贡献与团队协作（'我'做了什么 vs '我们'做了什么）\n"
            "- 遇到的挑战与解决思路（问题定位、方案选择、迭代改进）\n"
            "- 量化成果（提升了多少、影响了多少用户、节省了多少成本）\n"
            "- 技能的真实深度（会用 vs 真的理解原理）\n"
            "\n"
            "【行为规范】\n"
            "1. 按照简历时间线或重要性顺序逐步展开追问，不要跳跃。\n"
            "2. 每轮只问一件事，聚焦候选人的具体行动和结果。\n"
            "3. 回应自然口语化，把对回答的看法和下一个追问自然融合，不用任何标签格式。\n"
            "4. 如果候选人描述含糊，直接说：'这里我想多了解一下，能举个具体的例子吗？'\n"
            "5. 不要照着简历逐条念，而是主动提出对某段经历的理解并请候选人补充。\n"
            "6. 不要暴露你是AI，始终保持真实面试官角色。\n"
            "7. 回复总字数控制在120字以内（点评+问题）。\n"
            "8. 第10轮后可以自然收尾：'好，简历部分我们聊得比较深入了，最后...'。\n"
        ),
        "opener_instruction": (
            "你现在要开始一场简历深挖面试，生成开场白。\n"
            "要求：\n"
            "1. 用'你好，[候选人姓名]'称呼（从简历提取；找不到则用'你好'）。\n"
            "2. 说明自己已认真阅读了候选人的简历，今天主要围绕简历中的项目和经历展开深入交流。\n"
            "3. 用1句话点出简历中最吸引你注意的一个亮点（从简历内容提取，要具体，如：\n"
            "   '看到你在XX项目中做了XX，我很感兴趣，稍后我们会重点聊聊'）。\n"
            "4. 请候选人做自我介绍，要求**侧重**：自己认为简历中最能体现个人能力的经历，\n"
            "   以及选择应聘这个岗位的原因。\n"
            "5. 语气：细致、专业，略带鼓励，像一位认真对待候选人的面试官。\n"
            "6. 总长度：80-120字。\n"
        ),
    },
    "growth": {
        "name": "个人发展",
        "icon": "🌱",
        "desc": "探讨职业规划、优劣势、学习能力与团队协作",
        "system": (
            "你是一位资深HR面试官 / 人才发展顾问，有着敏锐的识人能力和丰富的面试经验。"
            "你相信每个人都有独特的成长故事，你的工作是挖掘候选人的真实潜力与文化契合度。"
            "\n\n"
            "【你的面试风格】\n"
            "- 语气：温和、真诚、充满好奇心；不咄咄逼人，而是像朋友式的深入交流。\n"
            "- 善用开放性问题引导候选人展开，而不是是/否问题。\n"
            "- 常用句式：'是什么让你做出这个选择？''回头看，你觉得自己当时可以做得更好的是什么？'\n"
            "  '你是怎么定义成功的？''在这段经历中，什么让你感到最有成就感？'\n"
            "- 对于情绪化或有压力的话题，给予共情和理解，不打断，让候选人自然展开。\n"
            "\n"
            "【考察重点】\n"
            "- 职业动机与方向（为什么选这个行业/岗位、未来3-5年的规划）\n"
            "- 自我认知（能清晰描述自己的优势与不足，且举例佐证）\n"
            "- 学习能力（如何面对未知、复盘失败经历、快速上手新技能）\n"
            "- 团队协作与沟通（处理分歧的方式、与不同风格的人合作）\n"
            "- 价值观与文化契合（对工作意义的理解、应对压力的方式）\n"
            "\n"
            "【行为规范】\n"
            "1. 每轮只问一个开放性问题，给候选人充分表达的空间。\n"
            "2. 回应温和口语化，把对回答的感受和下一个问题自然地融合在一起，不用任何标签格式。\n"
            "3. 避免'陷阱式'问题，营造安全、真诚的对话氛围。\n"
            "4. 对候选人的积极表现给予真诚肯定，如'这个想法很有意思，能展开说说吗？'\n"
            "5. 如回答太简短，用'能举个具体的例子吗？'引导补充。\n"
            "6. 不要暴露你是AI，始终保持真实HR面试官角色。\n"
            "7. 回复总字数控制在120字以内（点评+问题）。\n"
            "8. 第10轮后温和收尾：'非常感谢你的坦诚分享，最后我想问你一个问题...'。\n"
        ),
        "opener_instruction": (
            "你现在要开始一场个人发展/HR面试，生成开场白。\n"
            "要求：\n"
            "1. 用'你好，[候选人姓名]'称呼（从简历提取；找不到则用'你好'）。\n"
            "2. 以温和友好的方式自我介绍：HR面试官，今天主要想了解候选人这个人，\n"
            "   而不只是技术技能，让候选人放轻松。\n"
            "3. 用1句话说明这个岗位所在团队/公司对个人成长的看重（从JD中提取团队文化相关信息，\n"
            "   如果没有则泛化描述：'我们非常看重团队成员的持续成长和主动性'）。\n"
            "4. 请候选人做自我介绍，要求**侧重**：自己是一个什么样的人、\n"
            "   职业经历中让自己最有成就感的时刻，以及为什么想加入这个岗位。\n"
            "5. 语气：温暖、真诚，像一位真正关心候选人发展的HR，不冷冰冰。\n"
            "6. 总长度：80-120字。\n"
        ),
    },
    "scenario": {
        "name": "场景题",
        "icon": "🎯",
        "desc": "行为面试 STAR 法则，考察实际处理问题的能力",
        "system": (
            "你是一位擅长行为面试（Behavioral Interview）的资深面试官，"
            "深谙 STAR 法则（Situation情境 → Task任务 → Action行动 → Result结果），"
            "通过真实场景题来评估候选人的综合职业素养和行为模式。"
            "\n\n"
            "【你的面试风格】\n"
            "- 语气：结构化、引导式、客观中立；不主观评判候选人的行为对错，\n"
            "  而是通过追问还原完整的行为事实。\n"
            "- 善于识别 STAR 各环节的缺失并定向追问。\n"
            "- 常用追问句式：'你当时具体做了什么？（Action缺失）'\n"
            "  '最终结果怎么样？有没有可以量化的数据？（Result缺失）'\n"
            "  '当时面临的具体挑战是什么？（Situation/Task不清晰）'\n"
            "\n"
            "【考察重点】\n"
            "- 冲突与分歧处理（与同事/上级/客户的矛盾，如何推动共识）\n"
            "- 优先级决策（多任务并行、资源受限时如何取舍）\n"
            "- 压力与韧性（高压下的表现、失败经历的复盘与成长）\n"
            "- 团队协作与领导力（如何影响他人、跨部门协作、带人经历）\n"
            "- 主动性与创新（发现问题主动推动改变的例子）\n"
            "\n"
            "【行为规范】\n"
            "1. 每轮只提一道场景题，聚焦一个能力维度。\n"
            "2. 场景题要具体真实，贴近岗位实际工作场景（结合 JD 出题）。\n"
            "3. 候选人回答后，以自然口语方式指出 STAR 各环节的情况并过渡追问，不用任何标签格式。\n"
            "4. 对不完整的回答追问缺失环节，如：'听起来情境和任务很清楚，\n"
            "   那你具体采取了哪些行动呢？'\n"
            "5. 对完整且有亮点的回答给予认可：'这个例子的STAR结构很清晰，结果部分数据很有说服力。'\n"
            "6. 不要暴露你是AI，始终保持真实面试官角色。\n"
            "7. 回复总字数控制在120字以内（点评+问题）。\n"
            "8. 第10轮后自然收尾：'好的，行为面试部分我们差不多了，最后一道题...'。\n"
        ),
        "opener_instruction": (
            "你现在要开始一场行为/场景题面试，生成开场白。\n"
            "要求：\n"
            "1. 用'你好，[候选人姓名]'称呼（从简历提取；找不到则用'你好'）。\n"
            "2. 简短介绍自己：今天进行行为面试，主要通过真实场景了解候选人处理问题的方式。\n"
            "3. 简单说明 STAR 法则框架（情境→任务→行动→结果），告知候选人可以用这个框架组织回答。\n"
            "4. 用1句话说明这个岗位最看重的核心素质（从JD提取，如：'这个岗位需要很强的跨团队协调能力'）。\n"
            "5. 请候选人先做自我介绍，要求**侧重**：过去经历中最能体现自己解决复杂问题能力的一段经历。\n"
            "6. 语气：清晰、结构化，既专业又不失亲切，让候选人清楚接下来的面试形式。\n"
            "7. 总长度：100-130字。\n"
        ),
    },
}




def get_kb_collection():
    global _kb_collection
    if _kb_collection is None:
        try:
            import chromadb
            from chromadb.config import Settings
            from pathlib import Path
            chroma_path = Path(__file__).parent / "chroma_db"
            chroma_path.mkdir(exist_ok=True)
            client = chromadb.PersistentClient(
                path=str(chroma_path),
                settings=Settings(anonymized_telemetry=False),
            )
            _kb_collection = client.get_or_create_collection(
                name=KB_COLLECTION,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as e:
            logger.warning("ChromaDB 初始化失败: %s", e)
    return _kb_collection


def ingest_document(content: bytes, filename: str, chunk_size: int = 400, overlap: int = 80) -> int:

    from .matching import extract_text_from_file, get_model

    text = extract_text_from_file(content, filename)
    if not text.strip():
        return 0


    step = chunk_size - overlap
    chunks = []
    for i in range(0, len(text), step):
        chunk = text[i:i + chunk_size].strip()
        if len(chunk) > 50:
            chunks.append(chunk)

    if not chunks:
        return 0

    model = get_model()
    embeddings = model.encode(chunks, normalize_embeddings=True).tolist()
    collection = get_kb_collection()
    if collection is None:
        return 0

    existing = collection.count()
    ids = [f"{filename}_{existing + i}" for i in range(len(chunks))]
    metadatas = [{"source": filename, "chunk_idx": i} for i in range(len(chunks))]
    collection.upsert(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
    return len(chunks)


def retrieve_context(query: str, top_k: int = 3) -> str:

    collection = get_kb_collection()
    if collection is None or collection.count() == 0:
        return ""
    try:
        from .matching import get_model
        model = get_model()
        vec = model.encode(query, normalize_embeddings=True).tolist()
        n = min(top_k, collection.count())
        results = collection.query(
            query_embeddings=[vec],
            n_results=n,
            include=["documents", "metadatas"],
        )
        lines = []
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            src = meta.get("source", "面经")
            lines.append(f"[{src}]\n{doc}")
        return "\n\n".join(lines)
    except Exception as e:
        logger.warning("RAG 检索失败: %s", e)
        return ""


def get_kb_stats() -> dict:
    collection = get_kb_collection()
    if collection is None:
        return {"count": 0, "ready": False}
    return {"count": collection.count(), "ready": True}


def get_kb_segments(limit: int = 50, offset: int = 0) -> dict:

    collection = get_kb_collection()
    if collection is None:
        return {"segments": [], "total": 0}
    total = collection.count()
    if total == 0:
        return {"segments": [], "total": 0}
    # ChromaDB peek 只能取前 N 条，用 get 支持 offset
    try:
        result = collection.get(
            limit=min(limit, 200),
            offset=offset,
            include=["documents", "metadatas"],
        )
        segments = []
        for doc_id, doc, meta in zip(
            result.get("ids", []),
            result.get("documents", []),
            result.get("metadatas", []),
        ):
            segments.append({
                "id": doc_id,
                "source": (meta or {}).get("source", "未知来源"),
                "preview": (doc or "")[:200],
            })
        return {"segments": segments, "total": total}
    except Exception as e:
        logger.warning("get_kb_segments 失败: %s", e)
        return {"segments": [], "total": total}



def create_session(style: str, resume_text: str = "", job_name: str = "", job_summary: str = "") -> str:
    session_id = str(uuid.uuid4())
    cfg = STYLE_CONFIG.get(style, STYLE_CONFIG["technical"])
    _sessions[session_id] = {
        "id": session_id,
        "style": style,
        "style_name": cfg["name"],
        "resume_text": resume_text,
        "job_name": job_name,
        "job_summary": job_summary,
        "history": [],          # [{"role": "assistant"|"user", "content": str}]
        "created_at": time.time(),
        "turn": 0,
        "finished": False,
    }
    return session_id


def get_session(session_id: str) -> Optional[dict]:
    return _sessions.get(session_id)


def add_message(session_id: str, role: str, content: str):
    if session_id not in _sessions:
        return
    _sessions[session_id]["history"].append({"role": role, "content": content})
    if role == "user":
        _sessions[session_id]["turn"] += 1


def build_messages(session: dict, user_input: str) -> list:
    style = session["style"]
    cfg = STYLE_CONFIG.get(style, STYLE_CONFIG["technical"])
    system_text = cfg["system"]


    if session.get("job_name"):
        system_text += f"\n\n【应聘岗位】{session['job_name']}"


    if session.get("job_summary"):
        system_text += f"\n\n【岗位描述（JD）】\n{session['job_summary'][:1500]}"


    if session.get("resume_text"):
        system_text += f"\n\n【候选人简历（请据此深挖追问，不要直接复述）】\n{session['resume_text'][:2000]}"


    rag_ctx = retrieve_context(user_input, top_k=3)
    if rag_ctx:
        system_text += f"\n\n【相关面经参考（据此丰富问题的针对性，不要直接引用）】\n{rag_ctx}"

    system_text += (
        "\n\n【通用规则（始终遵守）】\n"
        "- 始终保持面试官角色，绝对不暴露你是AI或大语言模型。\n"
        "- 每次回复用真实对话的口语语气，将对上一回答的即时反应与下一个问题自然融合成流畅的话，\n"
        '  绝对禁止使用"点评："、"问题："、"亮点："、"薄弱点："等任何结构化标签或分段格式。\n'
        "- 每轮只问一个问题，不能同时问多个问题。\n"
        "- 回复总字数控制在120字以内。\n"
        "- 第10轮后主动进入收尾阶段。\n"
        "- 使用简体中文，语气符合本风格的定位。\n"
    )
    

    messages = [{"role": "system", "content": system_text}]


    for msg in session["history"][-16:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": user_input})
    return messages



async def stream_interview_response(messages: list) -> AsyncGenerator[str, None]:
    """调用 qwen-plus 流式生成面试官回复，逐 token yield"""
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage


    lc_msgs = []
    for m in messages:
        if m["role"] == "system":
            lc_msgs.append(SystemMessage(content=m["content"]))
        elif m["role"] == "user":
            lc_msgs.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            lc_msgs.append(AIMessage(content=m["content"]))

    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY")
    llm = ChatOpenAI(
        model="qwen-plus",
        temperature=0.75,
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        timeout=120,
        max_retries=1,
        extra_body={"enable_thinking": False},
    )

    async for chunk in llm.astream(lc_msgs):
        token = chunk.content
        if token:
            yield token


async def generate_opener(session: dict) -> AsyncGenerator[str, None]:
 
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage

    style = session["style"]
    cfg = STYLE_CONFIG.get(style, STYLE_CONFIG["technical"])

    resume_snippet = (session.get("resume_text") or "")[:1500]
    jd_snippet = (session.get("job_summary") or "")[:800]
    job_name = session.get("job_name") or "该岗位"

    prompt = (
        f"【面试风格】{cfg['name']}\n"
        f"【面试官人设】\n{cfg['system'][:300]}\n\n"
        f"【应聘岗位】{job_name}\n"
    )
    if jd_snippet:
        prompt += f"【岗位描述（JD）摘要】\n{jd_snippet}\n\n"
    if resume_snippet:
        prompt += f"【候选人简历】\n{resume_snippet}\n\n"

    prompt += (
        f"【开场白生成要求】\n{cfg['opener_instruction']}\n\n"
        "请直接输出开场白正文，不要加任何说明或前缀。"
    )

    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY")
    llm = ChatOpenAI(
        model="qwen-plus",
        temperature=0.7,
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        timeout=60,
        max_retries=1,
        extra_body={"enable_thinking": False},
    )

    async for chunk in llm.astream([
        SystemMessage(content="你是一位专业面试官，正在生成面试开场白。"),
        HumanMessage(content=prompt),
    ]):
        if chunk.content:
            yield chunk.content


async def generate_summary(session: dict) -> AsyncGenerator[str, None]:

    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage

    history_text = ""
    for msg in session["history"]:
        role = "【面试官】" if msg["role"] == "assistant" else "【候选人】"
        history_text += f"{role}\n{msg['content']}\n\n"

    style_name = STYLE_CONFIG.get(session["style"], {}).get("name", "面试")

    prompt = f"""以下是一场{style_name}的完整对话记录，共{session['turn']}轮问答：

{history_text}

请作为面试评估专家，给出结构化面试总结报告，包含：
1. **总体评价**（2-3句综合评价）
2. **优势亮点**（3条，列举候选人表现好的地方）
3. **待提升点**（2-3条，指出不足和改进建议）
4. **综合评分**（100分制，给出分数和一句话理由）
5. **面试建议**（1-2条针对性的准备建议）

请用中文回答，格式清晰。"""

    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY")
    llm = ChatOpenAI(
        model="qwen-plus",
        temperature=0.3,
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        timeout=120,
        max_retries=1,
        extra_body={"enable_thinking": False},
    )

    async for chunk in llm.astream([SystemMessage(content="你是专业的面试评估专家"), HumanMessage(content=prompt)]):
        if chunk.content:
            yield chunk.content
