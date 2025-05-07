import json
import logging
import os
from typing import AsyncGenerator, Tuple

from services.llm.workflow.base.workflow import Workflow
from services.llm.workflow.nodes.content_strategist.patterns_node import PatternNode
from services.llm.workflow.nodes.content_strategist.question_chain_node import Question_Chain_Node

logger = logging.getLogger(__name__)


class QuestionChainFlow:
    def __init__(self):
        self.workflow = Workflow("question_chain_flow")
        self.context = self.workflow.context

        # 创建节点
        self.question_chain_node = Question_Chain_Node(self.workflow.get_tid())
        self.patterns_node = PatternNode(self.workflow.get_tid())

        # 添加节点到工作流
        self.workflow.add_node(self.question_chain_node)
        self.workflow.add_node(self.patterns_node)

        # 设置节点执行顺序
        self.workflow.set_node_order([self.question_chain_node.name, self.patterns_node.name])

    async def analyze(self, articles_dir: str) -> AsyncGenerator[Tuple[str, str], None]:
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

        logger.info(f"开始执行工作流")
        logger.info(f"文章目录: {articles_dir}")
        logger.info(f"初始输入: {json.dumps(initial_inputs, ensure_ascii=False, indent=2)}")

        # 执行工作流
        async for result in self.workflow.execute(initial_inputs):
            yield result
