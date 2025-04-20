from typing import Dict, Any, AsyncGenerator
from ..node import Node
import json
from services.article_agent.author_style_analyzer import StyleGuideGenerator

class StyleGuideNode(Node):
    """风格指南生成节点"""
    
    def __init__(self, name: str = "style_guide"):
        super().__init__(name, StyleGuideGenerator())
        
    async def prepare_context(self) -> None:
        """准备上下文数据"""
        # 获取所有文章分析结果
        analyses =  self.inputs.get("analysis", [])
                
        self.context = {
            "content": json.dumps(analyses, ensure_ascii=False, indent=2),
            "author_name": self.inputs.get("author_name", "unknown")
        }
        
    async def call(self) -> AsyncGenerator[tuple[str, str], None]:
        """生成风格指南"""
        async for result in self.agent.call(**self.context):
            yield result
            
    async def process_output(self, processed_results: str) -> None:
        """处理输出数据"""
        self.outputs = {
            "style_guide": processed_results
        }