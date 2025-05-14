import json
from typing import AsyncGenerator, Dict, Any, List, Tuple, Coroutine

from services.llm.agent.base_agent import BaseAgent, logger


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

    async def build_messages(self) -> List[Dict[str, str]]:
        # 从context中获取所需信息
        theme_result = self.context.get("theme_result", "")
        selected_angle = self.context.get("selected_angle", "")
        structure_outline = self.context.get("structure_outline", "")
        elements_info = self.context.get("elements_info", "")

        prompt = await self.build_prompt(
            self.PROMPT_TEMPLATE,
            theme_result=theme_result,
            selected_angle=selected_angle,
            structure_outline=structure_outline,
            elements_info=elements_info,
        )
        return [{'role': 'user', 'content': prompt}]

    async def process_response(self, response: AsyncGenerator[Tuple[str, str], None]) -> AsyncGenerator[
        Tuple[str, str], None]:
        async for role, content in response:
            yield role, content
        yield 'assistant', '详细大纲生成完成'

    async def post_process(self) -> None:
        pass

    async def parse_response(self, response: str) -> dict[Any, Any] | None | Any:
        try:
            # 提取JSON内容
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end != -1:
                    json_content = response[start:end].strip()
                    return json.loads(json_content)
            else:
                return json.loads(response)

        except json.JSONDecodeError as e:
            logger.error(f"解析JSON响应失败: {str(e)}")
            return {}
