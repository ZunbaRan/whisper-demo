
from typing import  Dict, List, Union

from langchain_core.output_parsers import JsonOutputParser

from services.llm.agent.base_agent import BaseAgent


class HighTopicQuestionChain(BaseAgent):
    def __init__(self):
        super().__init__(model_name="Gemini/gemini-2.5-pro")

    PROMPT_TEMPLATE = open("services/deeper_research/agent/high_topic_question_chain_prompt.md", "r", encoding="utf-8").read()


    async def parse_response(self, response: str) -> Union[dict, list, str, int, float, bool, None]:
        parser = JsonOutputParser()
        return parser.parse(response)


    async def build_messages(self) -> List[Dict[str, str]]:
        prompt = await self.build_prompt(
            self.PROMPT_TEMPLATE,
            one_high_potential_topic=self.context["one_high_potential_topic"],
            knowledge_base_topic_summary_content=self.context["knowledge_base_topic_summary_content"],
            knowledge_base_heuristic_patterns_content=self.context["knowledge_base_heuristic_patterns_content"]
        )
        return [{'role': 'user', 'content': prompt}]

