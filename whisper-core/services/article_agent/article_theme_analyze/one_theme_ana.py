import json
from typing import AsyncGenerator, Tuple, Dict, Any, List

from services.llm.agent.base_agent import BaseAgent, logger

class OneThemeAnalyzer(BaseAgent):
    """单篇文章主题分析 Agent"""

    PROMPT_TEMPLATE = """角色: 你是一位资深的爆款内容创作者和分析师。

背景: 分析以下文章全文：
```
{content}
```

任务: 仔细阅读并分析文章，然后简洁、清晰地总结出：

1. **核心选题 (Main Topic):**
   * 这篇文章主要聚焦的核心话题、事件或现象是什么？
   * 它触及了哪些领域（例如：社会、科技、生活、文化、商业等）？

2. **切入角度/叙事方式 (Entry Angle / Narrative Approach):**
   * 作者是如何引入这个话题的？（例如：是否用了个人经历、新闻事件、一个疑问、一个普遍痛点、一个反常现象等作为开头？）
   * 文章展开的主要叙事逻辑或结构是怎样的？（例如：是问题探究型、现象解读型、体验分享型、观点对比型、辟谣揭秘型等？）
   * 在呈现内容时运用了哪些主要的技巧或手法来吸引读者？（例如：制造悬念、运用幽默/梗、引发情绪共鸣、展示调查过程、数据对比、挑战常识等？）

输出格式: 请以JSON格式返回结果，包含以下字段：
- main_topic: 核心选题（字符串）
- domains: 涉及领域（字符串数组）
- entry_point: 引入方式（字符串）
- narrative_structure: 叙事结构（字符串）
- engagement_techniques: 吸引读者技巧（字符串数组）"""

    async def pre_process(self) -> None:
        """前置处理"""
        pass

    async def build_messages(self) -> List[Dict[str, str]]:
        """构建消息"""
        prompt = await self.build_prompt(
            self.PROMPT_TEMPLATE,
            content=self.context["content"]
        )
        return [{'role': 'user', 'content': prompt}]

    async def process_response(self, response: AsyncGenerator[Tuple[str, str], None]) -> AsyncGenerator[Tuple[str, str], None]:
        """处理响应"""
        try:
            async for role, content in response:
                yield role, content
            yield 'done','done'

        except Exception as e:
            logger.error(f"处理主题分析响应失败: {str(e)}")
            yield "error", str(e)

    async def parse_response(self, response: str) -> Dict[str, Any]:
        """解析响应"""
        try:
            # 提取JSON内容
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end != -1:
                    json_content = response[start:end].strip()
                    return json.loads(json_content)
            
            # 如果没有找到JSON标记，尝试直接解析
            return json.loads(response)
            
        except json.JSONDecodeError as e:
            logger.error(f"解析JSON响应失败: {str(e)}")
            return {
                "main_topic": "",
                "domains": [],
                "entry_point": "",
                "narrative_structure": "",
                "engagement_techniques": []
            }

    async def post_process(self) -> None:
        """后置处理"""
        pass
