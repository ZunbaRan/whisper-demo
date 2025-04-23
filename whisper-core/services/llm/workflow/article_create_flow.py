import os
import json
from typing import Dict, Any, AsyncGenerator, List, Tuple
import logging

from .nodes.angle_hook_strategist_node import AngleHookStrategistNode
from .nodes.chapter_and_style_node import ChapterAndStyleNode
from .nodes.depth_enhancer_node import DepthEnhancerNode
from .nodes.elements_extraction_node import ElementsExtractionNode
from .nodes.engagement_injector_node import EngagementInjectorNode
from .nodes.structure_analysis_node import StructureAnalysisNode
from .nodes.structured_draft_node import StructuredDraftNode
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
        # 角度钩选策略节点
        self.angle_hook_strategist_node = AngleHookStrategistNode()
        # 结构化草稿节点
        self.structured_draft_node = StructuredDraftNode()
        # 章节创作节点
        self.chapter_and_style_node = ChapterAndStyleNode()
        # 深度与细微差别增强节点
        self.depth_enhancer_node = DepthEnhancerNode()
        # 互动与争议注入节点
        self.engagement_injector_node = EngagementInjectorNode()

        # 添加节点到工作流
        self.workflow.add_node(self.theme_analysis_node)
        self.workflow.add_node(self.elements_extraction_node)
        self.workflow.add_node(self.structure_analysis_node)
        self.workflow.add_node(self.structured_draft_node)
        self.workflow.add_node(self.angle_hook_strategist_node)
        self.workflow.add_node(self.structured_draft_node)
        self.workflow.add_node(self.chapter_and_style_node)
        self.workflow.add_node(self.depth_enhancer_node)
        self.workflow.add_node(self.engagement_injector_node)

        # 设置节点执行顺序
        self.workflow.set_node_order([self.theme_analysis_node.name,
                                      self.elements_extraction_node.name,
                                      self.structure_analysis_node.name,
                                      self.structured_draft_node.name,
                                      self.angle_hook_strategist_node.name,
                                      self.structured_draft_node.name,
                                      self.chapter_and_style_node.name,
                                      self.depth_enhancer_node.name,
                                      self.engagement_injector_node.name,
                                      ])

    async def analyze_author_style(self, content: str) -> AsyncGenerator[Tuple[str, str], None]:
        """分析作者风格的主方法"""

        # 准备初始输入
        initial_inputs = {
            "content": content
        }

        # 执行工作流
        async for result in self.workflow.execute(initial_inputs):
            yield result
