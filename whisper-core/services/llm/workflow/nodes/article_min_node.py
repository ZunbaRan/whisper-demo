import json
import uuid
from typing import List, Tuple, AsyncGenerator

from services.llm.article_agent.article_min import ArticleMinAgent
from services.llm.article_agent.depth_enhancer_agent import DepthEnhancerAgent
from services.llm.workflow.base.node import Node


class ArticleMinNode(Node):
    async def call(self) -> AsyncGenerator[Tuple[str, str], None]:
        """主题分析"""
        async for result in self.agent.call(**self.context):
            yield result

    async def prepare_context(self) -> None:
        self.context = {
            "style_guide": self.inputs.get("style_guide"),
            "draft": self.inputs.get("draft", "")
        }

    async def process_output(self, results: List[Tuple[str, str]]) -> None:

        # 提取元组集合中所有的 content 部分
        content_list = [result[1] for result in results]
        content_str = "".join(content_list)  # 使用空字符串拼接

        self.outputs = {
            "article_min": content_str
        }

    def __init__(self, tid: str = uuid.uuid4(), name: str = "article_min"):
        super().__init__(name, ArticleMinAgent(), tid)
