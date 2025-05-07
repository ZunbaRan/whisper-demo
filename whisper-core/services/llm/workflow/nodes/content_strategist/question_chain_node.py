import asyncio
import os
import uuid
from typing import List, Tuple, AsyncGenerator

from services.llm.article_agent.content_strategist.patterns import PatternsAgent
from services.llm.article_agent.content_strategist.question_chain_agent import QuestionChainAgent
from services.llm.workflow.base.node import Node
from services.llm.workflow.base.output_manager import OutputManager


class Question_Chain_Node(Node):

    def __init__(self, tid: str = uuid.uuid4(), name: str = "question_chain_node"):
        # node初始化的 PatternsAgent 其实没用
        super().__init__(name, PatternsAgent(), tid)
        self.output_manager = OutputManager("public/output")

    async def process_single_article(self, article):
        """处理单篇文章"""
        self.agent.context = {
            "content": article["content"]
        }
        agent = QuestionChainAgent()
        async for result in agent.call(content=article["content"]):
            pass

        return agent.response_stream, agent.context["format_res"]

    async def call(self) -> AsyncGenerator[Tuple[str, str], None]:
        """分析每篇文章的主题"""
        analysis_results = []
        tasks = []
        for article in self.context["articles"]:
            task = self.process_single_article(article)
            tasks.append(task)

        # 并发执行所有文章处理任务
        results = await asyncio.gather(*tasks)
        for article_results, format_res in results:
            if format_res:
                analysis_results.append(format_res)
            for result in article_results:
                yield result

        # 保存所有分析结果
        self.outputs = {
            "question_chain_results": analysis_results
        }

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
        articles = articles[:3]
        self.context = {
            "articles": articles
        }


    async def process_output(self, results: List[Tuple[str, str]]) -> None:
        pass
