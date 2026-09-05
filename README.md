# path2Offer —— 智能求职辅助系统

> 一个面向应届毕业生 / 求职者的「数据驱动 + 大模型」求职平台。
> 包含**岗位图谱、新兴岗位动态、简历智能评估、人岗匹配、AI 模拟面试**五大核心模块，以及完整的**用户认证与历史记录**体系。
>
> 技术栈：**FastAPI（Python）+ Vue 3（TypeScript）+ PostgreSQL + ChromaDB + 通义千问（DashScope）**

---

## 目录

1. [系统总览](#1-系统总览)
2. [代码结构详解](#2-代码结构详解)
3. [完整启动流程（数据库 → 后端 → 前端）](#3-完整启动流程)
4. [功能模块使用说明](#4-功能模块使用说明)
5. [⚠️ 大模型 Token 耗尽的处理](#5-大模型-token-耗尽的处理)
6. [⚠️ 模拟面试麦克风 / VPN 限制说明](#6-模拟面试麦克风--vpn-限制说明)
7. [常见故障排查（FAQ）](#7-常见故障排查-faq)
8. [交接清单（接手前必读）](#8-交接清单)

---

## 1. 系统总览

| 层 | 技术 | 端口 | 入口 |
|----|------|------|------|
| 前端 | Vue 3 + Vite + TypeScript + Element Plus + ECharts | `5173` | `frontend/src/main.ts` |
| 后端 | FastAPI + Uvicorn | `8000` | `backend/app/main.py`（约 2200 行） |
| 关系数据库 | PostgreSQL 16.14（备份由 16.14 导出） | `5432` | 库名 `forjob_new`，唯一岗位主表 `bigdata_recruit_job`（54,873 条带标签岗位） |
| 向量数据库 | ChromaDB（本地嵌入式） | — | `backend/app/chroma_db/`（岗位向量 + 面试知识库） |
| 大模型 | 通义千问 `qwen-plus` / `qwen-vl-plus`（阿里云 DashScope，OpenAI 兼容协议） | — | 需在 `.env` 配置 `DASHSCOPE_API_KEY` |
| 嵌入模型 | `BAAI/bge-small-zh-v1.5`（SentenceTransformer，本地推理） | — | 首次需联网下载，之后走本地缓存 |

**整体数据流**

```
            ┌──────────────┐   HTTP / SSE   ┌─────────────────┐
浏览器 ───▶ │  Vue 前端    │ ─────────────▶ │  FastAPI 后端   │
(5173)      │  axios/fetch │ ◀───────────── │   (8000)        │
            └──────────────┘                └────────┬────────┘
                                                      │
                          ┌───────────────────────────┼───────────────────────────┐
                          ▼                            ▼                           ▼
                   PostgreSQL(岗位/用户/历史)   ChromaDB(向量检索)        DashScope(qwen 大模型)
```

---

## 2. 代码结构详解

### 2.1 后端 `backend/`

```
backend/
├── .env                      # 🔑 密钥配置（DASHSCOPE_API_KEY / AUTH_SECRET_KEY 等），不要提交到 git
├── requirements.txt          # ⚠️ 不完整！见下方「依赖补充」
├── venv/                     # Python 虚拟环境（Python 3.12）
├── app/
│   ├── main.py               # 【核心】所有 HTTP 路由（60+ 接口）、CORS、启动钩子
│   ├── database.py           # SQLAlchemy 引擎 & 连接串（PostgreSQL）
│   ├── models.py             # ORM 模型：10 张表（见下）
│   ├── auth.py               # JWT 签发/校验 + bcrypt 密码哈希（不依赖 passlib）
│   ├── resume_agents.py      # 【简历评估】多 Agent 流水线（提取→解析→评估→报告），SSE 流式
│   ├── matching.py           # 【人岗匹配】SBERT 向量 + Word2Vec 信号 + 规则打分
│   ├── interview_rag.py      # 【模拟面试】RAG 知识库 + 面试官多风格 prompt + 流式对话
│   ├── tf_wordcloud.py       # 词云 TF-IDF 计算
│   ├── city_coordinates_complete.py  # 全国城市经纬度坐标（地图热力图用）
│   ├── topic_discovery.py    # 新兴岗位发现算法
│   ├── skill_lexicon.json    # 技能词典（技能抽取/归一化用）
│   ├── chroma_db/            # ChromaDB 持久化目录（岗位向量库 + 面试知识库，本地生成不上传）
│   └── wc_precomputed/       # 各岗位大类预计算词云 JSON（加速首屏）
├── graph_base_data/          # 新兴岗位图谱数据（岗位定义、技能演变、标准岗位等 JSON）
├── scripts/                  # 数据采集 & 索引脚本
│   ├── scrape_boss.py        # BOSS 直聘爬虫
│   ├── scrape_liepin.py      # 猎聘爬虫
│   ├── import_jobs.py        # 岗位数据入库
│   ├── index_new_jobs.py     # 增量构建岗位向量索引
│   ├── build_job_skills.py   # 构建「岗位-技能」关联数据
│   ├── build_topics.py       # 构建主题/新兴岗位榜单数据
│   ├── export_graph_data.py  # 导出图谱数据 JSON
│   ├── skill_trend_analysis.py # 技能趋势分析（技能演变数据）
│   └── add_product_jobs.py
└── dataclean/                # 数据清洗（jieba 分词、行业词典、停用词）
    ├── clean_jobs.py         # 核心清洗函数（文本/行业/薪资/分词）
    ├── dict_industry.py
    ├── user_dict.txt
    ├── stopwords.txt
    └── input2/               # 清洗源数据（四大领域标注 JSON）
```

**数据库表（`models.py`，10 张）**

| 表名 | 用途 |
|------|------|
| `bigdata_recruit_job` | 唯一岗位主表（54,873 条：51,567 条 v8 标注数据 + 3,306 条筛选旧数据；label：正常/噪音/抄袭/抄袭通胀/时滞/0） |
| `job_topics` | 岗位主题（聚类结果） |
| `job_topic_relation` | 岗位-主题关联 |
| `job_skill_relation` | 岗位-技能关联（新兴岗位发现用） |
| `users` | 用户账号（用户名 + bcrypt 密码哈希） |
| `user_profiles` | 用户个人资料（求职意向等） |
| `resume_analyses` | 简历评估历史 |
| `matching_histories` | 简历-岗位匹配历史 |
| `interview_records` | 模拟面试记录 |
| `favorite_jobs` | 收藏岗位 |

**后端接口分组（共 60+，见 `main.py`）**

- 岗位检索/筛选：`/jobs`、`/api/jobs/filter`、`/api/jobs/filter-options`、`/api/jobs/by-position-name`（职位名模糊匹配，自动忽略空格/括号差异）
- 岗位图谱：`/api/persona/aggregate`、`/api/persona/wordcloud`、`/api/persona/search`、`/api/persona/categories`、`/api/persona/geo-distribution`
- 新兴岗位动态：`/api/position-definitions`
- 简历评估（SSE）：`/api/resume/evaluate`、`/api/resume/evaluate-jd`
- 人岗匹配：`/api/matching/status`、`/api/matching/auto`、`/api/matching/specific`、`/api/matching/deep-analysis`
- 模拟面试：`/api/interview/styles`、`/api/interview/session/start`、`/api/interview/session/{id}/chat`、`/finish`、知识库 `/api/interview/kb/*`
- 认证/资料：`/api/auth/register`、`/login`、`/me`、`/api/profile`
- 历史记录：`/api/history/{resume|matching|interview}/*`
- 收藏：`/api/favorites/*`

### 2.2 前端 `frontend/`

```
frontend/
├── package.json              # 依赖与脚本（dev / build / preview）
├── vite.config.ts            # Vite 配置，别名 @ → src
├── index.html
└── src/
    ├── main.ts               # 应用入口
    ├── App.vue               # 根组件，按 route.meta.layout 切换布局
    ├── router/index.ts       # 路由表 + 登录守卫（无 token 跳 /login）
    ├── layout/
    │   ├── MainLayout.vue     # 主布局（侧边栏 + 顶栏 + <slot>）
    │   └── AuthLayout.vue     # 登录/注册布局
    ├── views/                # 页面
    │   ├── JobPersona.vue        # 岗位图谱（默认首页 /persona）
    │   ├── ResumeAnalysis.vue    # 简历评估 /resume
    │   ├── JobMatching.vue       # 人岗匹配 /matching
    │   ├── InterviewSimulator.vue# 模拟面试 /interview（含语音输入）
    │   ├── PositionDefinition.vue# 新兴岗位动态 /position-def（新兴岗位定义 + 技能演变趋势图）
    │   ├── LoginView.vue / RegisterView.vue / ProfileView.vue
    ├── components/           # 复用组件
    │   ├── PanoramaGraph.vue     # 全景图谱组件
    │   ├── DomainViewGraph.vue   # 领域技能层次视图组件
    │   ├── WordCloudFlow.vue     # 岗位技能演变趋势图组件
    │   ├── resume.vue            # 简历分析三阶段 UI（上传/处理/报告）
    │   ├── EChartsCard.vue       # ECharts 通用封装
    │   ├── JobGeoHeatmap.vue     # 岗位地理热力图（leaflet）
    │   ├── SalaryDistribution.vue / SkillWordCloud.vue / PersonaFilters.vue …
    ├── api/                  # 接口封装
    │   ├── analysis.ts          # 画像/简历/词云等
    │   ├── matching.ts          # 匹配
    │   ├── position.ts          # 新兴岗位动态接口
    │   ├── auth.ts              # 认证
    │   └── history.ts           # 历史记录
```

**前端路由表**

| 路径 | 页面 | 是否需登录 |
|------|------|-----------|
| `/`、`/dashboard` | 重定向到 `/persona` | 是 |
| `/persona` | 岗位图谱 | 是 |
| `/position-def` | 新兴岗位动态 | 是 |
| `/resume` | 简历评估 | 是 |
| `/matching` | 人岗匹配 | 是 |
| `/interview` | 模拟面试 | 是 |
| `/profile` | 个人资料 | 是 |
| `/login`、`/register` | 登录 / 注册 | 否（public） |

---

## 3. 完整启动流程

> 假设全新机器。按 **数据库 → 后端 → 前端** 顺序启动。开发机为 Windows（路径 `E:\allgraduate\forjob`），命令以 Git Bash / PowerShell 为例。

### 步骤 0：环境准备

| 软件 | 版本 | 说明 |
|------|------|------|
| Python | 3.12 | 后端 |
| Node.js | 18+ | 前端 |
| PostgreSQL | **16.14**（备份由 16.14 导出，含 `\restrict` 元命令，导入需 psql 16.10+ / 17.6+） | 数据库 |
| 通义千问 API Key | — | 阿里云 DashScope 申请，所有大模型功能依赖它 |

### 步骤 1：启动 PostgreSQL 并准备数据

1. 安装并启动 PostgreSQL，确认监听 `localhost:5432`。
2. 连接串写死在 `backend/app/database.py`：
   ```python
   SQLALCHEMY_DATABASE_URL = "postgresql+psycopg://postgres:025626@localhost:5432/forjob_new"
   ```
   - 用户 `postgres` / 密码 `025626` / 库 `forjob_new`。
   - **若你的本地密码不同，改这里。**
3. **从备份恢复数据库（推荐，已提供 `backend/data/jobs_data.zip`）**

   仓库附带数据备份 **`backend/data/jobs_data.zip`**（解压得到 `jobs_data.sql`，pg_dump 导出的 plain SQL，含表结构 + 全部数据）。备份本身**不含** `CREATE DATABASE`，所以要先建库再导入：

   ```bash
   # ① 先创建空库（连到默认 postgres 库执行）
   psql -U postgres -h localhost -c "CREATE DATABASE forjob_new;"

   # ② 导入前设置编码，避免中文乱码
   set PGCLIENTENCODING=UTF8

   # ③ 解压备份并导入（解压后把 jobs_data.sql 放到当前目录，或写绝对路径）
   psql -U postgres -h localhost -d forjob_new -f jobs_data.sql
   ```

   - 会提示输入 `postgres` 用户密码（默认 `025626`）。
   - 导入后岗位主表为 `bigdata_recruit_job`（唯一岗位表，共 **54,873** 条：51,567 条 v8 标注数据 + 3,306 条筛选旧数据，label 取值见上文表说明）。
   - 备份含 `\restrict` 元命令，**导入需 psql 16.10+ / 17.6+**（新版 PostgreSQL 安装包均满足；旧版 psql 会打印 `invalid command \restrict` 警告，数据通常仍可导入）。
   - 若库中已有旧数据，先 `DROP DATABASE forjob_new;` 重建空库再导入，避免主键冲突。
   - 验证：`psql -U postgres -d forjob_new -c "SELECT count(*) FROM bigdata_recruit_job;"` 应返回 `54873`。

### 步骤 2：配置后端密钥 `backend/.env`

```ini
# 通义千问（DashScope）—— 简历评估 / 模拟面试 / 人岗匹配深度分析全靠它
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx

# JWT 签名密钥（任意长随机串）
AUTH_SECRET_KEY=改成你自己的随机串

# 兼容字段（可留空，代码会优先用 DASHSCOPE_API_KEY）
OPENAI_API_KEY=
OPENAI_API_BASE=

# 禁用 ChromaDB 遥测，避免国内网络超时（务必保留）
ANONYMIZED_TELEMETRY=False
CHROMA_TELEMETRY=False
```

### 步骤 3：启动后端

```bash
cd E:/allgraduate/forjob/backend
source venv/Scripts/activate          # PowerShell 用 venv\Scripts\Activate.ps1

# 首次：安装依赖（requirements.txt 不完整，补全见下）
pip install -r requirements.txt
pip install sentence-transformers chromadb gensim jieba sentencepiece pdfplumber python-docx

# 启动（注意：不要加 --reload，长查询会被打断）
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

> **⚠️ 依赖补充**：`requirements.txt` 缺少向量检索相关包。实际 venv 中已装的关键包：
> `sentence-transformers==5.2.3`、`chromadb==1.5.2`、`gensim==4.4.0`、`jieba==0.42.1`、`langchain==0.3.27`、`langchain-openai==0.3.35`。
> 接手后建议执行 `pip freeze > requirements.txt` 固化完整依赖。

**首次启动注意：**
- 嵌入模型 `BAAI/bge-small-zh-v1.5` 会联网下载（已设镜像 `HF_ENDPOINT=https://hf-mirror.com`），下载后走本地缓存。
- 人岗匹配的岗位向量库若未构建，调用 `/api/matching/auto` 会返回 503「向量库构建中，首次约需 15 分钟」。先访问 `GET /api/matching/status` 看进度，或运行 `scripts/index_new_jobs.py` 预先构建。

**关闭后端：**
```bash
# Windows：先查 PID 再杀
netstat -ano | findstr :8000
taskkill //F //PID <pid>
```

### 步骤 4：启动前端

```bash
cd E:/allgraduate/forjob/frontend
npm install        # 首次
npm run dev        # → http://localhost:5173
```

打开浏览器访问 **http://localhost:5173**，先注册账号再使用。

> 前端 API 基址：检查 `src/api/*.ts` 中的 baseURL，确保指向 `http://localhost:8000`；后端 CORS 已放行 `5173`。

### 一键启动小抄

```bash
# 终端 1 - 后端
cd E:/allgraduate/forjob/backend && source venv/Scripts/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000

# 终端 2 - 前端
cd E:/allgraduate/forjob/frontend && npm run dev
```

---

## 4. 功能模块使用说明

### 4.1 岗位图谱 `/persona`（默认首页）

- **用途**：对 5.5 万岗位做聚合分析——薪资分布、城市/地理热力、学历经验要求、技能词云、岗位大类（人工智能/智能系统/物联网/大数据）。
- **三种视图**：
  - **全景图谱**（「全部」下默认视图）：岗位-技能知识图谱全景；
  - **领域技能层次视图**（选中四个领域时的默认视图）：按领域展示岗位-技能层次结构；
  - **领域画像 / 综合画像**：聚合图表（行业分布、薪资箱线图、地理热力、学历环图、技能词云）。
- **视图切换逻辑**：点「全部」→ 全景图谱；点四个领域 → 领域技能层次视图；可再手动切回画像视图。
- **使用**：进入页面自动加载。先出 `aggregate`（核心图表，<1s，缓存 10 分钟），词云 `wordcloud` 异步后加载（较慢，单独缓存）。可按分类/关键词筛选，懒加载岗位详情。
- **性能要点**：**词云接口与 aggregate 接口分离，切勿合并**（合并会拖慢首屏）。各大类词云已预计算在 `wc_precomputed/`。

### 4.2 新兴岗位动态 `/position-def`

- **用途**：基于多源异构数据驱动的新兴岗位图谱 · 定义 · 演化分析。
- **两个子视图**（页面顶部切换）：
  - **新兴岗位定义**：展示 128 个岗位定义（含 55 个新兴岗位），每个岗位含核心职责、必备技能、加分技能、典型应用场景、新兴程度、新兴度判定信号（岗位新兴技能占比、新兴职位占比、招聘次数环比增幅、命名新颖性）。
  - **岗位技能演变趋势图**：按岗位查看技能的出现、消失与趋势变化（4 季度时序），统计上升/下降/平稳/单点技能数。
- **岗位联动**：点击新兴岗位名称 → 弹窗展示岗位概要与**所含职位**；点击职位可展开该职位在库中的招聘详情（公司/薪资/城市/学历/经验/福利/岗位描述）；弹窗内「查看技能演变趋势」按钮可跳转到趋势图并自动选中该岗位。
- **使用**：可按岗位名称搜索、按所属领域/新兴岗位筛选，支持热门岗位快捷检索与一键重置。
- **数据来源**：`backend/graph_base_data/position_definitions.json`、`frontend/public/position_skill_evolution_fixed.json`。

### 4.3 简历评估 `/resume`

- **用途**：上传简历（PDF/Word/图片），多 Agent 流水线打分并生成改进报告。
- **流程（SSE 流式，5 步）**：`extract`（提取）→ `parse`（解析）→ `evaluate`（评估）→ `report`（报告）→ `done`，整体约 15–20s。
  - Agent-1 提取：`qwen-plus`，temperature 0.05
  - Agent-2 评估：`qwen-plus`，temperature 0.2
  - 图片简历走 `qwen-vl-plus` 视觉模型识别。
- **可带 JD 评估**：`/api/resume/evaluate-jd` 针对具体岗位 JD 给匹配性评估。
- **技术细节**：前端用 `fetch` + `ReadableStream` 消费 SSE（**不是** EventSource）。
- **依赖**：必须配置 `DASHSCOPE_API_KEY`。

### 4.4 人岗匹配 `/matching`

- **用途**：上传简历 → 自动推荐 Top-K 匹配岗位，或与指定岗位逐项打分。
- **打分机制**（`matching.py`）：SBERT 语义向量（bge-small-zh）+ Word2Vec 信号（可选）+ 规则分（学历/经验/薪资）。Word2Vec 模型路径由环境变量 `W2V_MODEL_PATH` 指定，未配置则自动降级为纯 SBERT。
- **前置条件**：岗位向量库需先构建完成。`GET /api/matching/status` 返回 `ready` 才能用；未就绪时 `auto` 接口返回 503。首次构建约 15 分钟。
- **深度分析** `/api/matching/deep-analysis`：调用 qwen 大模型生成自然语言匹配解读（消耗 Token）。

### 4.5 模拟面试 `/interview`

- **用途**：选择面试风格（技术/行为/综合等）→ 上传简历+JD → AI 面试官多轮流式对话 → 结束生成评估。
- **多风格**：`interview_rag.py` 中 `STYLE_CONFIG` 定义各类面试官 system prompt（如「技术面试」模拟 BAT/字节级资深面试官）。
- **RAG 知识库**：可上传资料到面试知识库（`/api/interview/kb/ingest`），检索增强面试问题。向量存于 ChromaDB。
- **对话**：`/api/interview/session/start` 建会话 → `/chat` 流式回答（qwen-plus）→ `/finish` 收尾评估 → `/history` 查记录。
- **语音输入**：回答框旁有麦克风按钮，支持语音转文字。**⚠️ 有 VPN 限制，见第 6 节。**

### 4.6 用户体系

- 注册/登录（JWT + bcrypt），路由守卫：未登录访问受保护页跳 `/login`；已登录访问 `/login`/`/register` 跳首页。
- 登录态存 localStorage，由 `composables/useAuth.ts` 管理。
- 个人资料 `/profile`，各模块历史记录可在对应页面查看/删除。

---

## 5. 大模型 Token 耗尽的处理

> 所有大模型功能（简历评估、模拟面试、匹配深度分析、图片简历识别）都走 **阿里云 DashScope 的 qwen-plus / qwen-vl-plus**，统一用 `backend/.env` 里的 `DASHSCOPE_API_KEY`。Token / 额度耗尽时，这些功能会报错，但**岗位图谱、岗位检索、人岗匹配的向量打分部分不受影响**（它们不调大模型）。

### 5.1 如何判断是 Token 耗尽

后端日志或前端会出现类似报错（`resume_agents.py` 已做友好映射）：
- `API Key 无效或已过期，请检查 DASHSCOPE_API_KEY` → key 失效或欠费
- HTTP `401 / 403` → 鉴权失败
- HTTP `429` → 限流 / 额度用尽
- `网络连接失败` → 网络问题（非 Token）

可直接用 curl 验证 key 是否还有额度：
```bash
curl https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions \
  -H "Authorization: Bearer $DASHSCOPE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen-plus","messages":[{"role":"user","content":"hi"}]}'
```

### 5.2 处理办法（按优先级）

1. **换一个有额度的 Key（最快）**
   - 登录 [阿里云百炼 / DashScope 控制台](https://dashscope.console.aliyun.com/) → 充值 / 开通新模型额度，或新建一个 API Key。
   - 修改 `backend/.env` 的 `DASHSCOPE_API_KEY=新key`。
   - **重启后端**（无 `--reload`，必须手动重启才会重新读取 `.env`）。

2. **检查账户欠费 / 实名 / 模型开通**
   - DashScope 需实名认证，且 `qwen-plus`、`qwen-vl-plus` 需在控制台「模型广场」分别开通。

3. **切换更便宜的模型降本**
   - 代码里模型名写死为 `qwen-plus`（在 `resume_agents.py`、`interview_rag.py` 多处）。
   - 可统一改为更便宜的 `qwen-turbo`，或在 `_get_llm()` 集中改一处。搜索关键字 `qwen-plus` 全局替换前请评估效果差异。

4. **改用其他 OpenAI 兼容厂商（无需改架构）**
   - 因为底层用的是 `langchain_openai.ChatOpenAI` + `base_url`，理论上可切到任意 OpenAI 兼容服务（如 DeepSeek、Moonshot、本地 Ollama）。
   - 需改两处：`base_url`（现为 `https://dashscope.aliyuncs.com/compatible-mode/v1`）+ `model` 名 + 对应 key。建议把 `base_url` 也抽到 `.env`，避免散落硬编码。

5. **临时降级 / 容错**
   - 大模型不可用时，前端应给出「AI 服务暂不可用，请稍后再试」提示，而非白屏。人岗匹配可只用向量打分、隐藏「深度分析」按钮，保证基础功能可用。

### 5.3 省 Token 建议（长期）

- 简历评估已限制重试次数（评估 Agent 失败时降温重试，见 `resume_agents.py` 中 `attempt` 逻辑），避免无限重试烧额度。
- 面试官回复 prompt 已限制「120 字以内」，控制输出长度。
- 画像/词云等高频读接口走内存缓存（`_AGG_CACHE` / `_WC_CACHE`，10 分钟），不要让前端反复触发。

---

## 6. 模拟面试麦克风 / VPN 限制说明

### 6.1 现象

模拟面试页 `/interview` 的「语音输入」按钮，在**国内网络环境下经常无法识别、报错或一直没反应**，但同样的代码在能科学上网的环境下正常。

### 6.2 根因

语音输入用的是浏览器原生 **Web Speech API**（`InterviewSimulator.vue` 中 `webkitSpeechRecognition`，`lang='zh-CN'`）：

```js
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
recognition = new SpeechRecognition()
recognition.lang = 'zh-CN'
recognition.continuous = true
recognition.interimResults = true
```

**Chrome / Edge 的 Web Speech API 把音频上传到 Google 的语音识别服务器**进行识别。Google 服务在中国大陆被墙，因此：
- **必须能访问 Google（即需要 VPN / 科学上网）** 才能正常识别。
- 无 VPN 时通常表现为：点了麦克风没反应、`onerror` 报 `network` 或 `not-allowed`、一直转圈不出文字。
- **Firefox 默认不支持**该 API（代码已提示「请使用 Chrome 或 Edge」）。

此外还需满足：
- 页面必须是 **HTTPS 或 localhost**（`http://` 非本机会被浏览器拒绝授权麦克风）。
- 用户需在浏览器**允许麦克风权限**。

### 6.3 给用户/运维的应对

| 场景 | 建议 |
|------|------|
| 开发/演示能科学上网 | 开 VPN，用 Chrome / Edge，本地 `localhost` 或 HTTPS 访问，允许麦克风权限 即可正常语音作答。 |
| 无 VPN / 内网部署 | **直接用键盘输入回答**——文本框始终可用，语音只是可选增强，不影响面试流程。 |
| 浏览器不支持 | 页面已提示换 Chrome / Edge。 |

### 6.4 彻底去掉 VPN 依赖的改造方向（可选，需后续开发）

Web Speech API 依赖 Google 是硬伤。若要在国内稳定语音输入，应改为**国产 ASR 服务**：

1. **后端代理 + 国产语音识别**（推荐）
   - 前端用 `MediaRecorder` 录音 → 上传后端 → 后端转发到**阿里云智能语音 / 科大讯飞 / 百度语音** ASR → 返回文字。
   - 好处：与现有 DashScope 同生态（可用阿里云语音），无需 VPN，可控可计费。
2. 接入科大讯飞 Web SDK（WebSocket 实时转写），同样无需翻墙。
3. 项目里已有 `/api/test/coze-upload`、`/api/test/coze-chat` 的实验性接口（Coze 相关），可作为第三方语音/对话集成的参考起点。

> 当前版本未做上述改造，**交接时请明确告知用户：语音作答需 VPN + Chrome/Edge，否则请打字。**

---

## 7. 常见故障排查（FAQ）

| 现象 | 可能原因 | 处理 |
|------|----------|------|
| 后端起不来，报数据库连接失败 | PostgreSQL 没启 / 密码不对 | 启动 PG；核对 `database.py` 连接串密码 |
| `pip install` 后仍缺包 | `requirements.txt` 不完整 | 补装 `sentence-transformers chromadb gensim jieba` 等 |
| 简历评估/面试报「API Key 无效」 | Token 耗尽 / key 失效 | 见 [第 5 节](#5-大模型-token-耗尽的处理)，换 key 后**重启后端** |
| `/api/matching/auto` 返回 503 | 岗位向量库未构建完 | 等待或跑 `scripts/index_new_jobs.py`，查 `/api/matching/status` |
| 首次启动卡在下载模型 | 在下 bge 嵌入模型 | 已配 hf-mirror 镜像，耐心等；或离线放好本地缓存 |
| 语音输入没反应 | 无 VPN / 非 Chrome / 非 HTTPS | 见 [第 6 节](#6-模拟面试麦克风--vpn-限制说明) |
| 前端请求跨域失败 | API baseURL 配错 / 后端没起 | 确认指向 `http://localhost:8000`，后端 CORS 已放行 5173 |
| 改了 `.env` 不生效 | 后端没重启 | 启动时**未加 `--reload`**，必须手动重启 |
| ChromaDB 遥测超时 | 国内网络 | 确认 `.env` 里 `ANONYMIZED_TELEMETRY=False` |

---

## 8. 交接清单

接手后建议尽快处理以下「技术债」，让系统更易维护：

- [ ] **固化依赖**：`pip freeze > backend/requirements.txt`（当前文件缺向量检索相关包）。
- [ ] **密钥外置**：`database.py` 的连接串密码、`resume_agents.py`/`interview_rag.py` 的 `base_url` 目前**硬编码**，建议统一读 `.env`。
- [ ] **更换 `AUTH_SECRET_KEY`**：交接后改成新的随机串，旧 token 失效。
- [x] **数据库备份**：已提供 `backend/data/jobs_data.zip`（解压得 `jobs_data.sql`，pg_dump 单表 `bigdata_recruit_job` 全量 54,873 条带标签数据）。导入方式见 [步骤 1](#步骤-1启动-postgresql-并准备数据)。这是核心资产，请妥善保存；后续如更新数据，用 `pg_dump -U postgres -d forjob_new -t public.bigdata_recruit_job -f jobs_data.sql` 重新导出，压缩为 zip 后替换该文件（明文约 187MB 超 Gitee 单文件 100MB 限制，必须压缩提交）。
- [ ] **确认 DashScope Key 额度**：登录控制台看余额，必要时换自己的 key（见第 5 节）。
- [ ] **语音功能现状**：明确告知使用方「语音作答需 VPN + Chrome/Edge」，长期可改国产 ASR（见 6.4）。
- [x] **清理弃用文件**：一次性脚本、调试脚本、旧学科数据（278 个文件）已于 2026-09 清理；`SalaryDistribution.vue` / `PersonaFilters.vue` 为无引用的遗留组件，可后续删除。

### 关键文件速查

| 想改什么 | 去哪 |
|----------|------|
| 数据库连接 | `backend/app/database.py` |
| 所有接口路由 | `backend/app/main.py` |
| 简历评估逻辑 / 模型 | `backend/app/resume_agents.py` |
| 面试官 prompt / 风格 | `backend/app/interview_rag.py`（`STYLE_CONFIG`） |
| 匹配打分算法 | `backend/app/matching.py` |
| 密钥 | `backend/.env` |
| 前端路由 | `frontend/src/router/index.ts` |
| 语音输入逻辑 | `frontend/src/views/InterviewSimulator.vue`（`startVoice`） |
| 接口地址封装 | `frontend/src/api/*.ts` |

---

_最后更新：2026-09。如有疑问，从 `backend/app/main.py` 的路由入手，配合本文 [第 2 节](#2-代码结构详解) 的结构图定位代码。_
