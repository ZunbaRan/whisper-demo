import json
from typing import List, Tuple, AsyncGenerator

from services.article_agent.angle_hook_strategist import AngleHookStrategist
from services.llm.workflow.node import Node


class AngleHookStrategistNode(Node):
    """角度钩选策略节点"""

    async def call(self) -> AsyncGenerator[Tuple[str, str], None]:
        """角度钩选策略"""
        async for result in self.agent.call(**self.context):
            yield result

    async def prepare_context(self) -> None:
        theme_result = self.inputs.get("theme_result")
        elements_info = self.inputs.get("elements_info")

        self.context = {
            "main_theme": theme_result.get("main_theme", ""),
            "thesis": theme_result.get("thesis", ""),
            "golden_quotes": elements_info.get("golden_quotes", []),
            "examples": elements_info.get("examples", [])
        }

    async def process_output(self, results: List[Tuple[str, str]]) -> None:
        # - angle: 角度 / 引子陈述（字符串）
        # - resonance: 受众共鸣点（字符串）
        # - connection: 内容链接（字符串）
        # - emotional_integration: 共鸣情感元素整合策略（字符串）"""
        content_list = [result[1] for result in results]
        content_str = "".join(content_list)  # 使用空字符串拼接
        print(f"角度钩选策略结果: {content_str}")

        angles = await self.agent.parse_response(content_str)
        self.outputs = {
            "angles": angles
        }

    def __init__(self, name: str = "angle_hook_strategist"):
        super().__init__(name, AngleHookStrategist())
