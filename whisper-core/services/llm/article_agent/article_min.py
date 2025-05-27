import json
from typing import AsyncGenerator, List, Dict, Any, Tuple

from services.llm.agent.base_agent import BaseAgent, logger

class ArticleMinAgent(BaseAgent):

    PROMPT_TEMPLATE = """
    请你阅读这篇草稿，借助文笔风格指南，对文章进行修改润色，不符合文笔风格指南的地方进行润色调整，同时对冗余的地方进行删减，保证总字数在3000字以下

    * **待审阅的文章草稿:**
        ```
        {draft}
        ```
    * **目标文笔风格指南:**
        ```
        {style_guide}
        ```
    """

    def __init__(self, model_name: str = "Gemini/gemini-2.5-pro"):
        super().__init__(model_name)
        self.style_guide = None
        self.draft = None

    async def pre_process(self) -> None:
        """前置处理"""
        # 从上下文中获取必要的参数
        self.draft = self.context.get("draft", "")
        self.style_guide = self.context.get("style_guide", "")

    async def build_messages(self) -> List[Dict[str, str]]:
        """构建消息"""
        prompt = await self.build_prompt(
            self.PROMPT_TEMPLATE,
            draft=self.draft,
            style_guide=self.style_guide,
        )
        return [{'role': 'user', 'content': prompt}]


    async def parse_response(self, response: str) -> str:
        return response
