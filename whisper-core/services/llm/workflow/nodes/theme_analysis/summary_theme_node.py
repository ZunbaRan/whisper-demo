import uuid
from typing import AsyncGenerator, Tuple, List

from services.llm.article_agent.article_theme_analyze.summary_theme_agent import SummaryThemeAgent
from services.llm.workflow.base.node import Node
from services.llm.workflow.base.output_manager import OutputManager


class SummaryThemeNode(Node):
    """主题总结节点"""

    def __init__(self, tid: str = uuid.uuid4(), name: str = "summary_theme"):
        super().__init__(name, SummaryThemeAgent(), tid)
        self.tid = str(tid)
        self.output_manager = OutputManager("public/output", str(tid))

    async def prepare_context(self) -> None:
        """准备上下文数据"""
        # 获取前一个节点的分析结果
        analysis_results = self.inputs.get("analysis_results", [])

        self.context = {
            "analysis_results": analysis_results
        }

    async def call(self) -> AsyncGenerator[tuple[str, str], None]:
        """生成主题总结"""
        async for result in self.agent.call(**self.context):
            yield result

    async def process_output(self, results: List[Tuple[str, str]]) -> None:
        """处理输出数据"""

        format_res = self.agent.format_res

        self.context["summary_result"] = format_res

        # 保存到文件
        self.output_manager.save_step_output("theme_summary", format_res)

        # 设置输出
        self.outputs = {
            "summary_result": format_res
        }
