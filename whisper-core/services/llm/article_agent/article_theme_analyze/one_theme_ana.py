import json
from typing import AsyncGenerator, Tuple, Dict, Any, List

from services.llm.agent.base_agent import BaseAgent, logger
from services.llm.utils.format_json import FormatJson


class OneThemeAnalyzer(BaseAgent):
    """单篇文章主题分析 Agent"""

    PROMPT_TEMPLATE = """
 ## 角色: 你是一位资深的爆款内容创作者和分析师。

 ## 背景: 分析以下文章全文：
 ```
 {content}
 ```

 ## 任务:
 仔细阅读并分析文章，然后简洁、清晰地总结出以下信息：

     1. **核心选题 (Main Topic):**
        * 这篇文章主要聚焦的核心话题、事件或现象是什么？
        * 它触及了哪些领域（例如：社会、科技、生活、文化、商业等）？
    
     2. **切入角度/叙事方式 (Entry Angle / Narrative Approach):**
        * 作者是如何引入这个话题的？（例如：个人经历、新闻事件、疑问、痛点、反常现象等）
        * 文章展开的主要叙事逻辑或结构是怎样的？（例如：问题探究型、现象解读型、体验分享型、观点对比型、辟谣揭秘型等）
        * 在呈现内容时运用了哪些主要的技巧或手法来吸引读者？（例如：制造悬念、幽默/梗、情绪共鸣、展示调查、数据对比、挑战常识等）
    
     3. **爆款潜力分析 (Viral Potential Analysis):**
        * 结合选题本身特点（如时效性、争议性、共鸣度、新奇度、信息差、情感浓度等），分析为什么这个**选题选择**本身具备成为爆款的潜力？它触及了大众的哪些普遍关切、情绪 G 点或好奇心？
    
     4. **底层逻辑/普适洞察 (Underlying Logic / Universal Insight):**
        * 请提炼文章内容背后更深层次、更本质的洞察。剥离具体的品牌名、人名、事件细节后，这篇文章揭示了什么样的**普遍现象、社会规律、人性特点或运作机制**？（例如：“信息不对称导致价值认知偏差”、“技术发展引发的伦理焦虑与情感需求”、“群体认同与标签化现象”、“情绪价值在决策中的作用”等，力求抽象和普适）
        
     5. **情感主线/基调 (Dominant Emotional Tone / Arc):**
        * 文章整体上呈现出怎样的主导情感色彩或基调？（例如：是普遍的焦虑感、对不公的愤怒、民族自豪感、怀旧情绪、幽默自嘲、理性探讨，还是温暖共情？）是否存在常见的情感引导模式（例如：从愤怒到反思，从焦虑到寻求解决方案），因为情感是驱动分享和共鸣的核心引擎。
        
     6. **常见价值主张 (Common Value Proposition):**
        * 文章通常为读者提供了哪些核心价值？（例如：提供信息差/内幕消息、引发情感共鸣/提供情绪价值、提供实用解决方案/避坑指南、拓宽视野/认知升级、提供身份认同/群体归属感、娱乐消遣等）,因为清晰的价值主张是内容吸引力的基础

 ## 输出格式:
     请严格以JSON格式返回结果，包含以下字段：
     - main_topic: (字符串) 核心选题的简洁描述。
     - domains: (字符串数组) 涉及的主要领域。
     - entry_point: (字符串) 文章引入话题的方式。
     - narrative_structure: (字符串) 主要的叙事逻辑或结构类型。
     - engagement_techniques: (字符串数组) 使用的主要吸引读者技巧。
     - viral_reasoning: (字符串) 对该选题为何具有爆款潜力的分析。
     - underlying_logic: (字符串) 对文章揭示的底层逻辑或普适洞察的提炼。
     - dominant_emotional:  (字符串) 对文章揭主导情感色彩或基调的提炼。
     - value_proposition: (字符串) 对文章为读者提供了哪些核心价值的总结。
    """

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

    async def process_response(self, response: AsyncGenerator[Tuple[str, str], None]) -> AsyncGenerator[
        Tuple[str, str], None]:
        """处理响应"""
        try:
            async for role, content in response:
                yield role, content
            yield 'done', 'done'

        except Exception as e:
            logger.error(f"处理主题分析响应失败: {str(e)}")
            yield "error", str(e)

    async def parse_response(self, response: str) -> Dict[str, Any]:
        """解析响应"""
        return await FormatJson.llm_parse(response, {
            "main_topic": "",
            "domains": [],
            "entry_point": "",
            "narrative_structure": "",
            "engagement_techniques": [],
            "viral_reasoning": "",
            "underlying_logic": "",
            "dominant_emotional": "",
            "value_proposition": ""
        })

    async def post_process(self) -> None:
        """后置处理"""
        pass
