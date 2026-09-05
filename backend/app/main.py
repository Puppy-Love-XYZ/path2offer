from dotenv import load_dotenv
from .matching import start_indexing
import os as _os
from .city_coordinates_complete import CITY_COORDS

load_dotenv(_os.path.join(_os.path.dirname(__file__), '..', '.env'))

COZE_API_TOKEN = _os.getenv("COZE_API_TOKEN", "")
COZE_BOT_ID = _os.getenv("COZE_BOT_ID", "7605470089049096238")
COZE_API_BASE = "https://api.coze.cn"
COZE_UPLOAD_URL = "https://api.coze.cn/v1/files/upload"
COZE_CHAT_URL = "https://api.coze.cn/v3/chat"

from fastapi import FastAPI, Depends, Query, HTTPException, UploadFile, File as FastAPIFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from .database import engine, get_db, SessionLocal
from . import models
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import asyncio
import json
import re
import httpx
import logging
import time


from .auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, validate_password_strength,
)
from .models import User, UserProfile, Job
from .models import ResumeAnalysis, MatchingHistory, InterviewRecord
from .models import JobTopic, JobTopicRelation

app = FastAPI(title="Job Analysis API", version="1.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)


_AGG_CACHE: dict = {}
_AGG_CACHE_TTL = 3600  

def _clear_agg_cache():
    """清空 aggregate 缓存，接口结构变更时调用"""
    _AGG_CACHE.clear()

_clear_agg_cache()  


JOB_CATEGORIES = [
    {"name": "人工智能", "keywords": ["人工智能", "机器学习", "深度学习", "大模型", "AI", "算法", "自然语言处理", "计算机视觉", "语音识别", "推荐系统"], "color": "#409EFF"},
    {"name": "智能系统", "keywords": ["智能系统", "智能控制", "智能驾驶", "机器人", "自动驾驶", "系统架构", "控制系统", "嵌入式", "决策系统", "协同系统"], "color": "#5B9FB8"},
    {"name": "物联网", "keywords": ["物联网", "IoT", "传感器", "嵌入式", "边缘计算", "无线通信", "智能硬件", "工业互联网", "通信协议", "设备管理"], "color": "#67C23A"},
    {"name": "大数据", "keywords": ["大数据", "数据工程", "数据分析", "ETL", "Hadoop", "Spark", "数据平台", "实时计算", "数据治理", "数据仓库"], "color": "#E6A23C"},
    {"name": "技术开发", "keywords": ["工程师", "开发", "程序员", "架构师", "技术", "前端", "后端", "全栈", "测试"], "color": "#409EFF"},
    {"name": "数据/AI",  "keywords": ["数据", "算法", "机器学习", "人工智能", "大数据", "分析", "BI", "量化"],    "color": "#67C23A"},
    {"name": "产品/设计","keywords": ["产品", "设计师", "UI", "UX", "交互", "视觉"],                             "color": "#E6A23C"},
    {"name": "运营/市场","keywords": ["运营", "市场", "营销", "推广", "品牌", "新媒体", "策划"],                  "color": "#F56C6C"},
    {"name": "销售/商务","keywords": ["销售", "商务", "BD", "客户", "采购"],                                     "color": "#909399"},
    {"name": "财务/法务","keywords": ["财务", "会计", "审计", "法务", "风控", "合规"],                           "color": "#00b4d8"},
    {"name": "管理",     "keywords": ["总监", "经理", "主管", "总裁", "VP", "CTO", "COO"],                      "color": "#722ED1"},
]


@app.on_event("startup")
async def app_startup():
    models.Base.metadata.create_all(bind=engine)
    print("✅ 后端启动完成")
    # 所有耗时任务暂时禁用

def _precompute_all_categories() -> None:
    from .tf_wordcloud import build_lda_wordcloud, load_precomputed, save_precomputed
    db = SessionLocal()
    try:
        for cat in JOB_CATEGORIES:
            cat_name = cat["name"]
            if load_precomputed(cat_name) is not None:
                logger.info("分类词云已有预计算缓存，跳过: %s", cat_name)
                continue
            try:
                kw_parts = [f"job_name LIKE :ck{i}" for i in range(len(cat["keywords"]))]
                params = {f"ck{i}": f"%{kw}%" for i, kw in enumerate(cat["keywords"])}
                where_sql = " OR ".join(kw_parts)
                rows = db.execute(
                    text(f"SELECT job_summary FROM jobs WHERE ({where_sql}) AND job_summary IS NOT NULL"),
                    params,
                ).fetchall()
                texts = [r[0] for r in rows if r[0]]
                logger.info("预计算分类词云: %s，共 %d 篇文档", cat_name, len(texts))
                word_cloud_data = build_lda_wordcloud(texts, num_words=60)
                save_precomputed(cat_name, word_cloud_data)
            except Exception as e:
                logger.error("预计算分类 '%s' 失败: %s", cat_name, e)
    finally:
        db.close()


@app.on_event("startup")
async def _startup_precompute():
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _precompute_all_categories)


@app.on_event("startup")
async def _startup_matching_index():
    from .matching import start_indexing
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, lambda: start_indexing(SessionLocal))


# ==================== 岗位匹配接口 ====================

@app.get("/api/matching/status")
def matching_index_status():
    from .matching import get_index_status
    return get_index_status()


@app.post("/api/matching/auto")
async def matching_auto_recommend(
    file: UploadFile = File(...),
    top_k: int = Query(20, ge=5, le=50),
    db: Session = Depends(get_db),
):
    from .matching import auto_recommend, extract_text_from_file, get_index_status
    status = get_index_status()
    if status["status"] != "ready":
        pct = 0
        if status["total"]:
            pct = round(status["indexed"] / status["total"] * 100)
        raise HTTPException(
            503,
            detail=f"向量库构建中（{pct}%），完成后再试。首次约需 15 分钟。",
        )
    content = await file.read()
    resume_text = extract_text_from_file(content, file.filename or "")
    if not resume_text.strip():
        raise HTTPException(400, detail="无法从文件中提取文本，请检查文件格式")
    matches = auto_recommend(resume_text, top_k=top_k, db=db)
    from .matching import _w2v_available
    return {"matches": matches, "resume_preview": resume_text[:300], "w2v_available": bool(_w2v_available)}


@app.post("/api/matching/specific")
async def matching_specific_job(
    file: UploadFile = File(...),
    job_id: int = Query(...),
    db: Session = Depends(get_db),
):
    from .matching import specific_match, extract_text_from_file
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(404, detail="岗位不存在")
    content = await file.read()
    resume_text = extract_text_from_file(content, file.filename or "")
    if not resume_text.strip():
        raise HTTPException(400, detail="无法从文件中提取文本")
    report = specific_match(resume_text, job)
    return {
        "match_score": report["total_score"],
        "report": report,
        "job": job.to_dict(),
        "resume_preview": resume_text[:300],
    }


@app.get("/api/matching/jobs/search")
def matching_job_search(
    keyword: str = Query(..., min_length=1),
    limit: int = Query(50, ge=5, le=300),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        text("""
            SELECT id, job_name, company_name, work_city,
                   job_salary, your_education, working_exp,
                   LEFT(job_summary, 300) AS jd_preview
            FROM bigdata_recruit_job
            WHERE job_name LIKE :kw OR company_name LIKE :kw
            ORDER BY
                CASE WHEN job_name LIKE :exact THEN 0 ELSE 1 END,
                job_name
            LIMIT :lim OFFSET :off
        """),
        {"kw": f"%{keyword}%", "exact": keyword, "lim": limit, "off": offset},
    ).fetchall()
    total = db.execute(
        text("SELECT COUNT(*) FROM bigdata_recruit_job WHERE job_name LIKE :kw OR company_name LIKE :kw"),
        {"kw": f"%{keyword}%"},
    ).scalar()
    return {
        "jobs": [
            {
                "id": r.id,
                "job_name": r.job_name,
                "company_name": r.company_name,
                "work_city": r.work_city,
                "job_salary": r.job_salary,
                "your_education": r.your_education,
                "working_exp": r.working_exp,
                "jd_preview": r.jd_preview,
            }
            for r in rows
        ],
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@app.get("/api/matching/jobs/{job_id}")
def matching_job_detail(job_id: int, db: Session = Depends(get_db)):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(404, detail="岗位不存在")
    return job.to_dict()


@app.post("/api/matching/parse-resume")
async def matching_parse_resume(file: UploadFile = File(...)):
    from .resume_agents import extract_resume_structured
    content = await file.read()
    try:
        parsed = await extract_resume_structured(content, file.filename or "resume")
    except ValueError as e:
        raise HTTPException(400, detail=str(e))
    except Exception as e:
        raise HTTPException(500, detail=f"简历解析失败：{e}")
    return {"parsed": parsed}


@app.post("/api/matching/deep-analysis")
async def matching_deep_analysis(
    file: UploadFile = File(...),
    job_id: int = Query(...),
    db: Session = Depends(get_db),
):
    import httpx
    import json as json_mod
    from .matching import specific_match, extract_text_from_file
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(404, detail="岗位不存在")
    content = await file.read()
    resume_text = extract_text_from_file(content, file.filename or "")
    if not resume_text.strip():
        raise HTTPException(400, detail="无法从文件中提取文本")
    report = specific_match(resume_text, job)
    dims = report["dimensions"]
    matched_skills = dims.get("skills", {}).get("matched_skills", [])
    deep_analysis: dict = {"strengths": [], "weaknesses": [], "advice": []}
    api_key = _os.getenv("DASHSCOPE_API_KEY") or ""
    if api_key:
        prompt = (
            "你是一位专业的职业发展顾问，请根据以下信息深度分析候选人与目标岗位的匹配情况。\n\n"
            "## 候选人简历摘要\n"
            f"{resume_text[:1500]}\n\n"
            "## 目标岗位\n"
            f"职位：{job.job_name}\n"
            f"公司：{job.company_name}\n"
            f"学历要求：{job.your_education or '不限'}\n"
            f"经验要求：{job.working_exp or '不限'}\n"
            f"岗位描述：{(job.job_summary or '')[:800]}\n\n"
            "## 算法初步评估\n"
            f"- 综合匹配分：{report['total_score']}分（满分100）\n"
            f"- 语义匹配：{dims.get('semantic', {}).get('score', 0)}分\n"
            f"- 技能覆盖：{dims.get('skills', {}).get('score', 0)}分\n"
            f"- 命中技能词：{', '.join(matched_skills[:8]) if matched_skills else '无'}\n"
            f"- 经验评估：{dims.get('experience', {}).get('match', '')}\n"
            f"- 学历评估：{dims.get('education', {}).get('match', '')}\n\n"
            "请从三个角度给出深度分析，每点2-3条，语言简洁有力，直接指出具体要点。\n"
            "以纯JSON格式输出（不要有任何额外文字）：\n"
            '{"strengths":["优势亮点1","优势亮点2","优势亮点3"],'
            '"weaknesses":["差距不足1","差距不足2"],'
            '"advice":["投递建议1","投递建议2","投递建议3"]}'
        )
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                    json={
                        "model": "qwen-plus",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3,
                    },
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                )
                resp.raise_for_status()
                raw = resp.json()["choices"][0]["message"]["content"].strip()
                if "```" in raw:
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                deep_analysis = json_mod.loads(raw)
        except Exception as e:
            logger.warning("大模型深度分析失败，降级为纯算法结果：%s", e)
    return {
        "match_score": report["total_score"],
        "report": report,
        "deep_analysis": deep_analysis,
        "job": job.to_dict(),
        "resume_preview": resume_text[:300],
    }


@app.get("/api/interview/styles")
def interview_get_styles():
    from .interview_rag import STYLE_CONFIG
    return {
        k: {"name": v["name"], "icon": v["icon"], "desc": v["desc"]}
        for k, v in STYLE_CONFIG.items()
    }


@app.get("/api/interview/kb/stats")
def interview_kb_stats(current_user=Depends(get_current_user)):
    from .interview_rag import get_kb_stats
    return get_kb_stats()


@app.get("/api/interview/kb/segments")
def interview_kb_segments(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
):
    from .interview_rag import get_kb_segments
    return get_kb_segments(limit=limit, offset=offset)


@app.delete("/api/interview/kb/clear")
def interview_kb_clear(current_user=Depends(get_current_user)):
    from .interview_rag import get_kb_collection
    col = get_kb_collection()
    if col and col.count() > 0:
        ids = col.get(include=[])["ids"]
        if ids:
            col.delete(ids=ids)
    return {"message": "知识库已清空"}


@app.post("/api/interview/kb/ingest")
async def interview_kb_ingest(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    from .interview_rag import ingest_document
    content = await file.read()
    count = ingest_document(content, file.filename or "document")
    return {"message": f"成功入库 {count} 个片段", "chunks": count, "filename": file.filename}


@app.post("/api/interview/session/start")
async def interview_session_start(
    file: Optional[UploadFile] = File(None),
    style: str = Query("technical"),
    job_name: str = Query(""),
    job_id: int = Query(0),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from .interview_rag import (
        create_session, add_message,
        generate_opener,
    )
    from .matching import extract_text_from_file
    resume_text = ""
    if file and file.filename:
        content = await file.read()
        resume_text = extract_text_from_file(content, file.filename)
    job_summary = ""
    resolved_job_name = job_name
    if job_id:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job_summary = job.job_summary or ""
            if not resolved_job_name:
                resolved_job_name = job.job_name or ""
    session_id = create_session(
        style=style,
        resume_text=resume_text,
        job_name=resolved_job_name,
        job_summary=job_summary,
    )
    async def sse_gen():
        from .interview_rag import get_session
        yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
        session = get_session(session_id)
        tokens = []
        try:
            async for token in generate_opener(session):
                tokens.append(token)
                yield f"data: {json.dumps({'type': 'token', 'text': token})}\n\n"
        except Exception as e:
            logger.error("开场白生成失败: %s", e)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            return
        full = "".join(tokens)
        add_message(session_id, "assistant", full)
        yield f"data: {json.dumps({'type': 'done', 'turn': 0})}\n\n"
    return StreamingResponse(sse_gen(), media_type="text/event-stream")


@app.post("/api/interview/session/{session_id}/chat")
async def interview_session_chat(
    session_id: str,
    body: dict,
    current_user=Depends(get_current_user),
):
    from .interview_rag import (
        get_session, add_message, build_messages, stream_interview_response,
    )
    session = get_session(session_id)
    if not session:
        raise HTTPException(404, detail="会话不存在或已过期")
    user_msg = (body.get("message") or "").strip()
    if not user_msg:
        raise HTTPException(400, detail="消息不能为空")
    messages = build_messages(session, user_msg)
    add_message(session_id, "user", user_msg)
    async def sse_gen():
        tokens = []
        try:
            async for token in stream_interview_response(messages):
                tokens.append(token)
                yield f"data: {json.dumps({'type': 'token', 'text': token})}\n\n"
        except Exception as e:
            logger.error("面试LLM调用失败: %s", e)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            return
        full_response = "".join(tokens)
        add_message(session_id, "assistant", full_response)
        turn = session["turn"]
        yield f"data: {json.dumps({'type': 'done', 'turn': turn})}\n\n"
    return StreamingResponse(sse_gen(), media_type="text/event-stream")


@app.post("/api/interview/session/{session_id}/finish")
async def interview_session_finish(
    session_id: str,
    current_user=Depends(get_current_user),
):
    from .interview_rag import get_session, generate_summary
    session = get_session(session_id)
    if not session:
        raise HTTPException(404, detail="会话不存在")
    if session["turn"] < 1:
        raise HTTPException(400, detail="至少完成一轮问答后才能生成总结")
    session["finished"] = True
    user_id = current_user.id
    async def sse_gen():
        summary_parts: list[str] = []
        try:
            async for token in generate_summary(session):
                summary_parts.append(token)
                yield f"data: {json.dumps({'type': 'token', 'text': token})}\n\n"
        except Exception as e:
            logger.error("面试总结生成失败: %s", e)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            return
        try:
            with SessionLocal() as save_db:
                record = InterviewRecord(
                    user_id=user_id,
                    session_id=session_id,
                    style=session.get("style"),
                    style_name=session.get("style_name"),
                    job_name=session.get("job_name", ""),
                    turns=session.get("turn", 0),
                    duration_seconds=int(time.time() - session.get("created_at", time.time())),
                    history_json=json.dumps(session.get("history", []), ensure_ascii=False),
                    summary="".join(summary_parts),
                )
                save_db.add(record)
                save_db.commit()
        except Exception as e:
            logger.error("保存面试记录失败: %s", e)
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    return StreamingResponse(sse_gen(), media_type="text/event-stream")


@app.get("/api/interview/session/{session_id}/history")
def interview_session_history(
    session_id: str,
    current_user=Depends(get_current_user),
):
    from .interview_rag import get_session
    session = get_session(session_id)
    if not session:
        raise HTTPException(404, detail="会话不存在")
    return {
        "session_id": session_id,
        "style": session["style"],
        "style_name": session["style_name"],
        "turn": session["turn"],
        "history": session["history"],
        "finished": session["finished"],
        "duration": int(time.time() - session["created_at"]),
    }


# ==================== 测试 Coze 接口 ====================

@app.post("/api/test/coze-upload")
async def test_coze_upload(file: UploadFile = File(...)):
    try:
        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="上传的文件内容为空")
        headers = {
            "Authorization": f"Bearer {COZE_API_TOKEN}"
        }
        files = {
            "file": (file.filename, file_content, file.content_type)
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url=COZE_UPLOAD_URL,
                headers=headers,
                files=files
            )
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            response_data = {
                "error": "Coze 返回非 JSON 格式数据",
                "raw_response": response.text
            }
        return {
            "success": response.status_code == 200,
            "coze_status_code": response.status_code,
            "coze_response": response_data,
            "request_info": {
                "filename": file.filename,
                "file_size": len(file_content),
                "content_type": file.content_type,
                "token_used": COZE_API_TOKEN[:10] + "..."
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"测试 Coze 文件上传失败：{str(e)}"
        )


@app.post("/api/test/coze-chat")
async def test_coze_chat():
    headers = {
        "Authorization": f"Bearer {COZE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "bot_id": COZE_BOT_ID,
        "user_id": "123456789",
        "stream": True,
        "auto_save_history": True,
        "additional_messages": [
            {"role": "user", "type": "question", "content_type": "text", "content": "测试聊天权限"}
        ]
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            url="https://api.coze.cn/v3/chat",
            headers=headers,
            json=payload
        )
    return {
        "status_code": response.status_code,
        "response": response.json() if response.status_code == 200 else response.text
    }


@app.get("/")
def read_root():
    return {"message": "Welcome to Job Analysis API", "version": "1.0"}


@app.get("/jobs")
def get_jobs(
        db: Session = Depends(get_db),
        skip: int = 0,
        limit: int = 100,
        job_name: Optional[str] = Query(None, description="岗位名称过滤"),
        work_city: Optional[str] = Query(None, description="工作城市过滤"),
        work_major: Optional[str] = Query(None, description="专业要求过滤"),
        company_name: Optional[str] = Query(None, description="公司名称过滤")
):
    query = db.query(models.Job)
    if job_name:
        query = query.filter(models.Job.job_name.like(f"%{job_name}%"))
    if work_city:
        query = query.filter(models.Job.work_city.like(f"%{work_city}%"))
    if work_major:
        query = query.filter(models.Job.work_major.like(f"%{work_major}%"))
    if company_name:
        query = query.filter(models.Job.company_name.like(f"%{company_name}%"))
    total = query.count()
    jobs = query.offset(skip).limit(limit).all()
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "jobs": [job.to_dict() for job in jobs]
    }


@app.get("/jobs/{job_id}")
def get_job_by_id(job_id: int, db: Session = Depends(get_db)):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_dict()


@app.get("/jobs/search/by-keyword")
def search_jobs_by_keyword(
        keyword: str = Query(..., description="搜索关键词"),
        search_in: str = Query("job_name", description="搜索字段: job_name, company_name, job_summary等"),
        db: Session = Depends(get_db),
        skip: int = 0,
        limit: int = 50
):
    query = db.query(models.Job)
    if search_in == "job_name":
        query = query.filter(models.Job.job_name.like(f"%{keyword}%"))
    elif search_in == "company_name":
        query = query.filter(models.Job.company_name.like(f"%{keyword}%"))
    elif search_in == "job_summary":
        query = query.filter(models.Job.job_summary.like(f"%{keyword}%"))
    elif search_in == "all":
        query = query.filter(
            models.Job.job_name.like(f"%{keyword}%") |
            models.Job.company_name.like(f"%{keyword}%") |
            models.Job.job_summary.like(f"%{keyword}%")
        )
    total = query.count()
    jobs = query.offset(skip).limit(limit).all()
    return {
        "total": total,
        "keyword": keyword,
        "search_in": search_in,
        "jobs": [job.to_dict() for job in jobs]
    }
_FILTER_OPTIONS_CACHE: dict = {}
_FILTER_OPTIONS_TTL = 3600  

@app.get("/api/jobs/filter-options")
def get_job_filter_options(db: Session = Depends(get_db)):
    import time as _time
    now = _time.time()
    if _FILTER_OPTIONS_CACHE.get("ts") and now - _FILTER_OPTIONS_CACHE["ts"] < _FILTER_OPTIONS_TTL:
        return _FILTER_OPTIONS_CACHE["data"]
    cities_rows = db.execute(text("""
        SELECT work_city, COUNT(*) cnt FROM jobs
        WHERE work_city IS NOT NULL AND work_city != ''
        GROUP BY work_city ORDER BY cnt DESC LIMIT 80
    """)).fetchall()
    cities = [r[0] for r in cities_rows]
    edu_rows = db.execute(text("""
        SELECT DISTINCT your_education FROM jobs
        WHERE your_education IS NOT NULL AND your_education != ''
    """)).fetchall()
    edu_raw = sorted(set(r[0].strip() for r in edu_rows if r[0]))
    size_rows = db.execute(text("""
        SELECT company_size, COUNT(*) cnt FROM jobs
        WHERE company_size IS NOT NULL AND company_size != ''
        GROUP BY company_size ORDER BY cnt DESC
    """)).fetchall()
    company_sizes = [r[0] for r in size_rows]
    type_rows = db.execute(text("""
        SELECT DISTINCT work_type FROM jobs
        WHERE work_type IS NOT NULL AND work_type != ''
    """)).fetchall()
    work_types = sorted(set(r[0].strip() for r in type_rows if r[0]))
    exp_rows = db.execute(text("""
        SELECT
            CASE WHEN working_exp IN ('经验不限', '不限') THEN '不限' ELSE working_exp END AS working_exp,
            COUNT(*) cnt
        FROM jobs
        WHERE working_exp IS NOT NULL AND working_exp != ''
        GROUP BY 1 ORDER BY cnt DESC
    """)).fetchall()
    working_exps = list(dict.fromkeys(r[0] for r in exp_rows))
    benefit_rows = db.execute(text("""
        SELECT company_benefits, COUNT(*) cnt
        FROM bigdata_recruit_job 
        WHERE company_benefits IS NOT NULL 
          AND company_benefits != ''
          AND LENGTH(company_benefits) BETWEEN 2 AND 50
        GROUP BY company_benefits 
        ORDER BY cnt DESC 
        LIMIT 50
    """)).fetchall()
    benefit_keywords = [r[0] for r in benefit_rows if r[0]]
    result = {
        "cities": cities,
        "education_raw": edu_raw,
        "company_sizes": company_sizes,
        "work_types": work_types,
        "working_exps": working_exps,
        "benefit_keywords": benefit_keywords,
    }
    _FILTER_OPTIONS_CACHE["ts"] = now
    _FILTER_OPTIONS_CACHE["data"] = result
    return result


_EDU_HIERARCHY = {
    "大专": 1, "专科": 1,
    "本科": 2, "学士": 2,
    "硕士": 3, "研究生": 3,
    "博士": 4,
}
_EDU_TIERS = {
    "不限": None,
    "专科及以上": 1,
    "本科及以上": 2,
    "硕士及以上": 3,
    "博士": 4,
}

from pydantic import BaseModel as _BaseModel
from typing import List as _List

class JobFilterRequest(_BaseModel):
    cities: _List[str] = []
    work_types: _List[str] = []
    salary_min: int | None = None   
    salary_max: int | None = None
    education: str | None = None    
    major_keyword: str | None = None
    company_sizes: _List[str] = []
    benefit_keywords: _List[str] = []
    working_exps: _List[str] = []
    page: int = 1
    page_size: int = 20

@app.post("/api/jobs/filter")
def filter_jobs(req: JobFilterRequest, db: Session = Depends(get_db)):
    conditions = ["1=1"]
    params: dict = {}
    if req.cities:
        placeholders = ", ".join(f":city{i}" for i in range(len(req.cities)))
        conditions.append(f"work_city IN ({placeholders})")
        for i, c in enumerate(req.cities):
            params[f"city{i}"] = c
    if req.work_types:
        placeholders = ", ".join(f":wt{i}" for i in range(len(req.work_types)))
        conditions.append(f"work_type IN ({placeholders})")
        for i, wt in enumerate(req.work_types):
            params[f"wt{i}"] = wt
    if req.salary_min is not None:
        conditions.append("salary_max >= :smin")
        params["smin"] = req.salary_min * 1000
    if req.salary_max is not None:
        conditions.append("salary_min <= :smax")
        params["smax"] = req.salary_max * 1000
    if req.education and req.education != "不限":
        min_level = _EDU_TIERS.get(req.education)
        if min_level is not None:
            eligible = [k for k, v in _EDU_HIERARCHY.items() if v >= min_level]
            if eligible:
                placeholders = ", ".join(f":edu{i}" for i in range(len(eligible)))
                conditions.append(f"your_education IN ({placeholders})")
                for i, e in enumerate(eligible):
                    params[f"edu{i}"] = e
    if req.major_keyword:
        conditions.append("work_major LIKE :major")
        params["major"] = f"%{req.major_keyword}%"
    if req.company_sizes:
        placeholders = ", ".join(f":cs{i}" for i in range(len(req.company_sizes)))
        conditions.append(f"company_size IN ({placeholders})")
        for i, cs in enumerate(req.company_sizes):
            params[f"cs{i}"] = cs
    if req.working_exps:
        expanded_exps: list = []
        for we in req.working_exps:
            expanded_exps.append(we)
            if we == '不限':
                expanded_exps.append('经验不限')
        placeholders = ", ".join(f":we{i}" for i in range(len(expanded_exps)))
        conditions.append(f"working_exp IN ({placeholders})")
        for i, we in enumerate(expanded_exps):
            params[f"we{i}"] = we
    for i, kw in enumerate(req.benefit_keywords):
        conditions.append(f"company_benefits LIKE :bkw{i}")
        params[f"bkw{i}"] = f"%{kw}%"
    where = " AND ".join(conditions)
    offset = (req.page - 1) * req.page_size
    count_sql = text(f"SELECT COUNT(*) FROM jobs WHERE {where}")
    total = db.execute(count_sql, params).scalar()
    data_sql = text(f"""
        SELECT id, job_name, company_name, work_city, job_salary,
               salary_min, salary_max, your_education, working_exp,
               company_size, work_type, work_major, industry_name,
               job_summary, company_benefits
        FROM jobs WHERE {where}
        ORDER BY id DESC
        LIMIT :limit OFFSET :offset
    """)
    params["limit"] = req.page_size
    params["offset"] = offset
    rows = db.execute(data_sql, params).fetchall()
    jobs = [dict(r._mapping) for r in rows]
    return {"total": total, "page": req.page, "page_size": req.page_size, "jobs": jobs}


@app.get("/api/favorites")
def list_favorites(
    page: int = Query(1), limit: int = Query(20),
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    from .models import FavoriteJob
    q = db.query(models.FavoriteJob).filter(models.FavoriteJob.user_id == current_user.id)
    total = q.count()
    favs = q.order_by(models.FavoriteJob.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    result = []
    for fav in favs:
        job = fav.job
        result.append({
            "fav_id": fav.id,
            "job_id": fav.job_id,
            "favorited_at": fav.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "job_name": job.job_name if job else None,
            "company_name": job.company_name if job else None,
            "work_city": job.work_city if job else None,
            "job_salary": job.job_salary if job else None,
            "your_education": job.your_education if job else None,
            "working_exp": job.working_exp if job else None,
            "company_size": job.company_size if job else None,
            "work_type": job.work_type if job else None,
            "job_summary": job.job_summary if job else None,
        })
    return {"total": total, "page": page, "items": result}


@app.post("/api/favorites/{job_id}")
def add_favorite(
    job_id: int,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")
    exists = db.query(models.FavoriteJob).filter(
        models.FavoriteJob.user_id == current_user.id,
        models.FavoriteJob.job_id == job_id
    ).first()
    if exists:
        return {"ok": True, "fav_id": exists.id}
    fav = models.FavoriteJob(user_id=current_user.id, job_id=job_id)
    db.add(fav)
    db.commit()
    db.refresh(fav)
    return {"ok": True, "fav_id": fav.id}


@app.delete("/api/favorites/{job_id}")
def remove_favorite(
    job_id: int,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    fav = db.query(models.FavoriteJob).filter(
        models.FavoriteJob.user_id == current_user.id,
        models.FavoriteJob.job_id == job_id
    ).first()
    if fav:
        db.delete(fav)
        db.commit()
    return {"ok": True}


@app.get("/api/favorites/ids")
def get_favorite_ids(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    rows = db.query(models.FavoriteJob.job_id).filter(
        models.FavoriteJob.user_id == current_user.id
    ).all()
    return {"ids": [r[0] for r in rows]}


@app.get("/api/persona/categories")
def get_job_categories(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT job_name, COUNT(*) AS cnt
        FROM jobs
        WHERE job_name IS NOT NULL
        GROUP BY job_name
    """)).fetchall()
    name_count = {r.job_name: r.cnt for r in rows}
    total_all = sum(name_count.values())
    result = []
    categorized: set = set()
    for cat in JOB_CATEGORIES:
        cat_count = 0
        for job_name, cnt in name_count.items():
            if job_name not in categorized and any(kw in job_name for kw in cat["keywords"]):
                cat_count += cnt
                categorized.add(job_name)
        result.append({
            "name": cat["name"],
            "count": cat_count,
            "color": cat["color"],
            "keywords": cat["keywords"],
        })
    return {"categories": result, "total": total_all}


@app.get("/api/persona/search")
def persona_search(
        keyword: str = Query("", description="搜索关键词（岗位名或公司名）"),
        db: Session = Depends(get_db),
        limit: int = Query(50, description="返回分组数量上限")
):
    kw = keyword.strip()
    if not kw:
        groups = db.execute(text("""
            SELECT job_name,
                   COUNT(*) AS total,
                   COUNT(DISTINCT work_city) AS city_count,
                   COUNT(DISTINCT company_name) AS company_count,
                   AVG((salary_min + salary_max) / 2.0) AS avg_salary
            FROM jobs
            WHERE job_name IS NOT NULL
            GROUP BY job_name
            ORDER BY total DESC
            LIMIT :limit
        """), {"limit": limit}).fetchall()
        return {
            "keyword": "",
            "total_jobs": 0,
            "total_cities": 0,
            "total_companies": 0,
            "groups": [
                {
                    "job_name": r.job_name,
                    "count": r.total,
                    "city_count": r.city_count,
                    "company_count": r.company_count,
                    "avg_salary": round(r.avg_salary / 1000, 1) if r.avg_salary else 0,
                }
                for r in groups
            ],
        }
    groups = db.execute(text("""
        SELECT job_name,
               COUNT(*) AS total,
               COUNT(DISTINCT work_city) AS city_count,
               COUNT(DISTINCT company_name) AS company_count,
               AVG((salary_min + salary_max) / 2.0) AS avg_salary
        FROM bigdata_recruit_job
        WHERE (job_name LIKE :kw OR company_name LIKE :kw)
          AND job_name IS NOT NULL
        GROUP BY job_name
        ORDER BY total DESC
        LIMIT :limit
    """), {"kw": f"%{kw}%", "limit": limit}).fetchall()
    totals = db.execute(text("""
        SELECT COUNT(*)                    AS total_jobs,
               COUNT(DISTINCT work_city)   AS total_cities,
               COUNT(DISTINCT company_name) AS total_companies
        FROM bigdata_recruit_job
        WHERE job_name LIKE :kw OR company_name LIKE :kw
    """), {"kw": f"%{kw}%"}).fetchone()
    return {
        "keyword": kw,
        "total_jobs": totals.total_jobs,
        "total_cities": totals.total_cities,
        "total_companies": totals.total_companies,
        "groups": [
            {
                "job_name": r.job_name,
                "count": r.total,
                "city_count": r.city_count,
                "company_count": r.company_count,
                "avg_salary": round(r.avg_salary / 1000, 1) if r.avg_salary else 0,
            }
            for r in groups
        ],
    }


@app.get("/api/persona/search/jobs")
def persona_search_job_detail(
        job_name: str = Query(..., description="岗位名称（精确）"),
        keyword: str = Query("", description="原始搜索关键词"),
        limit: int = Query(20),
        offset: int = Query(0),
        db: Session = Depends(get_db),
):
    extra = ""
    params: dict = {"job_name": job_name, "limit": limit, "offset": offset}
    if keyword.strip():
        extra = " AND company_name LIKE :kw"
        params["kw"] = f"%{keyword.strip()}%"
    rows = db.execute(text(f"""
        SELECT job_name, company_name, work_city, job_salary,
               salary_min, salary_max, working_exp, your_education, company_size
        FROM jobs
        WHERE job_name = :job_name {extra}
        ORDER BY COALESCE(salary_min + salary_max, 0) DESC
        LIMIT :limit OFFSET :offset
    """), params).fetchall()
    return {"jobs": [dict(r._mapping) for r in rows]}


@app.get("/api/persona/aggregate")
def persona_aggregate(
        job_name: Optional[str] = Query(None, description="精确匹配岗位名称"),
        keyword: Optional[str] = Query(None, description="关键词模糊匹配岗位/公司"),
        category: Optional[str] = Query(None, description="按分类名称筛选"),
        city: Optional[str] = Query(None, description="按城市筛选"),
        db: Session = Depends(get_db),
):
    cache_key = f"{job_name}|{keyword}|{category}|{city}"
    now = time.time()
    if cache_key in _AGG_CACHE:
        ts, cached = _AGG_CACHE[cache_key]
        if now - ts < _AGG_CACHE_TTL:
            return cached
    where_parts: list[str] = []
    params: dict = {}
    if job_name:
        where_parts.append("job_name = :job_name")
        params["job_name"] = job_name
    elif category:
        cat_info = next((c for c in JOB_CATEGORIES if c["name"] == category), None)
        if cat_info:
            kw_conds = " OR ".join(
                [f"job_name LIKE :ck{i}" for i in range(len(cat_info["keywords"]))]
            )
            params.update({f"ck{i}": f"%{kw}%" for i, kw in enumerate(cat_info["keywords"])})
            where_parts.append(f"({kw_conds})")
    elif keyword:
        where_parts.append("(job_name LIKE :kw OR company_name LIKE :kw)")
        params["kw"] = f"%{keyword}%"
    if city:
        where_parts.append("work_city = :city")
        params["city"] = city
    where_sql = " AND ".join(where_parts) if where_parts else "1=1"

    bar_sql = f"""
        SELECT industry_name AS name, COUNT(*) AS value
        FROM bigdata_recruit_job 
        WHERE {where_sql}
          AND industry_name IS NOT NULL 
          AND industry_name != ''
        GROUP BY industry_name 
        ORDER BY value DESC 
        LIMIT 15
    """
    bar_type = "industry"
    bar_data = [{"name": r.name, "value": r.value}
                for r in db.execute(text(bar_sql), params).fetchall()]

    pie_results = db.execute(text(f"""
        SELECT COALESCE(your_education, '未知') AS name, COUNT(*) AS value
        FROM jobs WHERE {where_sql}
        GROUP BY your_education ORDER BY value DESC
    """), params).fetchall()
    pie_data = [{"name": r.name, "value": r.value} for r in pie_results]

    box_results = db.execute(text(f"""
        SELECT 
            COALESCE(your_education, '未知') AS edu,
            MIN((salary_min + salary_max) / 2.0 / 1000.0) AS p0,
            AVG((salary_min + salary_max) / 2.0 / 1000.0) AS p50,
            MAX((salary_min + salary_max) / 2.0 / 1000.0) AS p100,
            COUNT(*) AS cnt
        FROM bigdata_recruit_job
        WHERE {where_sql} 
          AND salary_min IS NOT NULL 
          AND salary_max IS NOT NULL
        GROUP BY your_education
        HAVING COUNT(*) >= 3
        ORDER BY p50 DESC
    """), params).fetchall()
    
    box_data = []
    for r in box_results:
        p0, p50, p100 = float(r.p0), float(r.p50), float(r.p100)
        box_data.append({
            "name": r.edu,
            "min": round(p0, 1),
            "q1": round(p0 + (p50 - p0) * 0.25, 1),
            "median": round(p50, 1),
            "q3": round(p50 + (p100 - p50) * 0.25, 1),
            "max": round(p100, 1),
        })

    # 生成词云数据
    word_cloud_data = []
    try:
        rows_for_wc = db.execute(
            text(f"SELECT job_summary FROM bigdata_recruit_job WHERE {where_sql} AND job_summary IS NOT NULL LIMIT 3000"),
            params,
        ).fetchall()
        texts = [r[0] for r in rows_for_wc if r[0]]
        if texts:
            from .tf_wordcloud import build_lda_wordcloud
            word_cloud_data = build_lda_wordcloud(texts, num_words=60)
    except Exception as e:
        logger.warning("词云数据生成失败: %s", e)
        word_cloud_data = []

    map_results = db.execute(text(f"""
    SELECT work_city, COUNT(*) AS cnt,
           AVG((salary_min + salary_max) / 2.0) AS avg_salary
    FROM bigdata_recruit_job WHERE {where_sql} AND work_city IS NOT NULL AND work_city != ''
    GROUP BY work_city ORDER BY cnt DESC
"""), params).fetchall()

    city_coordinates = CITY_COORDS

    map_data = []
    # 需要忽略的词汇
    ignore_keywords = ["全国", "全国范围", "远程办公", "上市国企", "央企研究院", "大型国企正式"]

    for row in map_results:
        # 跳过非城市名称
        if any(kw in row.work_city for kw in ignore_keywords):
            continue
            
        if row.work_city in city_coordinates:
            lng, lat = city_coordinates[row.work_city]
            map_data.append({
                "name": row.work_city,
                "value": row.cnt,
                "lng": lng,
                "lat": lat,
                "avg_salary": round(row.avg_salary / 1000, 1) if row.avg_salary else 0
            })
    result = {
        "job_name": job_name or keyword or category or city or "全部岗位",
        "bar_data": bar_data,
        "bar_type": bar_type,
        "pie_data": pie_data,
        "box_data": box_data,
        "word_cloud_data": word_cloud_data,
        "map_data": map_data,
        "province_data": [],
    }
    _AGG_CACHE[cache_key] = (time.time(), result)
    return result


_WC_CACHE: dict = {}

@app.get("/api/persona/wordcloud")
def persona_wordcloud(
        job_name: Optional[str] = Query(None),
        keyword: Optional[str] = Query(None),
        category: Optional[str] = Query(None),
        db: Session = Depends(get_db),
):
    cache_key = f"wc|{job_name}|{keyword}|{category}"
    now = time.time()
    if category and not job_name and not keyword:
        from .tf_wordcloud import load_precomputed
        precomputed = load_precomputed(category)
        if precomputed is not None:
            return {"word_cloud_data": precomputed}
    if cache_key in _WC_CACHE:
        ts, cached = _WC_CACHE[cache_key]
        if now - ts < _AGG_CACHE_TTL:
            return cached
    where_parts: list[str] = []
    params: dict = {}
    if job_name:
        where_parts.append("job_name = :job_name")
        params["job_name"] = job_name
    elif category:
        cat_info = next((c for c in JOB_CATEGORIES if c["name"] == category), None)
        if cat_info:
            kw_conds = " OR ".join([f"job_name LIKE :ck{i}" for i in range(len(cat_info["keywords"]))])
            params.update({f"ck{i}": f"%{kw}%" for i, kw in enumerate(cat_info["keywords"])})
            where_parts.append(f"({kw_conds})")
    elif keyword:
        where_parts.append("(job_name LIKE :kw OR company_name LIKE :kw)")
        params["kw"] = f"%{keyword}%"
    where_sql = " AND ".join(where_parts) if where_parts else "1=1"
    rows = db.execute(
        text(f"SELECT job_summary FROM jobs WHERE {where_sql} AND job_summary IS NOT NULL"),
        params,
    ).fetchall()
    texts = [r[0] for r in rows if r[0]]
    from .tf_wordcloud import build_lda_wordcloud, save_precomputed
    word_cloud_data = build_lda_wordcloud(texts, num_words=60)
    result = {"word_cloud_data": word_cloud_data}
    _WC_CACHE[cache_key] = (now, result)
    if category and not job_name and not keyword:
        save_precomputed(category, word_cloud_data)
    return result
@app.get("/jobs/names/unique")
def get_unique_job_names(
        db: Session = Depends(get_db),
        limit: int = 200,
        sort_by: str = Query("count", description="排序方式: count, name")
):
    subquery = db.query(
        models.Job.job_name,
        func.count(models.Job.id).label("job_count"),
        func.avg(models.Job.salary_min).label("avg_min_salary"),
        func.avg(models.Job.salary_max).label("avg_max_salary")
    ).filter(
        models.Job.job_name.isnot(None),
        models.Job.job_name != ""
    ).group_by(
        models.Job.job_name
    ).subquery()
    query = db.query(
        subquery.c.job_name,
        subquery.c.job_count,
        subquery.c.avg_min_salary,
        subquery.c.avg_max_salary
    )
    if sort_by == "count":
        query = query.order_by(subquery.c.job_count.desc())
    elif sort_by == "name":
        query = query.order_by(subquery.c.job_name)
    results = query.limit(limit).all()
    return [
        {
            "job_name": row[0],
            "count": row[1],
            "avg_min_salary": round(float(row[2]), 2) if row[2] else None,
            "avg_max_salary": round(float(row[3]), 2) if row[3] else None,
            "avg_total_salary": round((float(row[2] or 0) + float(row[3] or 0)) / 2, 2) if row[2] and row[3] else None
        }
        for row in results
    ]


@app.get("/jobs/names/top-categories")
def get_top_job_categories(
        top_n: int = Query(20, description="返回前N个岗位类别"),
        db: Session = Depends(get_db)
):
    job_keywords = [
        "工程师", "开发", "程序员", "架构师",
        "分析师", "数据", "算法", "AI", "人工智能",
        "产品经理", "运营", "市场", "销售", "商务",
        "设计师", "UI", "UX", "视觉",
        "测试", "运维", "实施", "咨询",
        "教师", "讲师", "培训", "教育",
        "医生", "护士", "医疗", "医药",
        "会计", "财务", "审计", "金融",
        "律师", "法务", "行政", "人事", "HR",
        "管理", "总监", "主管", "经理"
    ]
    results = []
    for keyword in job_keywords:
        count = db.query(models.Job).filter(
            models.Job.job_name.like(f"%{keyword}%")
        ).count()
        if count > 0:
            avg_salary = db.query(
                func.avg((models.Job.salary_min + models.Job.salary_max) / 2)
            ).filter(
                models.Job.job_name.like(f"%{keyword}%"),
                models.Job.salary_min.isnot(None),
                models.Job.salary_max.isnot(None)
            ).scalar()
            results.append({
                "category": keyword,
                "count": count,
                "avg_salary": round(float(avg_salary), 2) if avg_salary else None
            })
    results.sort(key=lambda x: x["count"], reverse=True)
    return results[:top_n]


@app.get("/jobs/stats/by-job-name")
def get_stats_by_job_name(
        job_name: str = Query(..., description="具体的岗位名称"),
        db: Session = Depends(get_db)
):
    total = db.query(models.Job).filter(
        models.Job.job_name == job_name
    ).count()
    if total == 0:
        raise HTTPException(status_code=404, detail=f"未找到岗位: {job_name}")
    salary_stats = db.query(
        func.min(models.Job.salary_min).label("min_salary_min"),
        func.max(models.Job.salary_max).label("max_salary_max"),
        func.avg(models.Job.salary_min).label("avg_salary_min"),
        func.avg(models.Job.salary_max).label("avg_salary_max"),
        func.avg((models.Job.salary_min + models.Job.salary_max) / 2).label("avg_total_salary")
    ).filter(
        models.Job.job_name == job_name,
        models.Job.salary_min.isnot(None),
        models.Job.salary_max.isnot(None)
    ).first()
    city_distribution = db.query(
        models.Job.work_city,
        func.count(models.Job.id).label("count")
    ).filter(
        models.Job.job_name == job_name
    ).group_by(
        models.Job.work_city
    ).order_by(
        func.count(models.Job.id).desc()
    ).limit(10).all()
    education_distribution = db.query(
        models.Job.your_education,
        func.count(models.Job.id).label("count")
    ).filter(
        models.Job.job_name == job_name
    ).group_by(
        models.Job.your_education
    ).all()
    experience_distribution = db.query(
        models.Job.working_exp,
        func.count(models.Job.id).label("count")
    ).filter(
        models.Job.job_name == job_name
    ).group_by(
        models.Job.working_exp
    ).all()
    company_size_distribution = db.query(
        models.Job.company_size,
        func.count(models.Job.id).label("count")
    ).filter(
        models.Job.job_name == job_name
    ).group_by(
        models.Job.company_size
    ).all()
    return {
        "job_name": job_name,
        "total_count": total,
        "salary_statistics": {
            "min_salary_min": float(salary_stats[0]) if salary_stats[0] else None,
            "max_salary_max": float(salary_stats[1]) if salary_stats[1] else None,
            "avg_salary_min": round(float(salary_stats[2]), 2) if salary_stats[2] else None,
            "avg_salary_max": round(float(salary_stats[3]), 2) if salary_stats[3] else None,
            "avg_total_salary": round(float(salary_stats[4]), 2) if salary_stats[4] else None
        },
        "city_distribution": [
            {"city": city, "count": count} for city, count in city_distribution
        ],
        "education_distribution": [
            {"education": edu, "count": count} for edu, count in education_distribution
        ],
        "experience_distribution": [
            {"experience": exp, "count": count} for exp, count in experience_distribution
        ],
        "company_size_distribution": [
            {"company_size": size, "count": count} for size, count in company_size_distribution
        ]
    }


@app.get("/jobs/names/suggestions")
def get_job_name_suggestions(
        prefix: str = Query(..., description="岗位名称前缀"),
        limit: int = Query(10, description="返回建议数量"),
        db: Session = Depends(get_db)
):
    suggestions = db.query(
        models.Job.job_name,
        func.count(models.Job.id).label("count")
    ).filter(
        models.Job.job_name.like(f"{prefix}%")
    ).group_by(
        models.Job.job_name
    ).order_by(
        func.count(models.Job.id).desc()
    ).limit(limit).all()
    return [
        {
            "job_name": name,
            "count": count
        }
        for name, count in suggestions
    ]


@app.get("/test-db")
def test_db(db: Session = Depends(get_db)):
    try:
        count = db.query(models.Job).count()
        return {
            "status": "connected",
            "database": "SQLite",
            "total_jobs": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")


@app.get("/api/analysis/salary-boxplot")
async def get_salary_boxplot(
        major: str = Query(None),
        work_type: str = Query(None),
        group_by: str = Query("your_education"),
        job_name: str = Query(None, description="按岗位名称筛选"),
        work_city: str = Query(None, description="按工作城市筛选"),
        db: Session = Depends(get_db)
):
    from .models import Job
    query = db.query(getattr(Job, group_by).label("category"))
    if major and major != "全部":
        query = query.filter(Job.work_major == major)
    if work_type and work_type != "全部":
        query = query.filter(Job.work_type == work_type)
    if job_name and job_name != "全部":
        query = query.filter(Job.job_name == job_name)
    if work_city and work_city != "全部":
        query = query.filter(Job.work_city == work_city)
    categories = query.distinct().all()
    results = []
    for (cat,) in categories:
        if not cat:
            continue
        conditions = [f"{group_by} = :cat"]
        params = {"cat": cat}
        if major and major != "全部":
            conditions.append("work_major = :major")
            params["major"] = major
        if work_type and work_type != "全部":
            conditions.append("work_type = :work_type")
            params["work_type"] = work_type
        if job_name and job_name != "全部":
            conditions.append("job_name = :job_name")
            params["job_name"] = job_name
        if work_city and work_city != "全部":
            conditions.append("work_city = :work_city")
            params["work_city"] = work_city
        where_clause = " AND ".join(conditions)
        stats_sql = text(f"""
            SELECT 
                MIN((salary_min + salary_max) / 2.0 / 1000.0) as min,
                AVG((salary_min + salary_max) / 2.0 / 1000.0) as median,
                MAX((salary_min + salary_max) / 2.0 / 1000.0) as max,
                COUNT(*) as cnt
            FROM bigdata_recruit_job 
            WHERE {where_clause}
            AND salary_min IS NOT NULL 
            AND salary_max IS NOT NULL
        """)
        stats = db.execute(stats_sql, params).fetchone()
        if stats and stats[0] is not None:
            results.append({
                "category": cat,
                "min": round(stats[0], 1),
                "q1": round(stats[0] + (stats[1] - stats[0]) * 0.25, 1),
                "median": round(stats[1], 1),
                "q3": round(stats[1] + (stats[2] - stats[1]) * 0.25, 1),
                "max": round(stats[2], 1)
            })
    return results


@app.get("/api/analysis/job-salary-trend")
def get_job_salary_trend(
        job_name: str = Query(..., description="岗位名称"),
        group_by: str = Query("work_city",
                              description="分组维度: work_city, your_education, working_exp, company_size"),
        top_n: int = Query(10, description="返回前N个结果"),
        db: Session = Depends(get_db)
):
    results = db.query(
        getattr(models.Job, group_by).label("group_value"),
        func.count(models.Job.id).label("count"),
        func.avg(models.Job.salary_min).label("avg_min"),
        func.avg(models.Job.salary_max).label("avg_max"),
        func.avg((models.Job.salary_min + models.Job.salary_max) / 2).label("avg_total")
    ).filter(
        models.Job.job_name == job_name,
        models.Job.salary_min.isnot(None),
        models.Job.salary_max.isnot(None)
    ).group_by(
        getattr(models.Job, group_by)
    ).order_by(
        func.count(models.Job.id).desc()
    ).limit(top_n).all()
    return [
        {
            "group": group,
            "count": count,
            "avg_min_salary": round(float(avg_min), 2) if avg_min else None,
            "avg_max_salary": round(float(avg_max), 2) if avg_max else None,
            "avg_total_salary": round(float(avg_total), 2) if avg_total else None
        }
        for group, count, avg_min, avg_max, avg_total in results
    ]


@app.get("/api/persona/summary")
def job_persona_summary(
    job_name: str = Query(...),
    db: Session = Depends(get_db)
):
    total = db.query(models.Job).filter(models.Job.job_name == job_name).count()
    avg_salary = db.query(
        func.avg((models.Job.salary_min + models.Job.salary_max) / 2)
    ).filter(
        models.Job.job_name == job_name,
        models.Job.salary_min.isnot(None),
        models.Job.salary_max.isnot(None)
    ).scalar()
    def top_field(field):
        res = db.query(
            field, func.count(models.Job.id)
        ).filter(
            models.Job.job_name == job_name,
            field.isnot(None)
        ).group_by(field).order_by(func.count(models.Job.id).desc()).first()
        return res[0] if res else None
    return {
        "job_name": job_name,
        "total_jobs": total,
        "avg_salary": round(avg_salary, 2) if avg_salary else None,
        "top_city": top_field(models.Job.work_city),
        "top_education": top_field(models.Job.your_education),
        "top_experience": top_field(models.Job.working_exp),
        "top_company_size": top_field(models.Job.company_size)
    }


@app.get("/api/persona/geo-distribution")
def job_geo_distribution(
    job_name: str = Query(...),
    city: str = Query(None, description="按城市筛选"),
    district: str = Query(None, description="按区县筛选"),
    db: Session = Depends(get_db)
):
    query = db.query(
        models.Job.work_city,
        models.Job.city_district,
        models.Job.street_name,
        func.count(models.Job.id).label("count")
    ).filter(
        models.Job.job_name == job_name,
        models.Job.work_city.isnot(None)
    )
    if city:
        query = query.filter(models.Job.work_city == city)
    if district:
        query = query.filter(models.Job.city_district == district)
    location_distribution = query.group_by(
        models.Job.work_city,
        models.Job.city_district,
        models.Job.street_name
    ).order_by(
        func.count(models.Job.id).desc()
    ).limit(100).all()
    city_coordinates = {
        "北京": [39.9042, 116.4074],
        "上海": [31.2304, 121.4737],
        "广州": [23.1291, 113.2644],
        "深圳": [22.5431, 114.0579],
        "杭州": [30.2741, 120.1551],
        "南京": [32.0603, 118.7969],
        "成都": [30.5728, 104.0668],
        "武汉": [30.5928, 114.3055],
        "西安": [34.3416, 108.9398],
        "重庆": [29.4316, 106.9123],
        "天津": [39.0842, 117.2010],
        "苏州": [31.2989, 120.5853],
        "厦门": [24.4798, 118.0819],
        "长沙": [28.2278, 112.9388],
        "青岛": [36.0611, 120.3826],
        "郑州": [34.7466, 113.6253],
        "大连": [38.9140, 121.6147],
        "济南": [36.6512, 117.1201],
        "宁波": [29.8683, 121.5440],
        "东莞": [23.0478, 113.7629],
        "福州": [26.0745, 119.2965],
        "合肥": [31.8639, 117.2808],
        "昆明": [25.0389, 102.7183],
        "南宁": [22.8170, 108.3665],
        "贵阳": [26.5783, 106.7135],
        "兰州": [36.0580, 103.8235],
        "西宁": [36.6232, 101.7782],
        "银川": [38.4872, 106.2328],
        "乌鲁木齐": [43.8256, 87.6168],
        "拉萨": [29.6500, 91.1000],
        "海口": [20.0444, 110.1998],
        "太原": [37.8706, 112.5622],
        "石家庄": [38.0428, 114.5149],
        "哈尔滨": [45.7560, 126.6291],
        "长春": [43.8168, 125.3240],
        "沈阳": [41.8057, 123.4315]
    }
    geo_data = []
    city_data = []
    city_counts = {}
    for work_city, city_district, street_name, count in location_distribution:
        if work_city not in city_counts:
            city_counts[work_city] = 0
        city_counts[work_city] += count
    for city, total_count in city_counts.items():
        if city in city_coordinates:
            lat, lng = city_coordinates[city]
            import random
            lat_offset = random.uniform(-0.05, 0.05)
            lng_offset = random.uniform(-0.05, 0.05)
            city_data.append({
                "city": city,
                "count": total_count,
                "lat": lat + lat_offset,
                "lng": lng + lng_offset,
                "value": total_count,  
                "clickable": total_count >= 5 
            })
    for work_city, city_district, street_name, count in location_distribution:
        if work_city in city_coordinates:
            lat, lng = city_coordinates[work_city]
            import random
            lat_offset = random.uniform(-0.1, 0.1)
            lng_offset = random.uniform(-0.1, 0.1)
            geo_data.append({
                "city": work_city,
                "district": city_district or "未知区县",
                "street": street_name or "未知街道",
                "count": count,
                "lat": lat + lat_offset,
                "lng": lng + lng_offset,
                "value": count
            })
    return {
        "job_name": job_name,
        "city_data": city_data, 
        "geo_data": geo_data,   
        "total_cities": len(city_data),
        "filter": {
            "city": city,
            "district": district
        }
    }


@app.post("/api/resume/evaluate")
async def evaluate_resume(file: UploadFile = File(...)):
    from .resume_agents import run_evaluation_pipeline
    file_content = await file.read()
    filename = file.filename or "resume"
    return StreamingResponse(
        run_evaluation_pipeline(file_content, filename),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.post("/api/resume/evaluate-jd")
async def evaluate_resume_jd(
    file: UploadFile = File(...),
    jd_text: str = Form(...),
):
    from .resume_agents import run_jd_evaluation_pipeline
    file_content = await file.read()
    filename = file.filename or "resume"
    if not jd_text or not jd_text.strip():
        raise HTTPException(400, detail="请提供岗位描述（JD）文本")
    return StreamingResponse(
        run_jd_evaluation_pipeline(file_content, filename, jd_text.strip()),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


from pydantic import BaseModel
from typing import Optional as Opt


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class ProfileUpdateRequest(BaseModel):
    real_name: Opt[str] = None
    phone: Opt[str] = None
    gender: Opt[str] = None
    birth_year: Opt[int] = None
    location: Opt[str] = None
    school: Opt[str] = None
    major: Opt[str] = None
    degree: Opt[str] = None
    graduation_year: Opt[int] = None
    target_position: Opt[str] = None
    target_city: Opt[str] = None
    expected_salary_min: Opt[int] = None
    expected_salary_max: Opt[int] = None
    work_experience: Opt[str] = None
    tech_skills: Opt[str] = None
    about_me: Opt[str] = None


def _profile_completion(profile: UserProfile) -> int:
    fields = [
        "real_name", "phone", "gender", "birth_year", "location",
        "school", "major", "degree", "graduation_year",
        "target_position", "target_city", "expected_salary_min",
        "expected_salary_max", "work_experience", "tech_skills", "about_me"
    ]
    filled = sum(1 for f in fields if getattr(profile, f, None) not in (None, "", "[]"))
    return round(filled / len(fields) * 100)


@app.post("/api/auth/register")
def auth_register(body: RegisterRequest, db: Session = Depends(get_db)):
    if not (2 <= len(body.username) <= 50):
        raise HTTPException(status_code=400, detail="用户名长度须在 2-50 位之间")
    err = validate_password_strength(body.password)
    if err:
        raise HTTPException(status_code=400, detail=err)
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="该用户名已被注册")
    user = User(
        username=body.username,
        hashed_password=get_password_hash(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    profile = UserProfile(user_id=user.id)
    db.add(profile)
    db.commit()
    token = create_access_token({"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "username": user.username}
    }


@app.post("/api/auth/login")
def auth_login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被禁用")
    token = create_access_token({"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "username": user.username}
    }


@app.get("/api/auth/me")
def auth_me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username}


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@app.put("/api/auth/password")
def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(body.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码不正确")
    err = validate_password_strength(body.new_password)
    if err:
        raise HTTPException(status_code=400, detail=err)
    current_user.password_hash = get_password_hash(body.new_password)
    db.commit()
    return {"message": "密码修改成功"}


@app.get("/api/profile")
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    data = {c.name: getattr(profile, c.name) for c in profile.__table__.columns}
    data["completion"] = _profile_completion(profile)
    data["username"] = current_user.username
    return data


@app.put("/api/profile")
def update_profile(
    body: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
    for field, value in body.dict(exclude_unset=True).items():
        setattr(profile, field, value)
    completion = _profile_completion(profile)
    profile.is_profile_complete = completion >= 80
    db.commit()
    db.refresh(profile)
    data = {c.name: getattr(profile, c.name) for c in profile.__table__.columns}
    data["completion"] = completion
    data["username"] = current_user.username
    return data


class ResumeHistorySaveRequest(BaseModel):
    filename: Optional[str] = None
    overall_score: Optional[float] = None
    overall_rating: Optional[str] = None
    char_count: Optional[int] = None
    elapsed_seconds: Optional[float] = None
    result_json: Optional[str] = None


class MatchingHistorySaveRequest(BaseModel):
    mode: str
    filename: Optional[str] = None
    resume_preview: Optional[str] = None
    match_score: Optional[float] = None
    job_name: Optional[str] = None
    company_name: Optional[str] = None
    top_k: Optional[int] = None
    result_json: Optional[str] = None


@app.post("/api/history/resume/save")
def save_resume_history(
    body: ResumeHistorySaveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ResumeAnalysis(
        user_id=current_user.id,
        filename=body.filename,
        overall_score=body.overall_score,
        overall_rating=body.overall_rating,
        char_count=body.char_count,
        elapsed_seconds=body.elapsed_seconds,
        result_json=body.result_json,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"id": record.id, "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S")}


@app.get("/api/history/resume/{record_id}")
def get_resume_history_detail(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(ResumeAnalysis).filter(
        ResumeAnalysis.id == record_id,
        ResumeAnalysis.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return {
        "id": record.id,
        "filename": record.filename,
        "overall_score": record.overall_score,
        "overall_rating": record.overall_rating,
        "char_count": record.char_count,
        "elapsed_seconds": record.elapsed_seconds,
        "result_json": record.result_json,
        "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


@app.post("/api/history/matching/save")
def save_matching_history(
    body: MatchingHistorySaveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = MatchingHistory(
        user_id=current_user.id,
        mode=body.mode,
        filename=body.filename,
        resume_preview=body.resume_preview,
        match_score=body.match_score,
        job_name=body.job_name,
        company_name=body.company_name,
        top_k=body.top_k,
        result_json=body.result_json,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"id": record.id, "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S")}
@app.get("/api/history/resume")
def get_resume_history(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(ResumeAnalysis).filter(ResumeAnalysis.user_id == current_user.id)
    total = query.count()
    items = query.order_by(ResumeAnalysis.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return {
        "total": total,
        "page": page,
        "items": [
            {
                "id": r.id,
                "filename": r.filename,
                "overall_score": r.overall_score,
                "overall_rating": r.overall_rating,
                "char_count": r.char_count,
                "elapsed_seconds": r.elapsed_seconds,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for r in items
        ],
    }


@app.get("/api/history/matching")
def get_matching_history(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(MatchingHistory).filter(MatchingHistory.user_id == current_user.id)
    total = query.count()
    items = query.order_by(MatchingHistory.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return {
        "total": total,
        "page": page,
        "items": [
            {
                "id": r.id,
                "mode": r.mode,
                "filename": r.filename,
                "resume_preview": r.resume_preview[:100] if r.resume_preview else None,
                "match_score": r.match_score,
                "job_name": r.job_name,
                "company_name": r.company_name,
                "top_k": r.top_k,
                "result_json": r.result_json,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for r in items
        ],
    }


@app.get("/api/history/interview")
def get_interview_history(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(InterviewRecord).filter(InterviewRecord.user_id == current_user.id)
    total = query.count()
    items = query.order_by(InterviewRecord.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return {
        "total": total,
        "page": page,
        "items": [
            {
                "id": r.id,
                "session_id": r.session_id,
                "style": r.style,
                "style_name": r.style_name,
                "job_name": r.job_name,
                "turns": r.turns,
                "duration_seconds": r.duration_seconds,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for r in items
        ],
    }


@app.get("/api/history/interview/{record_id}")
def get_interview_record_detail(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(InterviewRecord).filter(
        InterviewRecord.id == record_id,
        InterviewRecord.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(404, detail="记录不存在")
    history = json.loads(record.history_json) if record.history_json else []
    return {
        "id": record.id,
        "session_id": record.session_id,
        "style": record.style,
        "style_name": record.style_name,
        "job_name": record.job_name,
        "turns": record.turns,
        "duration_seconds": record.duration_seconds,
        "history": history,
        "summary": record.summary,
        "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


@app.delete("/api/history/resume/{record_id}")
def delete_resume_history(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(ResumeAnalysis).filter(
        ResumeAnalysis.id == record_id,
        ResumeAnalysis.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(404, detail="记录不存在")
    db.delete(record)
    db.commit()
    return {"ok": True}


@app.delete("/api/history/matching/{record_id}")
def delete_matching_history(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(MatchingHistory).filter(
        MatchingHistory.id == record_id,
        MatchingHistory.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(404, detail="记录不存在")
    db.delete(record)
    db.commit()
    return {"ok": True}


@app.delete("/api/history/interview/{record_id}")
def delete_interview_history(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(InterviewRecord).filter(
        InterviewRecord.id == record_id,
        InterviewRecord.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(404, detail="记录不存在")
    db.delete(record)
    db.commit()
    return {"ok": True}


# ==================== 主题发现接口 ====================

@app.get("/api/topics")
def get_topics(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取所有主题列表, 按岗位数降序"""
    from .topic_discovery import get_all_topics
    return get_all_topics(db, page=page, page_size=page_size)


@app.get("/api/topics/emerging")
def get_emerging_topics(
    top_n: int = Query(20, ge=5, le=50),
    min_jobs: int = Query(50, ge=20, description="最低岗位数门槛"),
    min_hits: int = Query(5, ge=1, description="最低新兴技能加权命中次数"),
    db: Session = Depends(get_db),
):
    """新兴主题榜单: 按 CES 综合评分降序, 支持调门槛"""
    from .topic_discovery import compute_emerging_ranking
    return compute_emerging_ranking(db, top_n=top_n, min_jobs=min_jobs, min_emerging_hits=min_hits)


@app.get("/api/topics/{topic_id}")
def get_topic_detail(
    topic_id: int,
    db: Session = Depends(get_db),
):
    """获取主题详情: 基本信息 + 薪资/城市/学历/经验分布"""
    from .topic_discovery import get_topic_detail as _get_detail
    try:
        return _get_detail(db, topic_id)
    except ValueError as e:
        raise HTTPException(404, detail=str(e))


@app.get("/api/topics/{topic_id}/jobs")
def get_topic_jobs(
    topic_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取某主题下的岗位列表, 分页"""
    from .topic_discovery import get_topic_jobs as _get_jobs
    return _get_jobs(db, topic_id, page=page, page_size=page_size)


@app.get("/api/topics/{topic_id}/skills")
def get_topic_skills(
    topic_id: int,
    db: Session = Depends(get_db),
):
    """获取主题技能画像: 四级技能列表 + 新兴技能密度 + 独特性 + CES 评分"""
    from .topic_discovery import compute_emerging_score
    try:
        return compute_emerging_score(topic_id, db)
    except ValueError as e:
        raise HTTPException(404, detail=str(e))


@app.get("/api/jobs/emerging")
def get_emerging_jobs(
    top_n: int = Query(20, ge=5, le=50),
    min_jobs: int = Query(2, ge=1, description="岗位名组最低岗位数门槛"),
    min_emerging_score: float = Query(1.5, ge=0, description="单岗新兴分门槛(需同时命中≥2个新兴技能)"),
    merge_similar: bool = Query(True, description="是否合并同主题相似岗位名"),
    similarity_threshold: float = Query(0.8, ge=0.5, le=0.99, description="相似岗位名合并阈值"),
    db: Session = Depends(get_db),
):
    """新兴岗位榜单: 基于岗位-技能表按岗位名聚合 (依赖 job_skill_relation 表)"""
    from .topic_discovery import compute_emerging_jobs
    return compute_emerging_jobs(
        db, top_n=top_n, min_jobs=min_jobs, min_emerging_score=min_emerging_score,
        merge_similar=merge_similar, similarity_threshold=similarity_threshold,
    )


@app.get("/api/position-definitions")
def get_position_definitions(
    keyword: Optional[str] = Query(None, description="岗位名称关键词"),
    domain: Optional[str] = Query(None, description="所属领域筛选"),
    emerging_only: Optional[bool] = Query(None, description="仅新兴岗位"),
):
    """返回 position_definitions.json 中的新岗位定义数据"""
    import os as _os2
    json_path = _os2.path.join(
        _os2.path.dirname(__file__), "..", "graph_base_data", "position_definitions.json"
    )
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if keyword:
        kw = keyword.lower()
        data = [d for d in data if kw in d.get("岗位名称", "").lower()]
    if domain:
        data = [d for d in data if d.get("所属领域") == domain]
    if emerging_only is not None:
        flag = "是" if emerging_only else "否"
        data = [d for d in data if d.get("是否是新兴岗位") == flag]

    return {"total": len(data), "positions": data}


@app.get("/api/jobs/by-position-name")
def get_jobs_by_position_name(
        position_name: str = Query(..., description="职位名称（自动忽略空格差异）"),
        limit: int = Query(20, ge=1, le=50),
        db: Session = Depends(get_db),
):
    """按职位名称模糊查询岗位记录（两侧都去掉空格后匹配，解决库中'前端 开发 工程师'这类带空格数据）"""
    import re as _re
    # 去掉职位名中的所有空白、全角/半角括号后缀（如编号 A87383）再匹配
    core = _re.sub(r"[（(].*?[)）]", "", position_name)
    core = _re.sub(r"\s+", "", core)
    if not core:
        return {"total": 0, "jobs": []}

    sql = text("""
        SELECT id, job_name, company_name, job_salary, salary_min, salary_max,
               work_city, city_district, company_size, your_education, working_exp,
               company_benefits, job_summary
        FROM bigdata_recruit_job
        WHERE REPLACE(job_name, ' ', '') LIKE :kw
        ORDER BY id
        LIMIT :lim
    """)
    rows = db.execute(sql, {"kw": f"%{core}%", "lim": limit}).fetchall()

    # 统计总数（仅用于展示）
    cnt_sql = text("""
        SELECT COUNT(*) FROM bigdata_recruit_job WHERE REPLACE(job_name, ' ', '') LIKE :kw
    """)
    total = db.execute(cnt_sql, {"kw": f"%{core}%"}).scalar()

    return {
        "total": total,
        "jobs": [
            {
                "id": r.id,
                "job_name": r.job_name,
                "company_name": r.company_name,
                "job_salary": r.job_salary,
                "salary_min": r.salary_min,
                "salary_max": r.salary_max,
                "work_city": r.work_city,
                "city_district": r.city_district,
                "company_size": r.company_size,
                "your_education": r.your_education,
                "working_exp": r.working_exp,
                "company_benefits": r.company_benefits,
                "job_summary": r.job_summary,
            }
            for r in rows
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)