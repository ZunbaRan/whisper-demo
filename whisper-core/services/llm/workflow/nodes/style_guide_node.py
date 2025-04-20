from typing import Dict, Any, AsyncGenerator, Tuple, List
from ..node import Node
import json
from services.article_agent.author_style_analyzer import StyleGuideGenerator
from services.llm.workflow.output_manager import OutputManager

class StyleGuideNode(Node):
    """风格指南生成节点"""
    
    def __init__(self, name: str = "style_guide"):
        super().__init__(name, StyleGuideGenerator())
        self.output_manager = OutputManager()
        
    async def prepare_context(self) -> None:
        """准备上下文数据"""
        # 获取所有文章分析结果
        analyses =  self.inputs.get("analyses", '')
                
        self.context = {
            "content": analyses,
            "author_name": self.inputs.get("author_name", "unknown")
        }
        
    async def call(self) -> AsyncGenerator[tuple[str, str], None]:
        """生成风格指南"""
        async for result in self.agent.call(**self.context):
            yield result
            
    async def process_output(self, processed_results: List[Tuple[str, str]]) -> None:
        # 把 processed_results 持久化到文件
        self.output_manager = OutputManager()
        # 提取元组集合中所有的 content 部分, 并直接拼接为一个str
        content_list = [result[1] for result in processed_results]
        content_str = "".join(content_list)  # 使用空字符串拼接
        print(f"风格指南生成结果: {content_str}")

        self.output_manager.save_str_file("style_guide", content_str)
        """处理输出数据"""
        self.outputs = {
            "style_guide": processed_results
        }