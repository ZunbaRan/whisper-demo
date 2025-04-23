import json
from typing import List, Tuple, AsyncGenerator

from services.article_agent.structured_draft.structured_draft_agent import StructuredDraftAgent
from services.llm.workflow.node import Node


class StructuredDraftNode(Node):
    async def call(self) -> AsyncGenerator[Tuple[str, str], None]:
        """角度钩选策略"""
        async for result in self.agent.call(**self.context):
            yield result

    async def prepare_context(self) -> None:

        angles = self.inputs.get("angles")
        # 选取第一个角度作为示例
        angle = angles[0]

        theme_result = self.inputs.get("theme_result")
        main_theme = theme_result.get("main_theme")
        thesis = theme_result.get("thesis")

        structure_outline = self.inputs.get("structure_outline")
        # structure_outline 是字符串数组， 拼接为一个长字符串
        structure_outline = "\n".join(structure_outline)

        theme = f"""中心主题: {main_theme}\n 主要论点: {thesis} """

        self.context = {
            "selected_angle": json.dumps(angle, ensure_ascii=False),
            "theme_result": theme,
            "structure_outline": structure_outline
        }

        pass

    async def process_output(self, results: List[Tuple[str, str]]) -> None:
        pass

    def __init__(self, name: str = "structured_draft"):
        super().__init__(name, StructuredDraftAgent())
