from fastapi import APIRouter, Request, HTTPException, Body
from fastapi.responses import JSONResponse, HTMLResponse
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

def register_deep_research_routes(app):
    router = APIRouter(prefix="/deep-research", tags=["deep-research"])
    
    @router.get("/status")
    def deep_research_status():
        return {"status": "Deep Research 功能正常"}
    
    @router.post("/analyze")
    async def analyze_query(request_data: Dict[str, Any] = Body(...)):
        """深度分析请求处理"""
        try:
            # 导入深度研究核心功能
            from deep_research.deep_research import DeepResearch
            from deep_research.search_engine.tavily import TavilySearchEngine
            
            # 初始化搜索引擎和深度研究模块
            import os
            search_engine = TavilySearchEngine(api_key=os.environ.get("TAVILY_API_KEY", ""))
            deep_research = DeepResearch(search_engine=search_engine)
            
            # 处理请求
            messages = request_data.get("messages", [])
            question = next((msg["content"] for msg in messages if msg["role"] == "user"), "")
            
            result = await deep_research.chat(messages=messages)
            return result
        except Exception as e:
            logger.error(f"深度分析失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"深度分析失败: {str(e)}")
    
    @router.get("/", response_class=HTMLResponse)
    async def deep_research_home(request: Request):
        """Deep Research 首页"""
        return app.templates.TemplateResponse("deep_research.html", {"request": request})
    
    # 添加更多 Deep Research 相关路由...
    
    # 将路由注册到主应用
    app.include_router(router) 