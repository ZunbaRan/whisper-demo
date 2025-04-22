import os
import json
from typing import Dict, Any, AsyncGenerator, List, Tuple
import logging
from .nodes.elements_extraction_node import ElementsExtractionNode
from .nodes.structure_analysis_node import StructureAnalysisNode
from .nodes.theme_analysis_node import ThemeAnalysisNode
from .workflow import Workflow

logger = logging.getLogger(__name__)


class ArticleAnalysisFlow:
    """文章分析工作流"""

    def __init__(self, author_name: str):
        self.author_name = author_name
        self.workflow = Workflow("article_create_flow")
        self.context = self.workflow.context

        # 主题分析节点
        self.theme_analysis_node = ThemeAnalysisNode()
        # 元素提取节点
        self.elements_extraction_node = ElementsExtractionNode()
        # 结构分析节点
        self.structure_analysis_node = StructureAnalysisNode()

        # 添加节点到工作流
        self.workflow.add_node(self.theme_analysis_node)
        self.workflow.add_node(self.elements_extraction_node)
        self.workflow.add_node(self.structure_analysis_node)

        # 设置节点执行顺序
        self.workflow.set_node_order([self.theme_analysis_node.name,
                                      self.elements_extraction_node.name,
                                      self.structure_analysis_node.name])

    async def analyze_author_style(self, content: str) -> AsyncGenerator[Tuple[str, str], None]:
        """分析作者风格的主方法"""

        # 准备初始输入
        initial_inputs = {
            "content": content
        }

        # 执行工作流
        async for result in self.workflow.execute(initial_inputs):
            yield result
