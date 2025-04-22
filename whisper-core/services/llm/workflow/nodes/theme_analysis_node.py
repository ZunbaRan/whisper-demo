from typing import List, Tuple, AsyncGenerator, Any

from services.article_agent.podcast_deconstructor.theme_analysis_agent import ThemeAnalysisAgent
from services.llm.workflow.node import Node
from services.llm.workflow.output_manager import OutputManager


class ThemeAnalysisNode(Node):

    def __init__(self, name: str = "theme_analysis"):
        super().__init__(name, ThemeAnalysisAgent())
        self.output_manager = OutputManager()

    async def call(self) -> AsyncGenerator[Tuple[str, str], None]:
        """主题分析"""
        async for result in self.agent.call(**self.context):
            yield result

    async def prepare_context(self) -> None:
        pass

    async def process_output(self, results: List[Tuple[str, str]]) -> None:
        # - main_theme: 中心主题（字符串）
        # - thesis: 主要论点（字符串）
        # - sub_topics: 子主题列表（字符串数组

        # 提取元组集合中所有的 content 部分, 并直接拼接为一个str
        content_list = [result[1] for result in results]
        content_str = "".join(content_list)  # 使用空字符串拼接
        print(f"风格指南生成结果: {content_str}")

        # {"main_theme": "", "thesis": "", "sub_topics": []}
        con_theme = await self.agent.parse_response(content_str)

        """处理输出数据"""
        self.outputs = {
            "theme_result": con_theme
        }
