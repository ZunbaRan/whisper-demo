from typing import AsyncGenerator, Tuple, Dict, Any
from fastapi import APIRouter, HTTPException
import logging

from services.llm.workflow.nodes.theme_ana.theme_analysis_flow import ThemeAnalysisFlow

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/analyze-themes")
async def analyze_themes(articles_dir: str = "C:/Users/14589/Documents/write-style") -> Dict[str, Any]:
    """
    分析文章主题的API端点
    
    Args:
        articles_dir: 包含待分析文章的目录路径
        
    Returns:
        生成器，返回分析过程中的状态和结果
    """
    try:
        # 创建主题分析工作流实例
        flow = ThemeAnalysisFlow()

        results = []

        # 执行分析
        async for result in flow.analyze_themes(articles_dir):
            results.append(result)

        return {
            "status": "success",
            "message": "文章创建分析完成",
            "results": results,
        }


    except Exception as e:
        error_msg = f"分析文章主题时发生错误: {str(e)}"
        logger.error(error_msg)
        raise Exception(str(e))
