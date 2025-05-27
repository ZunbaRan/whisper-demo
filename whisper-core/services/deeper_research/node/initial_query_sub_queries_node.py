import json
import uuid
from typing import AsyncGenerator, Tuple

from langchain_community.document_loaders import TextLoader

from services.deeper_research.agent.initial_query_sub_queries import InitialQuerySubQueriesAgent
from services.llm.workflow.base.node import Node
from services.llm.workflow.base.output_manager import OutputManager


class InitialQuerySubQueriesNode(Node):

    async def call(self) -> AsyncGenerator[Tuple[str, str], None]:
        async for role, content in self.agent.call(**self.context):
            print(f"{content}", flush=True)
            yield role, content

        self.outputs = {
            "sub_queries": self.agent.format_res,
            "knowledge_base_topic_summary_content": self.context["knowledge_base_topic_summary_content"],
            "knowledge_base_heuristic_patterns_content": self.context["knowledge_base_heuristic_patterns_content"]
        }

    async def prepare_context(self) -> None:
        """准备上下文"""
        kb1_path = "services/agent_doc/patterns.txt"
        loader = TextLoader(kb1_path, encoding="utf-8")
        docs = loader.load()
        self.context["knowledge_base_heuristic_patterns_content"] = docs[0].page_content
        
        kb2_path = "services/agent_doc/theme_summary.json"
        # 读取json文件
        with open(kb2_path, "r", encoding="utf-8") as f:
            self.context["knowledge_base_topic_summary_content"] = json.load(f)
            
        # loader = JSONLoader(kb2_path, jq_schema='.[]')
        # docs = loader.load()
        # self.context["theme_summary"] = docs[0].page_content
    


    def __init__(self, tid: str = uuid.uuid4(), name: str = "initial_query_sub_queries_node"):
        super().__init__(name, InitialQuerySubQueriesAgent(), tid)
        self.output_manager = OutputManager("public/output")