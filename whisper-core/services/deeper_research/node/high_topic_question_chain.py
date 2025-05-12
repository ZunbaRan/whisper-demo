import json
import uuid
from typing import AsyncGenerator, Tuple

from google.genai.types import GenerateContentConfig
from langchain_community.document_loaders import TextLoader

from services.deeper_research.agent.high_topic_question_chain import HighTopicQuestionChain
from services.deeper_research.agent.initial_query_sub_queries import InitialQuerySubQueriesAgent
from services.llm.workflow.base.node import Node
from services.llm.workflow.base.output_manager import OutputManager


from pydantic import BaseModel
from typing import List, Optional

# 定义问题链详情的子模型
class QuestionChainDetail(BaseModel):
    question: str
    answer_focus: str
    information_needed_queries: List[str]

# 定义主模型
class HighTopicQuestionChainModel(BaseModel):
    question_chain_framework_description: str
    question_chain_details: List[QuestionChainDetail]
    suggested_entry_method: str
    suggested_narrative_techniques: List[str]

class HighTopicQuestionChainNode(Node):

    def __init__(self, tid: str = uuid.uuid4(), name: str = "high_topic_question_chain"):
        super().__init__(name, HighTopicQuestionChain(), tid)
        self.output_manager = OutputManager("public/output")

    async def pre_process(self) -> None:
        # 配置 Google Search grounding
        config = GenerateContentConfig(
            response_mime_type="application/json",
            response_schema = HighTopicQuestionChainModel
        )
        self.context["config"] = config

    async def call(self) -> AsyncGenerator[Tuple[str, str], None]:
        async for role, content in self.agent.call(**self.context):
            print(f"{content}", flush=True)
            yield role, content

        self.outputs = {
            "high_topic_question_chain": self.agent.format_res,
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
