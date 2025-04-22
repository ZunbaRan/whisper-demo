from typing import List, Tuple, Any, AsyncGenerator

from services.article_agent.podcast_deconstructor.elements_extraction_agent import ElementsExtractionAgent
from services.llm.workflow.node import Node


class ElementsExtractionNode(Node):

    def __init__(self, name: str = "elements_extraction"):
        super().__init__(name, ElementsExtractionAgent())

    async def call(self) -> AsyncGenerator[Tuple[str, str], None]:
        """元素提取"""
        async for result in self.agent.call(**self.context):
            yield result

    async def prepare_context(self) -> None:
        content = self.inputs.get("content", "")
        theme_result = self.inputs.get("theme_result")

        self.context = {
            "content": content,
            "theme_result": theme_result
        }

    async def process_output(self, results: List[Tuple[str, str]]) -> Any:
        # 提取元组集合中所有的 content 部分, 并直接拼接为一个str
        content_list = [result[1] for result in results]
        content_str = "".join(content_list)  # 使用空字符串拼接
        print(f"元素提取结果: {content_str}")

        # {
        #     "golden_quotes": [],
        #     "actionable_advice": [],
        #     "examples": [],
        #     "data_points": []
        # }
        elements_info = await self.agent.parse_response(content_str)

        """处理输出数据"""
        self.outputs = {
            "elements_info": elements_info
        }

