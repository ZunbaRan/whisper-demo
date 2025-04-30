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
   * 这些文章倾向于选择哪些**类型**的话题？
   * 选题时是否存在一些共同的**考量因素**？

2. **切入角度/叙事技巧总结 (Entry Angle / Narrative Techniques Summary):**
   * 这些文章的**引入方式**有哪些？（例如：个人故事/经历、设置悬念/疑问、引用数据/新闻、描绘冲突/反差、直接点明痛点等）
   * 在**叙事推进和内容呈现**上，有哪些技巧或模式？（例如：口语化/幽默化表达、展现调查/求证过程、"我"视角代入、多角度信息整合与对比、制造情绪起伏、结构化论证、调用读者互动等）
   
3. **爆款驱动因素共性提炼 (Common Viral Drivers Synthesis):**
   * **关键环节：** 综合所有分析中的 `viral_reasoning` 部分，**提炼列举**出这些选题能够**成功引爆传播**的、反复出现的**核心驱动因素**是什么？请具体化，例如，不仅仅是“情绪共鸣”，而是“引发对XX的焦虑/自豪/愤怒”等。

4. **底层逻辑/普适洞察归纳 (Recurring Underlying Logics Synthesis):**
   * **关键环节：** 综合所有分析中的 `underlying_logic` 部分，**总结归纳列举**这些爆款内容背后，**反复揭示**了哪些具有**普适性的核心洞察、社会规律、人性特点或时代症候**？请列出最常出现的几类本质洞察。
   
5. **情感主线/基调 (Dominant Emotional Tone / Arc):**
   * **关键环节：** 综合所有分析中的 `dominant_emotional`部分，**总结归纳列举**这些文章整体上呈现出怎样的主导情感色彩或基调？（例如：是普遍的焦虑感、对不公的愤怒、民族自豪感、怀旧情绪、幽默自嘲、理性探讨，还是温暖共情？）是否存在常见的情感引导模式（例如：从愤怒到反思，从焦虑到寻求解决方案），因为情感是驱动分享和共鸣的核心引擎。
        
6. **常见价值主张 (Common Value Proposition):**
   * 文章通常为读者提供了哪些核心价值？（例如：提供信息差/内幕消息、引发情感共鸣/提供情绪价值、提供实用解决方案/避坑指南、拓宽视野/认知升级、提供身份认同/群体归属感、娱乐消遣等）,因为清晰的价值主张是内容吸引力的基础


输出格式: 请以JSON格式返回结果，包含以下字段：
- topic_types: 话题类型（字符串数组）
- selection_factors: 选题考量因素（字符串数组）
- entry_methods: 常见引入方式（字符串数组）
- narrative_techniques: 叙事技巧（字符串数组）
- summary_insights: 总结性洞察（字符串数组）
- dominant_emotional_list: 主导情感色彩或基调(字符串数组)
- value_propositions: 核心价值列表（字符串数组)

"""

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
                "summary_insights": [],
                "dominant_emotional_list": [],
                "value_propositions": []
            }

    async def post_process(self) -> None:
        """后置处理"""
        await super().post_process()
