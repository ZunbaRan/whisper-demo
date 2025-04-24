import json
from typing import AsyncGenerator, Tuple, List, Dict, Any

from services.llm.agent.base_agent import BaseAgent, logger


class ElementsExtractionAgent(BaseAgent):
    """元素提取Agent"""

    PROMPT_TEMPLATE = """角色: 你是一位细致的内容提取者，专注于识别对话中的有影响力元素。
背景: 分析以下播客文字稿： "{text}"
已知主题信息：{theme_info}

任务: 基于以上主题信息，精确提取以下元素（原文引用或准确总结）：
1. 金句 (Golden Quotes): 识别并列出那些特别有见地、令人难忘、有力或完美概括核心观点的原话句子或短语。
2. 可行动建议/要点 (Actionable Advice/Takeaways): 列出发言者建议的清晰、简洁的建议或可执行步骤。
3. 例证/案例研究 (Illustrative Examples/Case Studies): 简要总结用于阐述观点的任何故事、轶事、具体的公司案例或个人经历。
4. 关键数据/统计 (Key Data/Statistics): 列出为支持主张而提及的任何具体数字、百分比或数据点。

输出格式: 请以JSON格式返回结果，包含以下字段：
- golden_quotes: 金句列表（字符串数组）
- actionable_advice: 可行动建议列表（字符串数组）
- examples: 例证列表（对象数组，每个对象包含summary和illustrates字段）
- data_points: 关键数据列表（字符串数组）"""

    async def pre_process(self) -> None:
        pass

    async def build_messages(self) -> List[Dict[str, str]]:
        content = self.context["content"]
        theme_result = self.context["theme_result"]
        prompt = await self.build_prompt(
            self.PROMPT_TEMPLATE,
            text=content,
            theme_info=json.dumps(theme_result, ensure_ascii=False)
        )
        return [{'role': 'user', 'content': prompt}]

    async def process_response(self, response: AsyncGenerator[Tuple[str, str], None]) -> AsyncGenerator[Tuple[str, str], None]:
        async for role, content in response:
            yield role, content
        yield 'assistant', '关键元素提取完成'

    async def post_process(self) -> None:
        pass

    async def parse_response(self, response: str) -> Dict[str, Any]:
        pass