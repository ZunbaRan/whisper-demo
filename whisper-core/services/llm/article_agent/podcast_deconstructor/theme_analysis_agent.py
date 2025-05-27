import json
from typing import AsyncGenerator, List, Dict, Any, Tuple

from google.genai.types import GenerateContentConfig
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel

from services.llm.agent.base_agent import BaseAgent, logger

class ThemeAnalysisRes(BaseModel):
    topic_domain: str
    main_theme: str
    thesis: str
    sub_topics: List[str]

class ThemeAnalysisAgent(BaseAgent):
    """主题分析Agent"""

    PROMPT_TEMPLATE = """角色: 你是一位专注于总结口语内容的专家级分析师。
背景: 以下是一期播客的文字稿。
文字稿: "{text}"
任务: 分析提供的文字稿，并识别：
1. 该播客内容属于什么领域
1. 讨论的中心主题或主要议题。
2. 发言者提出的主要论点或主张。
3. 涵盖的关键子主题。
输出格式: 请以JSON格式返回结果，包含以下字段：
- topic_domain: 领域（字符串）
- main_theme: 中心主题（字符串）
- thesis: 主要论点（字符串）
- sub_topics: 子主题列表（字符串数组）"""

    async def pre_process(self) -> None:
        config = GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ThemeAnalysisRes
        )
        self.context["config"] = config


    async def build_messages(self) -> List[Dict[str, str]]:
        content = self.context["content"]
        prompt = await self.build_prompt(self.PROMPT_TEMPLATE, text=content)
        return [{'role': 'user', 'content': prompt}]


    async def parse_response(self, response: str) -> Dict:
        parser = JsonOutputParser()
        return parser.parse(response)