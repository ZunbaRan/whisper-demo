from typing import AsyncGenerator
import json
import logging

from services.llm.article_agent.podcast_deconstructor.elements_extraction_agent import ElementsExtractionAgent
from services.llm.article_agent.podcast_deconstructor.structure_analysis_agent import StructureAnalysisAgent
from services.llm.article_agent.podcast_deconstructor.theme_analysis_agent import ThemeAnalysisAgent

logger = logging.getLogger(__name__)

class PodcastDeconstructors:
    """播客解构协调器"""

    def __init__(self):
        self.theme_agent = ThemeAnalysisAgent()
        self.elements_agent = ElementsExtractionAgent()
        self.structure_agent = StructureAnalysisAgent()

    async def process_podcast(self, content: str) -> AsyncGenerator[str, None]:
        try:
            # 1. 主题分析
            async for result in self.theme_agent.call(content=content):
                yield result
            theme_result = await self.theme_agent.get_step_output("theme_analysis")

            # 2. 元素提取
            async for result in self.elements_agent.call(
                    content=content,
                    theme_result=theme_result
            ):
                yield result
            elements_result = await self.elements_agent.get_step_output("elements_extraction")

            # 3. 结构分析
            async for result in self.structure_agent.call(
                    theme_result=theme_result,
                    elements_result=elements_result
            ):
                yield result
            structure_result = await self.structure_agent.get_step_output("structure_analysis")

            # 4. 生成最终结果
            final_result = {
                # 来自主题分析
                "main_theme": theme_result.get("main_theme", ""),
                "thesis": theme_result.get("thesis", ""),
                "sub_topics": theme_result.get("sub_topics", []),

                # 来自关键元素提取
                "golden_quotes": elements_result.get("golden_quotes", []),
                "actionable_advice": elements_result.get("actionable_advice", []),
                "examples": elements_result.get("examples", []),
                "data_points": elements_result.get("data_points", []),

                # 来自结构分析
                "structure_outline": structure_result.get("structure_outline", [])
            }

            # 输出最终结果
            for key, value in final_result.items():
                response_data = {
                    "role": "assistant",
                    "content": f"{key}: {json.dumps(value, ensure_ascii=False)}"
                }
                yield f"data: {json.dumps(response_data, ensure_ascii=False)}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            error_msg = f"处理播客内容时发生错误: {str(e)}"
            logger.error(error_msg)
            yield f"data: {json.dumps({'role': 'error', 'content': error_msg}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
