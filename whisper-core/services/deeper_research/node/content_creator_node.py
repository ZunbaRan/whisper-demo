import uuid
from typing import AsyncGenerator, Tuple, List

from google.genai.types import GenerateContentConfig

from services.deeper_research.agent.chain_report_agent import ChainReport
from services.deeper_research.agent.content_creator.content_creator_agent import ContentCreatorAgent
from services.llm.workflow.base.node import Node
from services.llm.workflow.base.output_manager import OutputManager


class ContentCreatorNode(Node):

    def __init__(self, tid: str = uuid.uuid4(), name: str = "content_creator_node"):
        super().__init__(name, ContentCreatorAgent(), tid)
        self.output_manager = OutputManager("public/output")


    async def call(self) -> AsyncGenerator[Tuple[str, str], None]:
        async for role, content in self.agent.call(**self.context):
            print(f"{content}", flush=True)
            yield role, content

        self.outputs = {
            "content_create": self.agent.format_res
        }

    # async def process_output(self, results: List[Tuple[str, str]]) -> None:
    #     """处理输出结果"""
    #     report_to_save = self.agent.__getattribute__("question_chain_details_copy")
    #     self.output_manager.save_step_output("chain_report_node", report_to_save)


