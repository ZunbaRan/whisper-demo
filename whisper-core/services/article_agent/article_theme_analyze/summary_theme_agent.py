import json
from typing import AsyncGenerator, Tuple, Dict, Any, List

from services.llm.agent.base_agent import BaseAgent, logger

class SummaryThemeAgent(BaseAgent):
    """多篇文章主题总结 Agent"""

    PROMPT_TEMPLATE = """角色: 你是一位资深的爆款内容策略专家。

背景: 基于以下多篇文章分析结果进行总结：
```
{analysis_results}
```

任务: 总结并清晰地列出这些爆款文章在以下两个方面的共性、常见模式和通用策略：

1. **选题策略总结 (Topic Selection Strategies Summary):**
   * 这些文章倾向于选择哪些**类型**的话题？（例如：社会热点追踪、生活痛点挖掘、科技趋势解读、网络现象剖析、常识挑战/辟谣、特定圈层文化、个人成长/经验等）
   * 选题时是否存在一些共同的**考量因素**？（例如：时效性、争议性、共鸣度、新奇度、实用性等）

2. **切入角度/叙事技巧总结 (Entry Angle / Narrative Techniques Summary):**
   * 这些文章常见的**引入方式**有哪些？（例如：个人故事/经历、设置悬念/疑问、引用数据/新闻、描绘冲突/反差、直接点明痛点等）
   * 在**叙事推进和内容呈现**上，有哪些常用的技巧或模式？（例如：口语化/幽默化表达、展现调查/求证过程、"我"视角代入、多角度信息整合与对比、制造情绪起伏、结构化论证、调用读者互动等）

输出格式: 请以JSON格式返回结果，包含以下字段：
- topic_types: 话题类型（字符串数组）
- selection_factors: 选题考量因素（字符串数组）
- entry_methods: 常见引入方式（字符串数组）
- narrative_techniques: 叙事技巧（字符串数组）
- summary_insights: 总结性洞察（字符串数组）"""

    async def pre_process(self) -> None:
        """前置处理"""
        self.analysis_results = self.context.get("analysis_results", [])

    async def build_messages(self) -> List[Dict[str, str]]:
        """构建消息"""
        # 将分析结果转换为字符串
        results_str = json.dumps(self.analysis_results, ensure_ascii=False, indent=2)
        
        prompt = await self.build_prompt(
            self.PROMPT_TEMPLATE,
            analysis_results=results_str
        )
        return [{'role': 'user', 'content': prompt}]

    async def process_response(self, response: AsyncGenerator[Tuple[str, str], None]) -> AsyncGenerator[Tuple[str, str], None]:
        async for item in super().process_response(response):
            yield item

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
                "topic_types": [],
                "selection_factors": [],
                "entry_methods": [],
                "narrative_techniques": [],
                "summary_insights": []
            }

    async def post_process(self) -> None:
        """后置处理"""
        await super().post_process()
