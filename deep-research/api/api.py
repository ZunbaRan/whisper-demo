from fastapi import FastAPI, Request, HTTPException, APIRouter, Body
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Dict, List, Any
import logging
import os

from deep_research.deep_research import DeepResearch, ExtraConfig
from deep_research.search_engine.tavily import TavilySearchEngine
from deep_research.search_engine.volc_bot import VolcBotSearchEngine
from deep_research.utils import get_last_message

from pydantic import BaseModel

class DeepResearchRequest(BaseModel):
    messages: List[Dict[str, str]]
    stream: bool = False
    max_search_words: int = 5
    max_planning_rounds: int = 5

class DeepResearchResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

app = FastAPI(title="Deep Research API")

# 配置模板和静态文件
templates = Jinja2Templates(directory="../frontend/templates")
app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")

@app.on_event("startup")
async def startup_event():
    # 设置 Deep Research 默认环境变量（如果未设置）
    if not os.getenv("REASONING_MODEL"):
        os.environ["REASONING_MODEL"] = "deepseek-r1-250120"
    
    if not os.getenv("SEARCH_ENGINE"):
        os.environ["SEARCH_ENGINE"] = "volc_bot"
    
    # 确保搜索引擎相关配置已设置
    if os.getenv("SEARCH_ENGINE") == "volc_bot" and not os.getenv("SEARCH_BOT_ID"):
        print("警告: 使用 volc_bot 搜索引擎但未设置 SEARCH_BOT_ID 环境变量")
    
    if os.getenv("SEARCH_ENGINE") == "tavily" and not os.getenv("TAVILY_API_KEY"):
        print("警告: 使用 tavily 搜索引擎但未设置 TAVILY_API_KEY 环境变量")

@app.get("/status")
def deep_research_status():
    return {"status": "Deep Research 功能正常"}

@app.post("/analyze")
async def analyze_query(request_data: Dict[str, Any] = Body(...)):
    """深度分析请求处理"""
    try:
        # 初始化搜索引擎和深度研究模块
        search_engine = TavilySearchEngine(api_key=os.environ.get("TAVILY_API_KEY", ""))
        deep_research = DeepResearch(search_engine=search_engine)
        
        # 处理请求
        messages = request_data.get("messages", [])
        question = next((msg["content"] for msg in messages if msg["role"] == "user"), "")
        
        result = await deep_research.chat(messages=messages)
        return result
    except Exception as e:
        logging.error(f"深度分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"深度分析失败: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def deep_research_home(request: Request):
    """Deep Research 首页"""
    return templates.TemplateResponse("deep_research.html", {"request": request})

def start_app():
    import uvicorn
    uvicorn.run("api.api:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    start_app() 