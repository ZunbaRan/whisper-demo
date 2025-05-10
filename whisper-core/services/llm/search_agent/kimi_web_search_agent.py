import logging
from typing import Dict, Any, List, Union, AsyncGenerator, Tuple
import json

from services.llm.agent.base_agent import BaseAgent
from services.llm.search_agent.search_res import SearchRes
from services.llm.utils.format_json import FormatJson

logger = logging.getLogger(__name__)

class KimiWebSearchAgent(BaseAgent):
    """使用 Kimi 进行联网搜索的 Agent"""

    def __init__(self):
        super().__init__(model_name="Kimi/kimi-latest")
        self.PROMPT_TEMPLATE = None

    async def pre_process(self) -> None:
        """预处理，设置搜索工具配置"""
        # Kimi 的搜索工具配置已经在 stream_chat 中通过 tools 参数设置
        tools = [
            {
                "type": "builtin_function",
                "function": {
                    "name": "$web_search",
                },
            }
        ]
        # 新建tools dict
        tools_dict = {'tools': tools,
                      "response_format": {"type": "json_object"},
                      'max_tokens': 1024*30}

        self.context["config"] = tools_dict
        

    async def build_messages(self) -> List[Dict[str, str]]:
        """构建消息列表

        Returns:
            List[Dict[str, str]]: 消息列表
        """
        query = self.context.get("query")
        messages = [
            {
                "role": "system",
                "content": """
                你是一个专业的搜索助手。请根据用户的查询，搜索获取相关信息，并以清晰、准确的方式呈现搜索结果
                **重要**：尽可能多获取一些结果
                输出格式：你需要以json的格式返回所有查询的结果
                包含以下字段：
                - query: 搜索的原问题
                - summary_content: 根据搜索结果的内容，总结出的主要信息
                - search_references: 字符串数组，包含每个搜索结果的URL
                    - site: 站点名/来源媒体
                    - url: 搜索结果引用链接
                    - content: 该网站中找到的匹配搜索结果的内容，尽可能的把相关内容都展示出来
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
    #     """处理响应流
    #
    #     Args:
    #         response: 响应流
    #
    #     Yields:
    #         Tuple[str, str]: (内容类型, 内容)
    #     """
    #     res_content = ''
    #     async for role, content in response:
    #         if role == 'content':
    #             res_content += content
    #             yield role, content
    #         elif role == 'reasoning':
    #             # 处理工具调用响应
    #             try:
    #                 tool_data = json.loads(content)
    #                 if tool_data.get('name') == '$web_search':
    #                     # 将搜索参数作为内容返回
    #                     yield 'content', json.dumps(tool_data['args'])
    #             except json.JSONDecodeError:
    #                 pass
    #     self.context["res_content"] = res_content



    async def parse_response(self, response: str) ->  str | SearchRes:
        """解析响应

            Args:
                response: 响应内容

        Returns:
            Union[dict, list, str, int, float, bool, None, SearchRes]: 解析后的结果
        """
        try:
            # 尝试将响应解析为 JSON SearchRes
            res:Dict = await FormatJson.llm_parse(response)
            search_res = SearchRes(**res)
            return search_res
        except json.JSONDecodeError:
            logger.error(f"解析响应失败: {response}")
            # 如果解析失败，返回原始响应
            return response

