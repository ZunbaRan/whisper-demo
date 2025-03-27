from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from httpx import AsyncClient
import uvicorn

app = FastAPI(title="API Gateway")

# 挂载静态文件
app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")

# 设置模板
templates = Jinja2Templates(directory="../frontend/templates")

# 添加配置变量
WHISPER_SERVICE_URL = "http://localhost:8001"  # whisper-core 服务地址

# 前端路由
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/transcribe")
async def transcribe_page(request: Request):
    return templates.TemplateResponse("transcribe.html", {"request": request})

# API 代理路由
@app.get("/api/whisper/{path:path}")
async def whisper_proxy(path: str):
    async with AsyncClient() as client:
        response = await client.get(f"{WHISPER_SERVICE_URL}/{path}")
        return response.json()

@app.post("/api/whisper/{path:path}")
async def whisper_proxy_post(path: str, request: Request):
    body = await request.json()
    async with AsyncClient() as client:
        response = await client.post(
            f"{WHISPER_SERVICE_URL}/{path}",
            json=body
        )
        return response.json()

# 添加 Deep Research 代理路由
@app.get("/api/deep-research/{path:path}")
async def deep_research_proxy(path: str):
    async with AsyncClient() as client:
        response = await client.get(f"http://deep-research:8000/{path}")
        return response.json()

@app.post("/api/deep-research/{path:path}")
async def deep_research_proxy_post(path: str, request: Request):
    body = await request.json()
    async with AsyncClient() as client:
        response = await client.post(
            f"http://deep-research:8000/{path}",
            json=body
        )
        return response.json()

def start_app():
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    start_app() 