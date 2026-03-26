# AI Resume Analyzer

一个可本地运行、可部署、可公开验收的智能简历分析系统。  
系统支持上传 PDF 简历、解析多页文本、结构化提取关键信息，并结合岗位描述输出可解释的匹配评分。

---

## 1. 项目简介

本项目面向笔试提交、作品集演示、线上验收场景，重点是：

- 后端：`FastAPI` 提供 RESTful API
- 前端：`Vue3 + Vite`，可直接部署到 GitHub Pages
- AI：支持 OpenAI 兼容接口，未配置时自动 fallback
- 缓存：优先 Redis，未配置时自动退化为内存缓存
- 部署：保留阿里云函数计算 FC（custom-container）能力

---

## 2. 技术选型说明

- **后端框架**：`FastAPI`（开发效率高，接口文档自动化）
- **PDF 解析**：`pdfplumber`（稳定，支持多页文本提取）
- **HTTP 客户端**：`httpx`（调用 OpenAI 兼容 LLM 接口）
- **缓存**：`redis`（可选）+ 进程内内存缓存（默认可用）
- **前端**：`Vue3` + `Vite` + `Axios`
- **部署**：GitHub Actions + GitHub Pages；阿里云 FC `s.yaml`

---

## 3. 项目结构说明

```text
/
  README.md
  .gitignore
  .env.example
  backend/
    app/
      __init__.py
      main.py
      config.py
      schemas.py
      utils/
        __init__.py
        pdf_parser.py
        text_cleaner.py
        hash_util.py
      services/
        __init__.py
        extractor.py
        matcher.py
        cache_service.py
        llm_client.py
      api/
        __init__.py
        routes.py
    tests/
      test_health.py
    requirements.txt
    Dockerfile
    s.yaml
    run_local.md
  frontend/
    package.json
    vite.config.ts
    index.html
    src/
      main.ts
      App.vue
      api/
        client.ts
        resume.ts
      components/
        ResultPanel.vue
        StatusAlert.vue
    .env.example
    README.md
  .github/
    workflows/
      deploy-pages.yml
```

---

## 4. 本地启动步骤

### 4.1 启动后端

```bash
cd backend
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

后端接口地址：`http://localhost:8000`

### 4.2 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端访问地址：`http://localhost:5173`

---

## 5. 环境变量说明

可从根目录 `.env.example` 复制：

### 后端变量

- `APP_NAME`：服务名
- `APP_ENV`：运行环境（`dev/prod`）
- `APP_HOST` / `APP_PORT`：监听地址与端口
- `CORS_ORIGINS`：前端域名白名单，多个用逗号分隔
- `LLM_BASE_URL`：OpenAI 兼容接口地址（如 `https://api.openai.com/v1`）
- `LLM_API_KEY`：模型密钥
- `LLM_MODEL`：模型名
- `REDIS_URL`：Redis 连接串（可选）
- `CACHE_TTL_SECONDS`：缓存过期秒数

### 前端变量

- `VITE_API_BASE_URL`：后端 API 基础地址（如 `http://localhost:8000`）
- `VITE_BASE_PATH`：前端构建子路径（GitHub Pages 常用）

---

## 6. API 文档说明

启动后可访问 FastAPI 自动文档：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 6.1 `GET /health`

健康检查。

### 6.2 `POST /api/resumes/parse`

- 请求：`form-data` 上传单个 `file`（PDF）
- 返回：
  - `raw_text`
  - `clean_text`
  - `parsed_info`
  - `resume_id`
  - `from_cache`

### 6.3 `POST /api/resumes/match`

- 请求 JSON：
  - `resume_id`
  - `job_description`
- 返回：
  - `job_keywords`
  - `matched_keywords`
  - `missing_keywords`
  - `dimension_scores`
  - `match_score`
  - `ai_summary`
  - `from_cache`

---

## 7. 前端部署到 GitHub Pages 的步骤

仓库已内置工作流：`.github/workflows/deploy-pages.yml`。

### 7.1 GitHub 仓库设置

1. 在仓库 `Settings -> Pages` 中启用 `GitHub Actions` 作为来源  
2. 在仓库 `Settings -> Secrets and variables -> Actions -> Variables` 新增：
   - `VITE_API_BASE_URL`：你的线上后端地址（例如 FC 网关地址）

### 7.2 触发部署

- 推送 `main` 或 `master` 分支的 `frontend/` 变更，自动构建并部署
- 工作流会自动把 `VITE_BASE_PATH` 设置为 `/${仓库名}/`

---

## 8. 后端部署到阿里云 FC 的步骤

后端目录已提供 `backend/s.yaml`（`custom-container` 方案）。

### 8.1 构建并推送镜像

```bash
cd backend
docker build -t ai-resume-analyzer:latest .
# 替换为你自己的镜像仓库地址
docker tag ai-resume-analyzer:latest registry.cn-hangzhou.aliyuncs.com/your-namespace/ai-resume-analyzer:latest
docker push registry.cn-hangzhou.aliyuncs.com/your-namespace/ai-resume-analyzer:latest
```

### 8.2 修改 `s.yaml`

将 `customContainerConfig.image` 改为你的镜像地址。

### 8.3 部署

```bash
cd backend
s deploy
```

部署成功后，绑定 HTTP 触发器或网关域名，即可作为前端 API 地址。

---

## 9. 缓存设计说明

- **解析缓存键**：`resume:parse:{file_hash}`
- **匹配缓存键**：`resume:match:{resume_id}:{jd_hash}`
- **优先 Redis**：读取 `REDIS_URL` 后启用
- **自动降级**：无 Redis 时使用进程内内存缓存
- **接口标识**：响应中统一返回 `from_cache` 字段
- **简历存储**：`resume_id -> {raw_text, clean_text, parsed_info}` 在服务内存中维护，后续可替换为数据库

---

## 10. AI 提取与匹配设计说明

### 10.1 简历信息提取

提取字段固定为：

- `name`
- `phone`
- `email`
- `address`
- `job_intention`
- `expected_salary`
- `work_years`
- `education`
- `projects`（数组）

工作模式：

1. **LLM 模式（`extraction_mode = "llm"`）**  
   配置 `LLM_BASE_URL + LLM_API_KEY + LLM_MODEL` 后启用，强约束 JSON 输出。
2. **Fallback 模式（`extraction_mode = "fallback"`）**  
   使用正则+规则提取基础信息，保证无 LLM 也可返回稳定结构化结果。

### 10.2 岗位匹配评分

采用“规则评分 + AI 总结”混合方案：

- 维度：
  - `skill_match`（技能匹配，50%）
  - `experience_relevance`（经验相关，30%）
  - `education_match`（学历匹配，20%）
- 产出：
  - `job_keywords`
  - `matched_keywords`
  - `missing_keywords`
  - `match_score`（0-100）
  - `ai_summary`

如果开启 LLM，可对规则分进行 `-5~+5` 轻量校准并生成更细致总结；未开启时仍返回可用结果。

---

## 11. 已知限制

- 当前未接入 OCR，扫描件 PDF（图片型）可能提取文本不足
- 未接入数据库，`resume_id` 存储依赖进程内内存（重启后丢失）
- 关键词抽取为轻量规则算法，复杂语义匹配能力有限
- LLM 调用依赖外部网络和第三方服务稳定性

---

## 12. 后续优化方向

- 增加 OCR 管道（如 PaddleOCR/Tesseract）提升扫描件可用性
- 将简历与匹配结果持久化到 PostgreSQL/MySQL
- 引入向量检索与语义相似度评分
- 增加批量简历比对、岗位多版本 A/B 分析
- 增加鉴权、多租户、审计日志、限流

---

## API 请求与响应样例

### A. 解析接口样例

请求（curl）：

```bash
curl -X POST "http://localhost:8000/api/resumes/parse" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@./sample_resume.pdf"
```

响应示例：

```json
{
  "resume_id": "7f3b4f2f-f5d2-46ee-93c2-a57f4d8e8f53",
  "raw_text": "......",
  "clean_text": "......",
  "parsed_info": {
    "extraction_mode": "fallback",
    "name": "张三",
    "phone": "13800138000",
    "email": "zhangsan@example.com",
    "address": "上海",
    "job_intention": "后端开发工程师",
    "expected_salary": "20k-30k",
    "work_years": "3年工作经验",
    "education": "本科",
    "projects": [
      {
        "name": "智能简历分析系统",
        "description": ""
      }
    ]
  },
  "from_cache": false
}
```

### B. 匹配接口样例

请求（curl）：

```bash
curl -X POST "http://localhost:8000/api/resumes/match" \
  -H "Content-Type: application/json" \
  -d "{\"resume_id\":\"7f3b4f2f-f5d2-46ee-93c2-a57f4d8e8f53\",\"job_description\":\"需要3年以上Python经验，熟悉FastAPI、Redis、Docker，本科及以上\"}"
```

响应示例：

```json
{
  "resume_id": "7f3b4f2f-f5d2-46ee-93c2-a57f4d8e8f53",
  "job_keywords": ["python", "fastapi", "redis", "docker", "本科"],
  "matched_keywords": ["python", "fastapi", "redis"],
  "missing_keywords": ["docker", "本科"],
  "dimension_scores": {
    "skill_match": 60.0,
    "experience_relevance": 100.0,
    "education_match": 100.0
  },
  "match_score": 78.0,
  "ai_summary": "候选人核心技术匹配较好，建议补充容器化经验。",
  "from_cache": false
}
```

