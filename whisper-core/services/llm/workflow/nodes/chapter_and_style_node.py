import json
from typing import List, Tuple, AsyncGenerator, Dict, Any

from services.article_agent.structured_draft.style_infusion_agent import ChapterAndStyleAgent
from services.llm.workflow.node import Node


class ChapterAndStyleNode(Node):
    async def call(self) -> AsyncGenerator[Tuple[str, str], None]:
        sections = self.inputs.get("sections")
        previous_chapter = ""  # 初始化前一章节内容

        for section in sections["sections"]:
            """角度钩选策略"""

            self.context = {
                "selected_angle": self.context["selected_angle"],
                "style_guide": self.context["style_guide"],
                "chapter_purpose": section["chapter_purpose"],
                "chapter_key_points": section["chapter_key_points"],
                "content_elements": section["content_elements"],
                "estimated_length": section["estimated_length"],
                "previous_chapter": previous_chapter
            }

            async for result in self.agent.call(**self.context):
                yield result

                if result[0] == 'assistant':  # 假设助手返回的结果是章节内容
                    previous_chapter += result[1]  # 收集当前章节内容作为下一章节的前一章节

    async def prepare_context(self) -> None:

        style_guide = self.inputs.get("style_guide")
        angles = self.inputs.get("angles")
        # 选取第一个角度作为示例
        angle = angles[0]

        self.context = {
            "style_guide": style_guide,
            "selected_angle": json.dumps(angle, ensure_ascii=False)
        }

    async def process_output(self, results: List[Tuple[str, str]]) -> None:
        content_list = [result[1] for result in results]
        content_str = "".join(content_list)  # 使用空字符串拼接
        print(f"章节创作结果: {content_str}")

        """处理输出数据"""
        self.outputs = {
            "draft": content_str
        }

    def __init__(self, name: str = "chapter_and_style"):
        super().__init__(name, ChapterAndStyleAgent())
