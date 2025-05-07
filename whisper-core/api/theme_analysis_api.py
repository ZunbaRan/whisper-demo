from typing import AsyncGenerator, Tuple, Dict, Any
from fastapi import APIRouter, HTTPException
import logging

from services.llm.workflow.question_chain_flow import QuestionChainFlow
from services.llm.workflow.theme_analysis_flow import ThemeAnalysisFlow

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/analyze-themes")
async def analyze_themes(articles_dir: str = "input/article_ana") -> Dict[str, Any]:
    """
    分析文章主题的API端点
    
    Args:
        articles_dir: 包含待分析文章的目录路径
        
    Returns:
        生成器，返回分析过程中的状态和结果
    """

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


@router.post("/analyze-question-chain")
async def analyze(articles_dir: str = "input/article_ana") -> Dict[str, Any]:
    """
    分析question-chain的API端点

    Args:
        articles_dir: 包含待分析文章的目录路径

    Returns:
        生成器，返回分析过程中的状态和结果
    """

    # 创建主题分析工作流实例
    flow = QuestionChainFlow()

    results = []

    # 执行分析
    async for result in flow.analyze(articles_dir):
        results.append(result)

    return {
        "status": "success",
        "message": "文章创建分析完成",
        "results": results,
    }
