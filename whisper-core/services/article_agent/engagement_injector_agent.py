import json
from typing import AsyncGenerator, List, Dict, Any, Tuple

from services.llm.agent.base_agent import BaseAgent, logger

class EngagementInjectorAgent(BaseAgent):
    """互动与争议注入师 Agent"""

    PROMPT_TEMPLATE = """
    **角色:**: 你是一位精通心理学和写作策略的专家，擅长在保持作者风格的同时，巧妙地识别和在文本中植入能够激发读者互动、思考或轻微“焦虑感”的心理触发点。

    背景:
    - **文章草稿:** 
    ```
    {draft}
    ```
    - **目标作者风格指南:** 
    ```
    {style_guide}
    ```

    **任务:**
    分析文章内容，识别适合注入互动/争议元素的位置,并进行策略性改写。
    1. **自动识别机会点:**
       - 寻找可以制造紧迫感/焦虑感的位置
       - 发现可以创造稀缺感的场景
       - 识别可以挑战常规观点的段落
       - 定位适合引入辩论点的内容

    2. **策略性改写:**
       - 在识别的位置巧妙融入互动/焦虑感/紧迫感/挑战/辩论元素
       - 确保改写与原文风格自然融合
       - 保持作者独特的语气和表达方式
       - 避免过度夸张或失实

    **约束:**
    **无缝融合:** 确保修改后的内容与原文风格、语气和逻辑完全一致，读起来天衣无缝，不显得突兀或生硬。
    **！！！风格一致性是铁律！！！:** **绝对、严格地**维持目标作者风格指南中定义的所有特征（语气、词汇、句法等）。互动元素必须像是作者本人会写出来的一样。
    **道德底线:** **严禁**使用误导性信息、制造恐慌、人身攻击或任何不道德的操纵手段。互动元素应表现为有力的观点、深刻的洞察或引人思考的问题。

    输出格式: 修改后的文章内容

"""

    def __init__(self, model_name: str = "Gemini/Gemini-2.0-Flash-thinking"):
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
            style_guide=self.style_guide
        )
        return [{'role': 'user', 'content': prompt}]

    async def process_response(self, response: AsyncGenerator[Tuple[str, str], None]) -> AsyncGenerator[Tuple[str, str], None]:
        async for role, content in response:
            yield role, content
        yield 'assistant', '互动元素注入完成'

    async def parse_response(self, response: str) -> Dict[str, Any]:
        pass

    async def post_process(self) -> None:
        """后置处理"""
        pass 