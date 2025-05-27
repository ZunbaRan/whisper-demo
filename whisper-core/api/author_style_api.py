from fastapi import APIRouter, HTTPException
import os
from typing import Dict, Any, List
import json

from services.llm.workflow.style_analysis_flow import StyleAnalysisFlow

router = APIRouter()

@router.post("/analyze-style")
async def analyze_author_style(author_name: str, articles_dir: str) -> Dict[str, Any]:
    """
    分析作者风格的API端点
    
    Args:
        author_name: 作者名称
        articles_dir: 文章目录路径
    
    Returns:
        Dict[str, Any]: 包含分析结果和状态信息的字典
    """

    # 创建文章分析工作流
    article_flow = StyleAnalysisFlow(author_name)

    # 收集所有输出
    results = []
    async for result in article_flow.analyze_author_style(articles_dir):
        results.append(result)

    return {
        "status": "success",
        "message": "作者风格分析完成",
    }

