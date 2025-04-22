import json
from typing import AsyncGenerator, Dict, Any, List, Tuple

from services.llm.agent.base_agent import BaseAgent, logger


class StyleInfusionAgent(BaseAgent):
    """风格注入Agent，负责按章节撰写文章并注入特定风格"""

    PROMPT_TEMPLATE = """角色: 你是一位熟练的作家，负责以特定风格起草文章的一个章节。
背景:
- 文章角度: {angle}
- 本章目标: {chapter_purpose}
- 本章关键内容: {chapter_content}
- 作者风格指南: {style_guide}
- 前一章节内容: {previous_chapter}

任务: 撰写文章的这一章节（大约 {estimated_length} 字）。
要求:
1. 使用提供的关键内容达成章节目标
2. 严格遵守风格指南中关于语气、句式结构、词汇和修辞手法的规定
3. 如果提供了前一章节的文本，请确保过渡平滑
4. 保持文章的整体连贯性和可读性

输出格式: 请以JSON格式返回结果，包含以下字段：
- content: 章节内容
- word_count: 实际字数
- style_compliance: 风格符合度评估（1-10分）"""

    async def pre_process(self) -> None:
        pass

    async def build_messages(self) -> List[Dict[str, str]]:
        # 从context中获取所需信息
        angle = self.context.get("angle", "")
        chapter_purpose = self.context.get("chapter_purpose", "")
        chapter_content = self.context.get("chapter_content", "")
        style_guide = self.context.get("style_guide", "")
        previous_chapter = self.context.get("previous_chapter", "")
        estimated_length = self.context.get("estimated_length", 500)
        
        prompt = await self.build_prompt(
            self.PROMPT_TEMPLATE,
            angle=angle,
            chapter_purpose=chapter_purpose,
            chapter_content=chapter_content,
            style_guide=style_guide,
            previous_chapter=previous_chapter,
            estimated_length=estimated_length
        )
        return [{'role': 'user', 'content': prompt}]

    async def process_response(self, response: AsyncGenerator[Tuple[str, str], None]) -> AsyncGenerator[Tuple[str, str], None]:
        async for role, content in response:
            yield role, content
        yield 'assistant', '章节内容生成完成'

    async def post_process(self) -> None:
        pass

    async def parse_response(self, response: str) -> Dict[str, Any]:
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"解析JSON响应失败: {str(e)}")
            return {
                "content": "",
                "word_count": 0,
                "style_compliance": 0
            } 