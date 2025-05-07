import os
import json
from typing import AsyncGenerator, Tuple
import logging

from .nodes.style_guide.article_analysis_node import ArticleAnalysisNode
from .nodes.style_guide.style_guide_node import StyleGuideNode
from services.llm.workflow.base.workflow import Workflow


logger = logging.getLogger(__name__)


class StyleAnalysisFlow:
    """文章分析工作流"""

    def __init__(self, author_name: str):
        self.author_name = author_name
        self.workflow = Workflow("article_analysis_flow")
        self.context = self.workflow.context

        # 创建节点
        self.analysis_node = ArticleAnalysisNode()
        self.style_guide_node = StyleGuideNode()

        # 添加节点到工作流
        self.workflow.add_node(self.analysis_node)
        self.workflow.add_node(self.style_guide_node)

        # 设置节点执行顺序
        self.workflow.set_node_order([self.analysis_node.name, self.style_guide_node.name])

    async def analyze_author_style(self, articles_dir: str) -> AsyncGenerator[Tuple[str, str], None]:
        """分析作者风格的主方法"""
        try:
            # 检查目录是否存在
            if not os.path.exists(articles_dir):
                raise FileNotFoundError(f"目录不存在: {articles_dir}")
            if not os.path.isdir(articles_dir):
                raise NotADirectoryError(f"路径不是目录: {articles_dir}")

            # 准备初始输入
            initial_inputs = {
                "articles_dir": articles_dir,
                "author_name": self.author_name
            }

            logger.info(f"开始执行文章分析工作流，作者: {self.author_name}")
            logger.info(f"文章目录: {articles_dir}")
            logger.info(f"初始输入: {json.dumps(initial_inputs, ensure_ascii=False, indent=2)}")

            # 执行工作流
            async for result in self.workflow.execute(initial_inputs):
                yield result

        except Exception as e:
            error_msg = f"分析作者风格时发生错误: {str(e)}"
            logger.error(error_msg)
            yield 'error', error_msg
            yield 'done' ,'[DONE]'
