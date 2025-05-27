import json
from typing import AsyncGenerator, Dict, Any, List, Tuple, Coroutine

from google.genai.types import GenerateContentConfig
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel

from services.llm.agent.base_agent import BaseAgent, logger


class Section(BaseModel):
    section_index: int
    section_type: str
    section_title: str
    chapter_purpose: str
    chapter_key_points: List[str]
    content_elements: List[str]
    writing_guidance: str

class StructuredDraftRes(BaseModel):
    sections: List[Section]

class StructuredDraftAgent(BaseAgent):
    """结构化草稿Agent，负责创建详细的文章大纲"""

    PROMPT_TEMPLATE_PATH = "services/llm/article_agent/structured_draft/structured_draft_prompt_temp.md"

    def __init__(self, model_name: str = "Gemini/gemini-2.5-pro"):
        super().__init__(model_name)
        self.PROMPT_TEMPLATE = None

    async def pre_process(self) -> None:
        # 读取文件
        with open(self.PROMPT_TEMPLATE_PATH, 'r', encoding='utf-8') as file:
            self.PROMPT_TEMPLATE = file.read()

        if self.model_name.startswith("Gemini"):
            config = GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=StructuredDraftRes
            )
            self.context["config"] = config

    async def build_messages(self) -> List[Dict[str, str]]:
        # 从context中获取所需信息
        theme_result = self.context.get("theme_result", "")
        # selected_angle = self.context.get("selected_angle", "")
        structure_outline = self.context.get("structure_outline", "")
        elements_info = self.context.get("elements_info", "")

        prompt = await self.build_prompt(
            self.PROMPT_TEMPLATE,
            theme_result=theme_result,
            # selected_angle=selected_angle,
            structure_outline=structure_outline,
            elements_info=elements_info,
        )
        return [{'role': 'user', 'content': prompt}]


    async def parse_response(self, response: str) -> dict   [Any, Any] | None | Any:
        parser = JsonOutputParser()
        return parser.parse(response)
