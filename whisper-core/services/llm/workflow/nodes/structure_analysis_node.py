from abc import ABC
from typing import List, Tuple, AsyncGenerator

from services.article_agent.podcast_deconstructor.structure_analysis_agent import StructureAnalysisAgent
from services.llm.workflow.node import Node


class StructureAnalysisNode(Node):

    def __init__(self, name: str = "structure_analysis"):
        super().__init__(name, StructureAnalysisAgent())


    async def call(self) -> AsyncGenerator[Tuple[str, str], None]:
        """结构分析"""
        async for result in self.agent.call(**self.context):
            yield result


    async def prepare_context(self) -> None:
        theme_result = self.inputs.get("theme_result")
        elements_info = self.inputs.get("elements_info")

        self.context = {
            "theme_result": theme_result,
            "elements_info": elements_info
        }

    async def process_output(self, results: List[Tuple[str, str]]) -> None:
        # {"structure_outline": []}
        # 提取元组集合中所有的 content 部分, 并直接拼接为一个str
        content_list = [result[1] for result in results]
        content_str = "".join(content_list)  # 使用空字符串拼接
        con_theme = await self.agent.parse_response(content_str)

        """处理输出数据"""
        self.outputs = {
            "structure_outline": con_theme
        }

        print("结构分析node执行完毕")
