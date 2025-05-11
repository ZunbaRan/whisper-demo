from typing import List, Dict, Union

from services.llm.agent.base_agent import BaseAgent
from services.llm.utils.format_json import FormatJson


class PerAnalysisReport(BaseAgent):

    def __init__(self):
        super().__init__(model_name="Gemini/gemini-2.5-pro")

    PROMPT_TEMPLATE = open("services/deeper_research/agent/per_analysis_report_prompt.md", "r", encoding="utf-8").read()

    async def build_messages(self) -> List[Dict[str, str]]:
        prompt = await self.build_prompt(
            self.PROMPT_TEMPLATE,
            initial_ai_search_query=self.context["initial_ai_search_query"],
            preliminary_report_markdown=self.context["preliminary_report_markdown"],
            knowledge_base_topic_summary_content = self.context["knowledge_base_topic_summary_content"],
            knowledge_base_heuristic_patterns_content = self.context["knowledge_base_heuristic_patterns_content"]
        )
        return [{'role': 'user', 'content': prompt}]

    async def parse_response(self, response: str) -> Union[dict, list, str, int, float, bool, None]:
        return await FormatJson.llm_parse(response)