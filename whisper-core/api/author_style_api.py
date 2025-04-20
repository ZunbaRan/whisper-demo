from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import json
import os
from services.article_agent.author_style_analyzer import AuthorStyleAnalyzer

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
        # 创建分析器实例
        analyzer = AuthorStyleAnalyzer(author_name)
        
        # 分析作者风格
        results = []
        async for result in analyzer.analyze_author_style(articles_dir):
            if result.startswith("data: "):
                if result[6:12] == '[DONE]':
                    break
                data = json.loads(result[6:])
                if data.get("role") == "assistant":
                    results.append(data.get("content", ""))

        
        return {
            "status": "success",
            "message": "作者风格分析完成",
            "results": results,
            "output_files": {
                "analysis_files": [f"{filename}_analysis.json" for filename in os.listdir(articles_dir) if filename.endswith('.md')],
                "style_guides": results
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get-analysis/{author_name}/{filename}")
async def get_article_analysis(author_name: str, filename: str) -> Dict[str, Any]:
    """
    获取特定文章的分析结果
    
    Args:
        author_name: 作者名称
        filename: 文章文件名
    
    Returns:
        Dict[str, Any]: 包含文章分析结果的字典
    """
    try:
        analysis_file = os.path.join("output", "author_style", author_name, f"{filename}_analysis.json")
        if not os.path.exists(analysis_file):
            raise HTTPException(status_code=404, detail=f"文章 {filename} 的分析结果不存在")
        
        with open(analysis_file, "r", encoding="utf-8") as f:
            return json.load(f)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get-style-guide/{author_name}/{tag}")
async def get_style_guide(author_name: str, tag: str) -> Dict[str, Any]:
    """
    获取特定tag的风格指南
    
    Args:
        author_name: 作者名称
        tag: 文章类型标签
    
    Returns:
        Dict[str, Any]: 包含风格指南内容的字典
    """
    try:
        guide_file = os.path.join("output", "author_style", author_name, f"{tag}_style_guide.md")
        if not os.path.exists(guide_file):
            raise HTTPException(status_code=404, detail=f"{tag} 类型的风格指南不存在")
        
        with open(guide_file, "r", encoding="utf-8") as f:
            return {
                "tag": tag,
                "content": f.read()
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 