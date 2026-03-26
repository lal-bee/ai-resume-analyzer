# 后端本地运行

## 1. 安装依赖

```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate
pip install -r requirements.txt
```

## 2. 配置环境变量

复制项目根目录的 `.env.example` 为 `.env`，最少配置：

- `CORS_ORIGINS=http://localhost:5173`

如需增强能力再配置：

- `REDIS_URL`
- `LLM_BASE_URL`
- `LLM_API_KEY`
- `LLM_MODEL`

## 3. 启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 4. 测试健康检查

访问 `http://localhost:8000/health`，应返回：

```json
{"status":"ok"}
```
