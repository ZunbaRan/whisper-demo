import json
from typing import List, Tuple, AsyncGenerator

from services.article_agent.depth_enhancer_agent import DepthEnhancerAgent
from services.llm.workflow.node import Node, logger


class DepthEnhancerNode(Node):
    async def call(self) -> AsyncGenerator[Tuple[str, str], None]:
        """主题分析"""
        async for result in self.agent.call(**self.context):
            yield result

    async def prepare_context(self) -> None:
        angles = self.inputs.get("angles")
        theme_result = self.inputs.get("theme_result")

        self.context = {
            "main_theme": theme_result.get("main_theme", ""),
            "thesis": theme_result.get("thesis", ""),
            "sub_topics": theme_result.get("sub_topics", []),
            "topic_domain": theme_result.get("topic_domain", ""),
            "selected_angle": json.dumps(angles[0], ensure_ascii=False),
            "style_guide": self.inputs.get("style_guide"),
            "draft": self.inputs.get("draft", "")
        }

    async def process_output(self, results: List[Tuple[str, str]]) -> None:

        # 提取元组集合中所有的 content 部分
        content_list = [result[1] for result in results]
        content_str = "".join(content_list)  # 使用空字符串拼接

        self.outputs = {
            "enhancement_result": content_str
        }
        print("深度与细微差别增强师执行完毕")

    def __init__(self, name: str = "depth_enhancer"):
        super().__init__(name, DepthEnhancerAgent())
