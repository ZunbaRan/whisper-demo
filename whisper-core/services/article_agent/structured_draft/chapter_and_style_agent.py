import json
from typing import AsyncGenerator, Dict, Any, List, Tuple

from services.llm.agent.base_agent import BaseAgent, logger


class ChapterAndStyleAgent(BaseAgent):
    """章节创作，负责按章节撰写文章并注入特定风格"""

    PROMPT_TEMPLATE = """
    **角色:** 你是一位技艺精湛的写手，能够完全沉浸在特定作者的风格中进行创作，目前正在撰写文章的特定一章。

    **背景:**
    - **文章整体角度:**: {selected_angle}
    - **当前章节目标:**: {chapter_purpose}
    - **本章需包含的关键内容:**: {chapter_key_points}
    - **本章需要包含的内容元素列表:** {content_elements}
    - **作者风格指南:**: 
        ```
        {style_guide}
        ```
    - **前一章节内容:**: (如果是第一章节, 则不需要提供) {previous_chapter}

    **任务:**
    请严格按照以下要求，撰写文章的**当前这一个章节**：
    1.  **达成章节目标:** 清晰、完整地阐述本章节应涵盖的内容和观点。
    2.  **融入关键内容:** 自然、有效地将指定的金句、数据、例子等素材编织进文本中。
    3.  **！！！绝对严格遵守风格指南！！！:** 在遣词造句（词汇选择、句式结构、句子长度）、语气语态、段落构建、修辞使用等方面，**必须**完全符合提供的“[作者姓名] 风格指南”中的所有规定。
    4.  **确保流畅性:** 如果提供了上一章节内容，确保开头能顺畅衔接。章节内部逻辑清晰，过渡自然。
    5.  **符合字数要求:** 力求达到预估字数范围, 大约 {estimated_length} 字。
    
    **注意事项:**
    1. **不要显示的说明章节：** 所有的章节属于同一篇文章的不同段落，不是实际的段落分割，因此不能在文中说明类似“上一章节讨论了...” “下一章再讨论...”等字样
    2. **素材汉化:** 对于金句、例子等内容，**必须**使用中文进行翻译。如果直接引用“金句、例证”等素材，只需要使用 > 符号进行标注，不要出现类似“我们引用的金句..” “有人曾说过...”等字样

    **输出格式 markdown:**
    **仅提供当前所撰写章节的完整文本。不要包含任何额外的说明、标题或注释，除非是章节本身的标题（如果大纲中有）。

    **约束:** 风格模仿的准确性是最高优先级。内容需服务于章节目标。
    """

    async def pre_process(self) -> None:
        pass

    async def build_messages(self) -> List[Dict[str, str]]:
        # 从context中获取所需信息
        angle = self.context.get("angle", "")
        chapter_purpose = self.context.get("chapter_purpose", "")
        chapter_content = self.context.get("chapter_content", "")
        style_guide = self.context.get("style_guide", "")
        selected_angle = self.context.get("selected_angle", "")
        previous_chapter = self.context.get("previous_chapter", "")
        chapter_key_points = self.context.get("chapter_key_points", "")
        content_elements = self.context.get("content_elements", "")
        estimated_length = self.context.get("estimated_length", 500)
        
        prompt = await self.build_prompt(
            self.PROMPT_TEMPLATE,
            angle=angle,
            chapter_purpose=chapter_purpose,
            chapter_content=chapter_content,
            style_guide=style_guide,
            previous_chapter=previous_chapter,
            estimated_length=estimated_length,
            chapter_key_points=chapter_key_points,
            content_elements=content_elements,
            selected_angle=selected_angle
        )
        return [{'role': 'user', 'content': prompt}]

    async def process_response(self, response: AsyncGenerator[Tuple[str, str], None]) -> AsyncGenerator[Tuple[str, str], None]:
        async for role, content in response:
            yield role, content
        yield 'assistant', '章节内容生成完成'

    async def post_process(self) -> None:
        pass

    async def parse_response(self, response: str) -> Dict[str, Any]:
        pass