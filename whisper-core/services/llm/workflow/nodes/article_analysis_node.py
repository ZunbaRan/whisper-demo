from typing import Dict, Any, AsyncGenerator, List, Tuple
import os
import json
import logging

from services.article_agent.author_style_analyzer.single_article_analyzer_agent import SingleArticleAnalyzer
from ..node import Node

logger = logging.getLogger(__name__)

class ArticleAnalysisNode(Node):
    """文章分析节点"""
    
    def __init__(self, name: str = "article_analysis"):
        super().__init__(name, SingleArticleAnalyzer())
        
    async def prepare_context(self) -> None:
        """准备上下文数据"""
        logger.info(f"准备文章分析节点上下文，输入: {json.dumps(self.inputs, ensure_ascii=False, indent=2)}")
        
        if "content" in self.inputs:
            # 单篇文章分析模式
            self.context = {
                "content": self.inputs.get("content", ""),
                "filename": self.inputs.get("filename", "unknown"),
                "author_name": self.inputs.get("author_name", "unknown")
            }
        else:
            # 批量分析模式
            self.context = {
                "articles_dir": self.inputs.get("articles_dir", ""),
                "author_name": self.inputs.get("author_name", "unknown")
            }
            
        logger.info(f"文章分析节点上下文: {json.dumps(self.context, ensure_ascii=False, indent=2)}")
        
    async def call(self) -> AsyncGenerator[Tuple[str, str], None]:
        """执行文章分析"""
        logger.info("开始执行文章分析")
        
        if "content" in self.context:
            # 单篇文章分析
            logger.info(f"分析单篇文章: {self.context['filename']}")
            async for result in self.agent.call(**self.context):
                yield result
        else:
            # 批量分析文章
            logger.info(f"批量分析文章，目录: {self.context['articles_dir']}")
            articles = await self._read_markdown_files(self.context["articles_dir"])
            logger.info(f"找到 {len(articles)} 篇文章需要分析")
            
            for article in articles:
                logger.info(f"开始分析文章: {article['filename']}")
                
                async for result in self.agent.call(
                    content=article["content"],
                    filename=article["filename"],
                    author_name=self.context["author_name"]
                ):
                    yield result
                    
            
    async def process_output(self, processed_results: List[Tuple[str, str]]) -> None:
        """处理输出数据"""
        logger.info("处理文章分析输出")

        # 提取元组集合中所有的 content 部分
        content_list = [result[1] for result in processed_results]
        content_str = "".join(content_list)  # 使用空字符串拼接
    
        logger.info(f"获取批量分析结果: {content_str}")
        self.outputs = {
            "analyses": content_str
        }

        logger.info(f"文章分析节点输出: {content_str}")

    async def _read_markdown_files(self, dir_path: str) -> List[Dict[str, str]]:
        """读取目录中的所有markdown文件"""
        logger.info(f"读取目录中的markdown文件: {dir_path}")
        articles = []
        for filename in os.listdir(dir_path):
            if filename.endswith('.md'):
                file_path = os.path.join(dir_path, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    articles.append({
                        "filename": filename,
                        "content": content
                    })
        logger.info(f"找到 {len(articles)} 个markdown文件")
        return articles
