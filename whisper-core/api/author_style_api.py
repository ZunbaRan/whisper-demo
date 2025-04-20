from fastapi import APIRouter, HTTPException
from services.llm.workflow.article_flow import ArticleFlow
import os
from typing import Dict, Any, List
import json

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
    try:
        # 创建文章分析工作流
        article_flow = ArticleFlow(author_name)
        
        # 收集所有输出
        results = []
        async for result in article_flow.analyze_author_style(articles_dir):
            results.append(result)
        
        # 获取输出文件列表
        analysis_files = []
        style_guides = []
        output_dir = os.path.join("output", "author_style", author_name)
        if os.path.exists(output_dir):
            for filename in os.listdir(output_dir):
                if filename.endswith('_analysis.json'):
                    analysis_files.append(filename)
                elif filename.endswith('_style_guide.md'):
                    style_guides.append(filename)

        return {
            "status": "success",
            "message": "作者风格分析完成",
            "results": results,
            "output_files": {
                "analysis_files": analysis_files,
                "style_guides": style_guides
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
