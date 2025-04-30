from typing import Dict, Any, List, Union, AsyncGenerator, Tuple

from google.genai.types import GenerateContentConfig, GoogleSearch, Tool

from services.llm.agent.base_agent import BaseAgent


class GeminiWebSearchAgent(BaseAgent):
    """使用 Gemini 进行联网搜索的 Agent"""

    def __init__(self):
        super().__init__()
        self.PROMPT_TEMPLATE = None

    async def pre_process(self) -> None:
        google_search_tool = Tool(
            google_search=GoogleSearch()
        )

        # 配置 Google Search grounding
        config = GenerateContentConfig(
            tools=[google_search_tool],
            response_modalities=["TEXT"],
            # response_mime_type="application/json",
            # response_schema = list[SearchResult]
        )
        self.context["config"] = config

    async def build_messages(self) -> List[Dict[str, str]]:
        query = self.context.get("query")
        messages = [
            {
                "role": "system",
                "content": """
                你是一个专业的搜索助手。请根据用户的查询，使用Google搜索获取相关信息，并以清晰、准确的方式呈现搜索结果。
                输出格式：你需要以json数组的格式返回所有查询的结果
                每个结果包含以下字段：
                - query: 搜索的原问题
                - summary_content: 根据搜索结果的内容，总结出的主要信息
                - search_references: 字符串数组，包含搜索结果的URL
                    - site: 搜索结果引用的网站
                    - url: 搜索结果引用的网址
                    - content: 在该网站中找到的匹配搜索结果的内容总结
                    - title: 该网站中找到的匹配搜索结果的标题
                """
            },
            {
                "role": "user",
                "content": f"请搜索以下内容并返回相关信息：{query}"
            }
        ]
        return messages

    async def process_response(self, response: AsyncGenerator[Tuple[str, str], None]) -> AsyncGenerator[Tuple[str, str], None]:
        res_content = ''
        parts = ''
        async for role, content in response:
            if role == 'content':
                res_content += content
            if role == 'parts':
                parts += content
            yield role, content
        self.context["res_content"] = res_content
        self.context["parts"] = parts

    async def post_process(self) -> None:
        pass

    async def parse_response(self, response: str) -> Union[dict, list, str, int, float, bool, None]:
        pass
