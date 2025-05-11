import uuid
from typing import AsyncGenerator, Tuple

from services.deeper_research.agent.search_report import SearchReportAgent
from services.llm.workflow.base.node import Node
from services.llm.workflow.base.output_manager import OutputManager


class SearchReportNode(Node):
    def __init__(self, tid: str = uuid.uuid4(), name: str = "search_report_node"):
        super().__init__(name, SearchReportAgent(), tid)
        self.output_manager = OutputManager("public/output")

    async def call(self) -> AsyncGenerator[Tuple[str, str], None]:
        """分析每篇文章的主题"""
        sub_queries = self.inputs["sub_queries"]
        async for role, content in self.agent.call(**self.context):
            print(f"{content}", flush=True)
            yield role, content

        self.outputs = {
            "preliminary_report_markdown": self.agent.format_res
        }