import uuid
from fastapi import APIRouter, HTTPException
import os
from typing import Dict, Any, List


from services.llm.workflow.article_create_flow import ArticleCreateFlow

router = APIRouter()


@router.post("/article-create-style")
async def article_create_style(podcast_file: str) -> Dict[str, Any]:
    """
    创建作者API端点

    
    Returns:
        Dict[str, Any]: 包含分析结果和状态信息的字典
    """

    # 创建文章分析工作流
    article_flow = ArticleCreateFlow("bi")

    print(f"----------tid: {article_flow.workflow.get_tid()}")

    results = []
    # output/c6c1ac2e-0582-11f0-a087-2b17684717c1.txt

    podcast_file_dir = os.path.join("output", podcast_file)
    if os.path.exists(podcast_file_dir):
        with open(podcast_file_dir, "r", encoding="utf-8") as f:
            content = f.read()

    async for result in article_flow.create_article(content):
        results.append(result)

    return {
        "status": "success",
        "message": "文章创建分析完成",
        "results": results,
    }


@router.post("/resume-article-create-style")
async def resume_article_create_style(node_name: str, tid: str) -> Dict[str, Any]:
    """
    从指定节点继续执行文章创建工作流
    """
    try:
        # 创建文章分析工作流
        article_flow = ArticleCreateFlow(tid, 'bi')

        results = []
        async for result in article_flow.resume_from_node(node_name):
            results.append(result)

        return {
            "status": "success",
            "message": "文章创建分析完成",
            "results": results,
        }
    except Exception as e:
        raise Exception(str(e))
