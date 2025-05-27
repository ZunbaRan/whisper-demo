import json
import uuid
from typing import List, Tuple, AsyncGenerator

from services.llm.article_agent.structured_draft.structured_draft_agent import StructuredDraftAgent
from services.llm.workflow.base.node import Node


class StructuredDraftNode(Node):
    async def call(self) -> AsyncGenerator[Tuple[str, str], None]:
        """结构化草稿Agent"""
        async for result in self.agent.call(**self.context):
            yield result

    async def prepare_context(self) -> None:

        # angles = self.inputs.get("angles")
        # # 选取第一个角度作为示例
        # angle = angles[0]

        theme_result = self.inputs.get("theme_result")
        main_theme = theme_result.get("main_theme")
        thesis = theme_result.get("thesis")
        sub_topics:[] = theme_result.get("sub_topics")
        sub_topics_str = "\n".join(sub_topics)

        theme = f"""中心主题: {main_theme}\n 主要论点: {thesis} \n 子主题: {sub_topics_str} """


        structure_outline = self.inputs.get("structure_outline")
        # structure_outline 是字符串数组， 拼接为一个长字符串
        structure_outline = "\n".join(structure_outline)

        elements_info = self.inputs.get("elements_info")
        # - golden_quotes: 金句列表（字符串数组）
        # - actionable_advice: 可行动建议列表（字符串数组）
        # - examples: 例证列表（对象数组，每个对象包含summary和illustrates字段）
        # - data_points: 关键数据列表（字符串数组）"""

        # 处理elements_info
        elements = ""
        if elements_info:
            # 处理金句
            golden_quotes = elements_info.get("golden_quotes", [])
            if golden_quotes:
                golden_quotes_str = "\n".join(golden_quotes)
                elements += f"\n金句列表: {golden_quotes_str}"
            # 处理可行动建议
            actionable_advice = elements_info.get("actionable_advice", [])
            if actionable_advice:
                actionable_advice_str = "\n".join(actionable_advice)
                elements += f"\n可行动建议: {actionable_advice_str}"
            # 处理例证
            examples = elements_info.get("examples", [])
            if examples:
                examples_str = "\n".join([f"Summary: {example.get('summary', '')}\nIllustrates: {example.get('illustrates', '')}" for example in examples])
                elements += f"\n例证列表: {examples_str}"
            # 处理关键数据
            data_points = elements_info.get("data_points", [])
            if data_points:
                data_points_str = "\n".join(data_points)
                elements += f"\n关键数据列表: {data_points_str}"

        self.context = {
            # "selected_angle": json.dumps(angle, ensure_ascii=False),
            "theme_result": theme,
            "structure_outline": structure_outline,
            "elements_info": elements
        }


    async def process_output(self, results: List[Tuple[str, str]]) -> None:
        # 提取元组集合中所有的 content 部分, 并直接拼接为一个str
        content_list = [result[1] for result in results]
        content_str = "".join(content_list)  # 使用空字符串拼接
        sections = await self.agent.parse_response(content_str)
        """处理输出数据"""
        self.outputs = {
            "sections": sections
        }

        print("结构化草稿结果node执行完毕")

    def __init__(self, tid: str = uuid.uuid4(), name: str = "structured_draft"):
        super().__init__(name, StructuredDraftAgent(), tid)
