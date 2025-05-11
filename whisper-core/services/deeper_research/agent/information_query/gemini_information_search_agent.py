import json
from typing import Dict, Any, List, Union, AsyncGenerator, Tuple

from google.genai.types import GenerateContentConfig, GoogleSearch, Tool

from services.llm.agent.base_agent import BaseAgent
from services.llm.search_agent.search_res import SearchRes
from services.llm.utils.format_json import FormatJson


class GeminiInformationSearchAgent(BaseAgent):
    """使用 Gemini 进行联网搜索的 Agent"""

    def __init__(self):
        super().__init__(model_name="Gemini/gemini-2.5-flash")

    async def pre_process(self) -> None:
        google_search_tool = Tool(
            google_search=GoogleSearch()
        )

        # 配置 Google Search grounding
        config = GenerateContentConfig(
            tools=[google_search_tool],
            response_modalities=["TEXT"]
        )
        self.context["config"] = config

    async def build_messages(self) -> List[Dict[str, str]]:
        query = self.context.get("query")
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]
        return messages

    async def parse_response(self, response: str) ->  str | SearchRes:
        return response
