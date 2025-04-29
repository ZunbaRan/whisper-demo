from typing import Dict, List, Any, AsyncGenerator, Tuple, Coroutine
import json
import logging
from services.llm.agent.base_agent import BaseAgent
from services.llm.utils.format_json import FormatJson

logger = logging.getLogger(__name__)


class AngleHookStrategist(BaseAgent):

    def __init__(self, model_name: str = "Gemini/gemini-2.5-pro"):
        super().__init__(model_name)
        self.PROMPT_TEMPLATE = None

    """角度与引子策略师"""

    PROMPT_TEMPLATE = """
    **角色:** 你是一位顶尖的内容策略师和病毒式营销文案专家，极其擅长根据目标受众和核心信息，构思能够引发高度关注和讨论的文章切入点 (Angle) 和开头诱饵 (Hook)。

**背景信息:**
* **播客核心信息:**
    ```
    - 中心主题 {main_theme} 
    - 主要论点 {thesis}
    ```
* **关键洞察/建议:** {key_points}
* **亮点素材:** {examples}
* **目标受众画像:** '{target_audience}']'

任务: 基于此播客内容，为文章构思 3-5 个不同的角度或"引子"。对于每个角度：
1. 清晰陈述该角度/引子。
2. 解释*为什么*它会与目标受众产生共鸣。
3. 建议它如何与播客的核心信息联系起来。
4. 我们希望文章能融入 {emotional_elements} 的元素。
5. 简要说明期望的融入的元素可以如何融入这个角度。



**任务:**
基于以上所有信息，构思 3 到 5 个**截然不同**且具有高度吸引力的文章角度 (Angle) / 引子 (Hook)。对于你构思的每一个角度：
1.  **角度/引子陈述:** 用一两句话清晰、有力地概括这个角度。
2.  **受众共鸣点:** 详细解释**为什么**这个角度会特别吸引**上述指定的目标受众**，触及他们的哪些痛点、渴望或兴趣点。
3.  **内容链接:** 说明这个角度如何自然地引入并串联播客的核心信息、关键洞察和亮点素材。
4.  **共鸣情感元素整合策略:** 简要构思如何将“共鸣元素/情感触发”巧妙地融入这个角度的叙述中，使其看起来自然且有说服力。

输出格式: 请以JSON数组格式返回结果, 每个元素包含以下字段:
  - angle: 角度/引子陈述（字符串）
  - resonance: 受众共鸣点（字符串）
  - connection: 内容链接（字符串）
  - emotional_integration: 共鸣情感元素整合策略（字符串）"""

    def __init__(self,
                 target_audience: str = "寻求获取财富提升,以及阶级跨越的年轻人士，对职业发展感到焦虑，渴望提升效率，但又对市面上的通用建议感到疲倦",
                 emotional_elements: str = "容易引发讨论, 触发读者感情共鸣的元素"):
        super().__init__()
        self.target_audience = target_audience
        self.emotional_elements = emotional_elements

    async def pre_process(self) -> None:
        """预处理：验证输入数据"""

        required_fields = ["main_theme", "thesis", "golden_quotes", "examples"]
        for field in required_fields:
            if field not in self.context:
                raise ValueError(f"缺少必要字段: {field}")

    async def build_messages(self) -> List[Dict[str, str]]:
        """构建消息"""
        # 从context中获取必要信息
        thesis = self.context["thesis"]
        main_theme = self.context["main_theme"]
        key_points = self.context["golden_quotes"]  # 取前三个关键点
        examples = self.context["examples"]  # 取前三个例子

        prompt = await self.build_prompt(
            self.PROMPT_TEMPLATE,
            thesis=thesis,
            main_theme=main_theme,
            examples=json.dumps(examples, ensure_ascii=False, indent=4),
            key_points="\n".join(key_points),
            target_audience=self.target_audience,
            emotional_elements=self.emotional_elements
        )
        return [{'role': 'user', 'content': prompt}]

    async def process_response(self, response: AsyncGenerator[Tuple[str, str], None]) -> AsyncGenerator[
        Tuple[str, str], None]:
        """处理响应"""
        async for role, content in response:
            yield role, content
        yield 'assistant', '创意内容策略完成'

    async def post_process(self) -> None:
        """后处理：清理临时数据"""
        pass

    async def parse_response(self, response: str) -> list:
        """解析响应"""
        return await FormatJson.llm_parse(response)
