import logging
from typing import Dict, Any, List, Union, AsyncGenerator, Tuple
import json

from services.llm.agent.base_agent import BaseAgent
from services.llm.search_agent.search_res import SearchRes
from services.llm.utils.format_json import FormatJson

logger = logging.getLogger(__name__)

class KimiInformationSearchAgent(BaseAgent):
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
                "role": "user",
                "content": query
            }
        ]
        return messages

    async def parse_response(self, response: str) ->  str | SearchRes:
        return response

