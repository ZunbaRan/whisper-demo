import uuid
from typing import AsyncGenerator, Tuple, List
import os

from services.article_agent.article_theme_analyze.one_theme_ana import OneThemeAnalyzer
from services.llm.workflow.base.node import Node
from services.llm.workflow.base.output_manager import OutputManager


class OneThemeNode(Node):
    """单篇文章主题分析节点"""

    def __init__(self, tid: str = uuid.uuid4(), name: str = "one_theme"):
        super().__init__(name, OneThemeAnalyzer(), tid)
        self.output_manager = OutputManager("public/output")

    async def prepare_context(self) -> None:
        """准备上下文数据"""
        # 获取文章目录
        articles_dir = self.inputs.get("articles_dir", "")
        if not os.path.exists(articles_dir):
            raise FileNotFoundError(f"目录不存在: {articles_dir}")

        # 读取目录下所有文件
        articles = []
        for filename in os.listdir(articles_dir):
            if filename.endswith('.md'):
                file_path = os.path.join(articles_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    articles.append({
                        "filename": filename,
                        "content": content
                    })

        # 测试直接去前两个文件
        # articles = articles[:1]
        self.context = {
            "articles": articles
        }

    async def call(self) -> AsyncGenerator[tuple[str, str], None]:
        """分析每篇文章的主题"""
        analysis_results = []
        for article in self.context["articles"]:
            # 设置当前文章内容
            self.agent.context = {
                "content": article["content"]
            }

            # 保存当前文章的文件名
            one_result: str = ''
            # 调用agent分析
            async for result in self.agent.call(content=article["content"]):
                if result[0] == "assistant":
                    yield result
                    # 保存分析结果
                    one_result += result[1]
                    if result[1] == "done":
                        json_result = await self.agent.parse_response(one_result)
                        analysis_results.append(json_result)

        # 保存所有分析结果
        self.outputs = {
            "analysis_results": analysis_results
        }

    async def process_output(self, results: List[Tuple[str, str]]) -> None:
        """处理输出数据"""
        # 提取所有分析结果
        # content_list = [result[1] for result in results]
        # content_str = "".join(content_list)
        #
        # # 保存到文件
        # self.output_manager.save_str_file("theme_analysis", content_str)
        pass
