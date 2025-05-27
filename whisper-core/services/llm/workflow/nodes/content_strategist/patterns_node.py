import uuid
from typing import List, Tuple, AsyncGenerator

from services.llm.article_agent.content_strategist.patterns import PatternsAgent
from services.llm.workflow.base.node import Node
from services.llm.workflow.base.output_manager import OutputManager


class PatternNode(Node):

    def __init__(self, tid: str = uuid.uuid4(), name: str = "summary_theme"):
        super().__init__(name, PatternsAgent(), tid)
        self.tid = str(tid)
        self.output_manager = OutputManager("public/output", str(tid))

    async def call(self) -> AsyncGenerator[Tuple[str, str], None]:
        """生成主题总结"""
        async for result in self.agent.call(**self.context):
            yield result

    async def prepare_context(self) -> None:
        """准备上下文数据"""
        # 获取前一个节点的分析结果
        analysis_results = self.inputs.get("question_chain_results", [])

        self.context = {
            "analysis_results_collection": analysis_results
        }

    async def process_output(self, results: List[Tuple[str, str]]) -> None:
        """处理输出数据"""

        format_res = self.agent.format_res

        self.context["patterns"] = format_res

        # 保存到文件
        self.output_manager.save_str_file("patterns", format_res)

        # 设置输出
        self.outputs = {
            "patterns": format_res
        }
