import json
from typing import List, Dict, AsyncGenerator, Tuple, Any

from services.llm.agent.base_agent import BaseAgent, logger


class StructureAnalysisAgent(BaseAgent):
    """结构分析Agent"""

    PROMPT_TEMPLATE = """角色: 你是一位逻辑思考者，擅长辨别论证结构。
背景: 基于以下信息，判断原始讨论可能的逻辑流程或叙事结构：
主题信息：{theme_info}
关键元素：{elements_info}

任务: 概述其结构。例如：
    - 提出问题 -> 分析原因 -> 提供解决方案 -> 举例说明
    - 概念介绍 -> 解释说明 -> 案例1 -> 案例2 -> 结论
    - 按时间顺序叙事 -> 关键经验教训

输出格式: 请以JSON格式返回结果，包含以下字段：
- structure_outline: 结构大纲列表（字符串数组）"""

    async def pre_process(self) -> None:
        pass

    async def build_messages(self) -> List[Dict[str, str]]:
        theme_result = self.context["theme_result"]
        elements_result = self.context["elements_info"]
        prompt = await self.build_prompt(
            self.PROMPT_TEMPLATE,
            theme_info=json.dumps(theme_result, ensure_ascii=False),
            elements_info=json.dumps(elements_result, ensure_ascii=False)
        )
        return [{'role': 'user', 'content': prompt}]

    async def process_response(self, response: AsyncGenerator[Tuple[str, str], None]) -> AsyncGenerator[Tuple[str, str], None]:
        async for role, content in response:
            yield role, content
        yield 'assistant', '结构分析完成'

    async def post_process(self) -> None:
        pass

    async def parse_response(self, response: str) -> list[str]:
        try:
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
            return []