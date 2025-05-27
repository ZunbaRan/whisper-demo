import json
from typing import AsyncGenerator, Dict, Any, List, Tuple

from services.llm.agent.base_agent import BaseAgent, logger


class ChapterAndStyleAgent(BaseAgent):
    """章节创作，负责按章节撰写文章并注入特定风格"""

    PROMPT_TEMPLATE_PATH = "services/llm/article_agent/structured_draft/chapter_style_prompt_temp.md"

    def __init__(self, model_name: str = "Gemini/gemini-2.5-pro"):
        super().__init__(model_name)
        self.PROMPT_TEMPLATE = None

    async def pre_process(self) -> None:
        # 读取文件
        with open(self.PROMPT_TEMPLATE_PATH, 'r', encoding='utf-8') as file:
            self.PROMPT_TEMPLATE = file.read()

    async def build_messages(self) -> List[Dict[str, str]]:
        # 从context中获取所需信息
        selected_angle = self.context.get("selected_angle", "")
        style_guide = self.context.get("style_guide", "")
        sections_dict = self.context.get("sections", "")

        sections = ''
        if sections_dict:
            # 转为str
            sections = json.dumps(sections_dict, ensure_ascii=False)

        prompt = await self.build_prompt(
            self.PROMPT_TEMPLATE,
            selected_angle=selected_angle,
            style_guide=style_guide,
            sections=sections
        )
        return [{'role': 'user', 'content': prompt}]


        # angle = self.context.get("angle", "")
        # section_index = self.context.get("section_index")
        # section_type = self.context.get("section_type", "")
        # section_title = self.context.get("section_title", "")
        #
        # chapter_purpose = self.context.get("chapter_purpose", "")
        # previous_chapter = self.context.get("previous_chapter", "")
        # chapter_key_points = self.context.get("chapter_key_points", "")
        # content_elements = self.context.get("content_elements", "")
        # estimated_length = self.context.get("estimated_length", 500)
        # writing_guidance = self.context.get("writing_guidance", "")
        #
        # prompt = await self.build_prompt(
        #     self.PROMPT_TEMPLATE,
        #     angle=angle,
        #     chapter_purpose=chapter_purpose,
        #     style_guide=style_guide,
        #     previous_chapter=previous_chapter,
        #     estimated_length=estimated_length,
        #     chapter_key_points=chapter_key_points,
        #     content_elements=content_elements,
        #     selected_angle=selected_angle,
        #     writing_guidance=writing_guidance,
        #     section_index=section_index,
        #     section_type=section_type,
        #     section_title=section_title
        # )
        # return [{'role': 'user', 'content': prompt}]

    async def parse_response(self, response: str) -> str | None | Any:
        return response