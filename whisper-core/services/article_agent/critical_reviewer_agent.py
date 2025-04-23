import json
from typing import AsyncGenerator, List, Dict, Any, Tuple

from services.llm.agent.base_agent import BaseAgent, logger

class CriticalReviewerAgent(BaseAgent):
    """批判性审阅与一致性检查器 Agent"""

    PROMPT_TEMPLATE = """
    角色: 你是一位极其严谨、注重细节的资深总编辑，拥有评估内容质量、风格一致性和整体影响力的火眼金睛。你的任务是对最终草稿进行全面的、基于标准的质量控制审查。

    背景信息:
    * **待最终审阅的文章草稿:**
        ```
        {draft}
        ```
    * **原始项目目标:**
        * **内容来源:** 将播客摘要 
        ```
            * main_theme: {main_theme}
            * Thesis: {thesis}
            * sub_topics: {sub_topics}
        ```        
        转化为文章。
        * **选定角度:** '{selected_angle}'
        * **模仿风格:**  (风格指南附后)。
    * **作者风格指南:**
        ```
        {style_guide}
        ```

    任务:
    请根据以下所有标准，对文章草稿进行严格、彻底的批判性评估。对于每项标准，请给出评分（1-10分，10分为最佳），并提供具体的、引用原文的例子来支持你的评分和评论：

    1. **内容保真度 (Content Fidelity):** (评分: /10)
       草稿是否准确、完整地反映了原始播客的核心信息和关键论点？是否存在误解或遗漏？
       * 评论/示例:

    2. **角度执行力 (Angle Execution):** (评分: /10)
       选定的文章角度是否在全文中得到清晰、一致的体现和贯彻？文章是否围绕该角度展开？
       * 评论/示例:

    3. **风格遵循度 (Style Adherence):** (评分: /10)
       文章在多大程度上成功模仿了 '{author_name}' 的风格？请对照风格指南，逐项（语气、句法、词汇、修辞、结构等）评价，并明确指出任何显著的偏差或不一致之处。
       * 评论/示例:

    4. **互动元素整合效果 (Engagement Element Integration):** (评分: /10)
       指定的"互动/争议/紧迫感"元素是否被有效、巧妙且合乎道德地整合进文章？感觉是自然流露还是强行植入？效果是否符合预期？
       * 评论/示例:

    5. **连贯性与流畅性 (Coherence & Flow):** (评分: /10)
       文章的整体结构是否逻辑清晰？段落之间、句子之间的过渡是否平滑自然？是否存在阅读障碍？
       * 评论/示例:

    6. **整体影响力与质量 (Overall Impact & Quality):** (评分: /10)
       综合来看，这篇文章是否有说服力、有见地？是否可能吸引并打动目标受众？是否存在任何明显的硬伤（事实错误、逻辑矛盾等）？
       * 评论/示例:

    输出格式: 提供一份结构化的评审报告。严格按照上述 6 个标准进行组织。在每个标准下，包含评分、详细评论和具体的原文引用示例。最后，给出一个**整体评估总结**和**最终修改建议**（如果需要）。

    """

    async def pre_process(self) -> None:
        """前置处理"""
        # 从上下文中获取必要的参数
        self.draft = self.context.get("draft", "")
        self.thesis = self.context.get("thesis", "")
        self.key_points = self.context.get("key_points", [])
        self.selected_angle = self.context.get("selected_angle", "")
        self.author_name = self.context.get("author_name", "")
        self.style_guide = self.context.get("style_guide", "")
        self.engagement_goals = self.context.get("engagement_goals", "")

    async def build_messages(self) -> List[Dict[str, str]]:
        """构建消息"""
        prompt = await self.build_prompt(
            self.PROMPT_TEMPLATE,
            draft=self.draft,
            thesis=self.thesis,
            key_points=self.key_points,
            selected_angle=self.selected_angle,
            author_name=self.author_name,
            style_guide=self.style_guide,
            engagement_goals=self.engagement_goals
        )
        return [{'role': 'user', 'content': prompt}]

    async def process_response(self, response: AsyncGenerator[Tuple[str, str], None]) -> AsyncGenerator[Tuple[str, str], None]:
        """处理响应"""
        try:
            # 合并所有响应内容
            full_response = ""
            for role, content in response:
                if role == "assistant":
                    full_response += content
                    yield (role, content)

            # 解析评审结果
            review_result = await self.parse_response(full_response)
            self.context["review_result"] = review_result
            
            # 输出评审完成消息
            yield ("assistant", "批判性审阅完成")
            yield ("done", "")
            
        except Exception as e:
            logger.error(f"处理批判性审阅响应失败: {str(e)}")
            yield ("error", str(e))

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
                "reviews": [],
                "overall_summary": "",
                "final_suggestions": []
            }

    async def post_process(self) -> None:
        """后置处理"""
        pass 