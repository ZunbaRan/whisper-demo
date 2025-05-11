import json
from typing import Dict, Any, List, Union, AsyncGenerator, Tuple

from google.genai.types import GenerateContentConfig, GoogleSearch, Tool

from services.llm.agent.base_agent import BaseAgent
from services.llm.search_agent.search_res import SearchRes
from services.llm.utils.format_json import FormatJson


class GeminiWebSearchAgent(BaseAgent):
    """使用 Gemini 进行联网搜索的 Agent"""

    def __init__(self):
        super().__init__(model_name="Gemini/gemini-2.5-flash")
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
                ## role: 你是一个专业的搜索助手。请根据用户的查询，使用Google搜索获取相关信息，并以清晰、准确的方式呈现搜索结果。
                ## 输出格式：你需要以json的格式返回所有查询的结果
                ## 注意!!!:只需要输出 json 格式的响应，不需要其他任何内容和标签，尤其是类似于 ```json 这种markdown标签
                每个结果包含以下字段：
                - query: 搜索的原问题
                - summary_content: 根据搜索结果的内容，总结出的主要信息
                - search_references: 字符串数组，包含搜索结果的URL
                    - site: 站点名/来源媒体
                    - url: 搜索结果引用的网址
                    - content: 在该网站中找到的匹配搜索结果的内容
                    - title: 该网站中找到的匹配搜索结果的标题
                """
            },
            {
                "role": "user",
                "content": f"请搜索以下内容并返回相关信息：{query}"
            }
        ]
        return messages

    # async def process_response(self, response: AsyncGenerator[Tuple[str, str], None]) -> AsyncGenerator[Tuple[str, str], None]:
    #     res_content = ''
    #     parts = ''
    #     async for role, content in response:
    #         if role == 'content':
    #             res_content += content
    #         if role == 'parts':
    #             parts += content
    #         yield role, content
    #     self.context["res_content"] = res_content
    #     self.context["parts"] = parts


    async def parse_response(self, response: str) ->  str | SearchRes:
        """解析响应

            Args:
                response: 响应内容

        Returns:
            Union[dict, list, str, int, float, bool, None, SearchRes]: 解析后的结果
        """
        try:
            # 尝试将响应解析为 JSON SearchRes
            res: Dict = await FormatJson.llm_parse(response)
            search_res = SearchRes(**res)
            return search_res
        except json.JSONDecodeError:
            # 如果解析失败，返回原始响应
            return response
