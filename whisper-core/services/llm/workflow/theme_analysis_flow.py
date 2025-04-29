import os
import json
from typing import AsyncGenerator, Tuple
import logging

from services.llm.workflow.nodes.theme_analysis.one_theme_node import OneThemeNode
from services.llm.workflow.nodes.theme_analysis.summary_theme_node import SummaryThemeNode
from services.llm.workflow.base.workflow import Workflow

logger = logging.getLogger(__name__)


class ThemeAnalysisFlow:
    """主题分析工作流"""

    def __init__(self):
        self.workflow = Workflow("theme_analysis_flow")
        self.context = self.workflow.context

        # 创建节点
        self.one_theme_node = OneThemeNode(self.workflow.get_tid())
        self.summary_theme_node = SummaryThemeNode(self.workflow.get_tid())

        # 添加节点到工作流
        self.workflow.add_node(self.one_theme_node)
        self.workflow.add_node(self.summary_theme_node)

        # 设置节点执行顺序
        self.workflow.set_node_order([self.one_theme_node.name, self.summary_theme_node.name])

    async def analyze_themes(self, articles_dir: str) -> AsyncGenerator[Tuple[str, str], None]:
        """分析文章主题的主方法"""

        # 检查目录是否存在
        if not os.path.exists(articles_dir):
            raise FileNotFoundError(f"目录不存在: {articles_dir}")
        if not os.path.isdir(articles_dir):
            raise NotADirectoryError(f"路径不是目录: {articles_dir}")

        # 准备初始输入
        initial_inputs = {
            "articles_dir": articles_dir
        }

        logger.info(f"开始执行主题分析工作流")
        logger.info(f"文章目录: {articles_dir}")
        logger.info(f"初始输入: {json.dumps(initial_inputs, ensure_ascii=False, indent=2)}")

        # 执行工作流
        async for result in self.workflow.execute(initial_inputs):
            yield result
