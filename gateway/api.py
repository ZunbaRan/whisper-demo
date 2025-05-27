from fastapi import FastAPI
from httpx import AsyncClient
import uvicorn

app = FastAPI(title="API Gateway")

@app.get("/")
async def root():
    return {"message": "API Gateway is running"}

@app.get("/whisper/{path:path}")
async def whisper_proxy(path: str):
    async with AsyncClient() as client:
        response = await client.get(f"http://whisper:8000/{path}")
        return response.json()

@app.get("/deep-research/{path:path}")
async def deep_research_proxy(path: str):
    async with AsyncClient() as client:
        response = await client.get(f"http://deep-research:8000/{path}")
        return response.json()

@app.get("/web-crawl/{path:path}")
async def web_crawl_proxy(path: str):
    async with AsyncClient() as client:
        response = await client.get(f"http://web-crawl:8000/{path}")
        return response.json()

def start_app():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start_app()
