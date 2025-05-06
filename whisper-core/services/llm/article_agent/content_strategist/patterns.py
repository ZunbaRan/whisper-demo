from typing import Dict, List, Union, AsyncGenerator, Tuple

from services.llm.agent.base_agent import BaseAgent


class PatternsAgent(BaseAgent):
    """内容创作模式Agent"""

    PROMPT_TEMPLATE = open("Patterns.md", "r", encoding="utf-8").read()

    async def process_response(self, response: AsyncGenerator[Tuple[str, str], None]) -> AsyncGenerator[
        Tuple[str, str], None]:
        async for item in super().process_response(response):
            yield item
            
    async def post_process(self) -> None:
        await super().post_process()

    async def parse_response(self, response: str) -> Union[dict, list, str, int, float, bool, None]:
        return response


    async def pre_process(self) -> None:
        pass

    async def build_messages(self) -> List[Dict[str, str]]:
        prompt = await self.build_prompt(
            self.PROMPT_TEMPLATE,
            content=self.context["content"]
        )
        return [{'role': 'user', 'content': prompt}]

