import json
from typing import AsyncGenerator, List, Dict, Any, Tuple

from services.llm.agent.base_agent import BaseAgent, logger

class DepthEnhancerAgent(BaseAgent):
    """深度与细微差别增强师 Agent"""

    PROMPT_TEMPLATE = """
    **角色:** 你是一位具备深厚领域知识  {topic_domain} 的批判性思考者和高级编辑，同时对写作风格有深刻理解。你的任务是提升草稿的思想深度和表达的细微差别，而非简单改写，并且把文章字数改写为3000字以下，在保留写作风格的前提下对文章进行凝练，字字幽默，金句频出，深刻又友好。

    **背景信息:**
    * **待审阅的文章草稿:**
        ```
        {draft}
        ```
    * **文章整体角度:**: {selected_angle}
    * **原始播客核心洞察 (供参考):**
        * main_theme: {main_theme}
        * Thesis: {thesis}
        * sub_topics: {sub_topics}
    * **目标作者风格指南:**
        ```
        {style_guide}
        ```

    **任务:**
    请仔细审阅提供的文章草稿，并针对以下方面提出**具体、可操作的**增强建议，并且按照建议修改文章，目的是在**严格保持** '[作者姓名]' 风格的前提下，增加内容的深度、说服力和细微差别：
    1.  **分析深度挖掘 (Deeper Analysis):**
        * 定位草稿中可以进行更深入分析的核心论点或观点。
        * **建议：** 提出可以追问的“为什么”或“这意味着什么？”。例如：“在第 3 段，当提到[某观点]时，可以进一步探讨其背后的[潜在假设]吗？建议增加一句：‘这实际上挑战了我们通常认为的...’”。
    2.  **拓展背景与联系 (Broader Context & Connections):**
        * 寻找可以将草稿观点与更广泛背景（当前趋势、历史事件、相关理论、跨领域知识）联系起来的机会。
        * **建议：** 提出具体的联系点。例如：“第 5 段讨论的[某策略]，可以简要联系到当前[某行业趋势]进行对比或印证，例如添加：‘这与我们在[另一领域]看到的[某现象]不谋而合。’”
    3.  **强化论证（适度） (Stronger Evidence/Illustration):**
        * 识别论证相对薄弱或可以进一步加强的地方。
        * **建议：** 建议在何处可以（如果符合风格）谨慎地补充一个**简短**的、**普遍认知**的例子、数据点或类比来强化论点。例如：“为增强第 2 段的说服力，可在[某主张]后补充一句概括性的数据说明，如：‘研究普遍显示，类似方法能提升效率约[X]%’。” (注意：除非必要，不虚构具体数据)
    4.  **引入细微差别/反思 (Nuance/Counter-arguments):**
        * 思考是否存在可以（且符合作者风格地）承认的复杂性、替代观点或潜在局限性，以使论证更全面、更可信。
        * **建议：** 提出具体的、符合风格的措辞来引入细微差别。例如：“在结尾段之前，可以考虑增加一句，承认‘当然，这种方法并非万能，在[特定情况]下可能需要调整...’，以体现作者思考的全面性。”
    5.  **根据思考的建议来对文章进行修改:**

    **约束:** 
    1. 所有建议必须以增强深度和细微差别为目标，同时**绝对尊重并维持** 目标作者的既定风格。避免提出会根本性改变风格的建议。
    2. 你所参考的所有内容都来源于用户输入的信息，严禁引入任何外部知识、数据、观点或进行无根据的推测**。
    3. 不要专门针对科学角度（如神经科学，计算机科学等严肃领域）专门进行创作探讨
    

输出格式: 请以markdown返回结果，包含修改点，修改建议，以及修改后的文章： 
输出示例：
    - 修改点1: 建议重写的段落
    - 该段落的问题/机会: 说明为什么这里需要增强段落分析
    - 具体建议: 提供**可直接采纳的修改建议**，可以是具体的措辞、需要补充的信息类型，或者需要进一步思考的问题。确保建议**符合风格指南**。
    
    - 修改点2: 建议重写的段落
    ...
    
    - 修改后的文章: 请直接返回修改后的文章内容，不要包含任何额外的解释或说明。
    """

    def __init__(self, model_name: str = "Gemini/gemini-2.5-pro"):
        super().__init__(model_name)
        self.thesis = None
        self.selected_angle = None
        self.sub_topics = None
        self.main_theme = None
        self.style_guide = None
        self.topic_domain = None
        self.draft = None

    async def pre_process(self) -> None:
        """前置处理"""
        # 从上下文中获取必要的参数
        self.draft = self.context.get("draft", "")
        self.style_guide = self.context.get("style_guide", "")
        self.topic_domain = self.context.get("topic_domain", "商业策略")  # 默认值
        self.main_theme = self.context.get("main_theme", "")
        self.sub_topics = self.context.get("sub_topics", "")
        self.selected_angle = self.context.get("selected_angle")
        self.thesis = self.context.get("thesis", "")

    async def build_messages(self) -> List[Dict[str, str]]:
        """构建消息"""
        prompt = await self.build_prompt(
            self.PROMPT_TEMPLATE,
            topic_domain=self.topic_domain,
            draft=self.draft,
            style_guide=self.style_guide,
            main_theme=self.main_theme,
            sub_topics=self.sub_topics,
            selected_angle=self.selected_angle,
            thesis=self.thesis
        )
        return [{'role': 'user', 'content': prompt}]


    async def parse_response(self, response: str) -> str:
        return response
