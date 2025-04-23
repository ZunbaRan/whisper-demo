from typing import List, Tuple, AsyncGenerator

from services.article_agent.engagement_injector_agent import EngagementInjectorAgent
from services.llm.workflow.node import Node


class EngagementInjectorNode(Node):
    async def call(self) -> AsyncGenerator[Tuple[str, str], None]:
        """互动与争议注入"""
        async for result in self.agent.call(**self.context):
            yield result

    async def prepare_context(self) -> None:
        draft = self.inputs.get("draft")
        style_guide = self.inputs.get("style_guide")

        self.context = {
            "draft": draft,
            "style_guide": style_guide
        }


    async def process_output(self, results: List[Tuple[str, str]]) -> None:
        # 提取元组集合中所有的 content 部分, 并直接拼接为一个str
        content_list = [result[1] for result in results]
        content_str = "".join(content_list)  # 使用空字符串拼接
        print(f"结构分析结果: {content_str}")

        """处理输出数据"""
        self.outputs = {
            "engagement_injector": content_str
        }

    def __init__(self, name: str = "engagement_injector"):
        super().__init__(name, EngagementInjectorAgent())