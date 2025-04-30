import uuid
from typing import AsyncGenerator, Tuple, List

from services.llm.article_agent.author_style_analyzer.style_guide_generator_agent import StyleGuideGenerator
import json

from services.llm.workflow.base.node import Node
from services.llm.workflow.base.output_manager import OutputManager


class StyleGuideNode(Node):
    """风格指南生成节点"""

    def __init__(self, tid: str = uuid.uuid4(), name: str = "style_guide"):
        super().__init__(name, StyleGuideGenerator(), tid)
        self.output_manager = OutputManager("public/output")

    async def prepare_context(self) -> None:
        """准备上下文数据"""
        # 获取所有文章分析结果
        analyses = self.inputs.get("analyses", '')
        # 提取字符串中所有 ```json 和 ``` 之间内容，并且转换为 list[Dict[str, Any]]
        json_blocks = []
        start_index = 0
        while True:
            start = analyses.find('```json', start_index)
            if start == -1:
                break
            start += len('```json')
            end = analyses.find('```', start)
            if end == -1:
                break
            json_str = analyses[start:end].strip()
            try:
                json_data = json.loads(json_str)
                json_blocks.append(json_data)
            except json.JSONDecodeError:
                print(f"无法解析 JSON 数据: {json_str}")
            start_index = end + len('```')

        self.context = {
            "content": json_blocks,
            "author_name": self.inputs.get("author_name", "unknown")
        }

    async def call(self) -> AsyncGenerator[tuple[str, str], None]:
        """生成风格指南"""
        async for result in self.agent.call(**self.context):
            yield result

    async def process_output(self, results: List[Tuple[str, str]]) -> None:
        # 把 processed_results 持久化到文件
        self.output_manager = OutputManager()
        # 提取元组集合中所有的 content 部分, 并直接拼接为一个str
        content_list = [result[1] for result in results]
        content_str = "".join(content_list)  # 使用空字符串拼接
        print(f"风格指南生成结果: {content_str}")

        self.output_manager.save_str_file("style_guide", content_str)
        """处理输出数据"""
        self.outputs = {
            "style_guide": content_str
        }
