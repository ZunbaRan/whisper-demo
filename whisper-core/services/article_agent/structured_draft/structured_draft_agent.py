import json
from typing import AsyncGenerator, Dict, Any, List, Tuple

from services.llm.agent.base_agent import BaseAgent, logger


class StructuredDraftAgent(BaseAgent):
    """结构化草稿Agent，负责创建详细的文章大纲"""

    PROMPT_TEMPLATE = """角色: 你是一位经验丰富的文章结构规划师，负责创建详细且连贯的文章大纲。
背景: 
- 播客主题: {theme_result}
- 选定角度: {selected_angle}
- 播客结构大纲: {structure_outline}

任务: 基于以上信息，创建一个详细的文章大纲，要求：
1. 保持原有结构的逻辑性
2. 在适当位置整合关键引言、示例和数据点
3. 确保每个部分都有明确的目的和内容要点
4. 考虑文章的整体流畅性和过渡

输出格式: 请以JSON格式返回结果，包含以下字段：
- sections: 章节列表，每个章节包含：
  - chapter_title: 章节标题
  - chapter_purpose: 章节目的
  - chapter_key_points: 关键要点列表
  - content_elements: 内容元素列表（包含引言、示例、数据等）
  - estimated_length: 预计字数"""

    async def pre_process(self) -> None:
        pass

    async def build_messages(self) -> List[Dict[str, str]]:
        # 从context中获取所需信息
        theme = self.context.get("theme", "")
        selected_angle = self.context.get("selected_angle", "")
        outline = self.context.get("outline", "")
        
        prompt = await self.build_prompt(
            self.PROMPT_TEMPLATE,
            theme=theme,
            angle=selected_angle,
            outline=outline
        )
        return [{'role': 'user', 'content': prompt}]

    async def process_response(self, response: AsyncGenerator[Tuple[str, str], None]) -> AsyncGenerator[Tuple[str, str], None]:
        async for role, content in response:
            yield role, content
        yield 'assistant', '详细大纲生成完成'

    async def post_process(self) -> None:
        pass

    async def parse_response(self, response: str) -> Dict[str, Any]:
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"解析JSON响应失败: {str(e)}")
            return {"sections": []} 