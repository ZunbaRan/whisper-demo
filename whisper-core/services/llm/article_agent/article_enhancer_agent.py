import json
from typing import AsyncGenerator, List, Dict, Any, Tuple

from services.llm.agent.base_agent import BaseAgent, logger

class ArticleEnhancerAgent(BaseAgent):
    """文章优化增强师 Agent"""
    ENHANCEMENT_PROMPT = """
    角色: 你是一位专业的文章优化师，你的核心职责是在**严格遵循原文风格和作者意图**的基础上，根据提供的问题描述和具体修改建议，对文章进行精准优化和提升。你擅长理解细微之处，确保修改自然流畅，如同出自原作者之手。

    背景:
    - **原文内容:** "{original_content}"
    - **修改建议:** 
    ```
    {suggestions}
    ```
    
    - **作者风格指南:** {style_guide}

    任务: 根据提供的修改建议，对文章进行优化。
    1. **保持原文风格:**
       - 严格遵循作者风格指南
       - 保持原有的语气和表达方式
       - 确保修改后的内容与原文风格一致

    2. **实施修改建议:**
       - 在指定位置进行修改
       - 确保修改符合建议要求
       - 保持修改的连贯性和自然性

    3. **优化效果检查:**
       - 确保修改后的内容更加清晰
       - 检查修改是否达到预期效果
       - 验证修改是否符合整体风格

    输出格式:
    [完整的、已优化的文章内容]
    """

    async def pre_process(self) -> None:
        """前置处理"""
        self.content = self.context.get("content", "")
        self.style_guide = self.context.get("style_guide", "")
        self.suggestions = self.context.get("suggestions", "")

    async def build_messages(self) -> List[Dict[str, str]]:
        """构建消息"""
    
        prompt = await self.build_prompt(
            self.ENHANCEMENT_PROMPT,
            original_content=self.content,
            suggestions=self.suggestions,
            style_guide=self.style_guide
        )
        return [{'role': 'user', 'content': prompt}]

    async def process_response(self, response: AsyncGenerator[Tuple[str, str], None]) -> AsyncGenerator[Tuple[str, str], None]:
        pass
      
    async def parse_response(self, response: str) -> Dict[str, Any]:
        pass

    async def post_process(self) -> None:
       pass