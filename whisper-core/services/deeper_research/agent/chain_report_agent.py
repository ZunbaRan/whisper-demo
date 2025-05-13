import json
import re
from typing import Dict, List, Union, Optional, Tuple, AsyncGenerator

from services.deeper_research.agent.information_query import search_information
from services.llm.agent.base_agent import BaseAgent


class ChainReport(BaseAgent):
    def     __init__(self):
        super().__init__(model_name="Gemini/gemini-2.5-pro")
        self.question_chain_details_copy = {}

    PROMPT_TEMPLATE = open("services/deeper_research/agent/high_topic_question_chain_prompt.md", "r", encoding="utf-8").read()

    async def pre_process(self) -> None:
        high_topic_question_chain = self.context["high_topic_question_chain"]

        question_chain_details = high_topic_question_chain.get('question_chain_details')

        question_chain_details_copy = []
        # question_chain_details dict 数组
        for question_chain_detail in question_chain_details:
            res = await search_information.search_information(question_chain_detail)
            search_results_for_query = res

            # 复制 res 并截取<search_results> 和 </search_results>之间的内容
            # 如果没有<search_results> 和 </search_results>之间的内容，则返回原始内容
            match = re.search(r"<search_results>(.*?)</search_results>", search_results_for_query, re.DOTALL)
            if match:
                search_results_for_query_cut = match.group(1).strip()
            else:
                search_results_for_query_cut = search_results_for_query

            # 复制 question_chain_detail
            question_chain_detail_copy = question_chain_detail.copy()
            # 完整数据用来生成报告
            question_chain_detail_copy["search_results_for_query"] = search_results_for_query
            question_chain_details_copy.append(question_chain_detail_copy)

            # 用来后续流程
            question_chain_detail["search_results_for_query"] = search_results_for_query_cut


        # 完整数据用来生成报告
        self.question_chain_details_copy = question_chain_details_copy



    async def parse_response(self, response: str) -> str:
        return response


    async def build_messages(self) -> List[Dict[str, str]]:
        pass

    async def call(
            self,
            content: Optional[str] = None,
            files: Optional[List[Dict[str, str]]] = None,
            **kwargs
    ) -> AsyncGenerator[Tuple[str, str], None]:
        self.context = {
            "content": content or '',
            "query": content or '',
            "files": files or [],
            **kwargs
        }

        await self.pre_process()

        res = self.context["high_topic_question_chain"]
        yield "content", json.dumps(res, ensure_ascii=False)

        self.format_res = res

