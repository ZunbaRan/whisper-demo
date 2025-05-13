from typing import Union, List, Dict
import asyncio

from services.llm.agent.base_agent import BaseAgent
from services.llm.utils import search_tool


class SearchReportAgent(BaseAgent):
    def __init__(self):
        super().__init__(model_name="Gemini/gemini-2.5-pro")

    PROMPT_TEMPLATE = open("services/deeper_research/agent/search_report_prompt.md", "r", encoding="utf-8").read()

    async def pre_process(self) -> None:
        sub_queries: list = self.context["sub_queries"]
        # 随机选择3个sub_query，避免超出token限制
        import random
        random.shuffle(sub_queries)
        sub_queries = sub_queries[:3]

        # Create a list of tasks for each sub_query search
        search_tasks = []
        for sub_query in sub_queries:
            print(f"==================sub_query: {sub_query}")
            # search_tool.web_search is an async function, so it can be awaited directly
            search_tasks.append(search_tool.web_search(sub_query))

        # Execute all search tasks concurrently
        # The results will be a list of strings (markdown_content_str from web_search)
        search_execution_results = await asyncio.gather(*search_tasks)

        self.context["search_execution_results"] = search_execution_results

    async def build_messages(self) -> List[Dict[str, str]]:
        prompt = await self.build_prompt(
            self.PROMPT_TEMPLATE,
            initial_ai_search_query=self.context["initial_ai_search_query"],
            search_execution_results=self.context["search_execution_results"]
        )
        return [{'role': 'user', 'content': prompt}]

    async def parse_response(self, response: str) -> Union[dict, list, str, int, float, bool, None]:
        return response
