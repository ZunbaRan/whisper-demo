from typing import Dict, Any, AsyncGenerator, Tuple, List

from services.article_agent.article_theme_analyze.summary_theme_agent import SummaryThemeAgent
from services.llm.workflow.node import Node
from services.llm.workflow.output_manager import OutputManager

class SummaryThemeNode(Node):
    """主题总结节点"""
    
    def __init__(self, name: str = "summary_theme"):
        super().__init__(name, SummaryThemeAgent())
        self.output_manager = OutputManager("public/output")
        
    async def prepare_context(self) -> None:
        """准备上下文数据"""
        # 获取前一个节点的分析结果
        analysis_results = self.inputs.get("analysis_results", [])
        
        self.context = {
            "analysis_results": analysis_results
        }
        
    async def call(self) -> AsyncGenerator[tuple[str, str], None]:
        """生成主题总结"""
        async for result in self.agent.call(**self.context):
            yield result
            
    async def process_output(self, results: List[Tuple[str, str]]) -> None:
        """处理输出数据"""
        # 提取所有内容
        content_list = [result[1] for result in results]
        content_str = "".join(content_list)
        
        # 保存到文件
        self.output_manager.save_str_file("theme_summary", content_str)
        
        # 设置输出
        self.outputs = {
            "summary_result": content_str
        } 