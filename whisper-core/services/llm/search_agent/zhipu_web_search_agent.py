from typing import Dict, Any, List, Union, AsyncGenerator, Tuple, Optional
import json

from services.llm.agent.base_agent import BaseAgent
from services.llm.manager.llm_service_manager import llm_service_manager


class ZhipuWebSearchAgent(BaseAgent):
    """使用智谱AI进行联网搜索的 Agent"""

    def __init__(self, search_engine):
        super().__init__(model_name="GLM/GLM-4-Air-250414")
        self.model_name = "GLM/GLM-4-Air-250414"
        self.search_engine = search_engine
        self.PROMPT_TEMPLATE = None

    async def build_messages(self) -> List[Dict[str, str]]:
        pass

    async def parse_response(self, response: str) -> Union[dict, list, str, int, float, bool, None, Any]:
        pass

    async def call(
            self,
            content: Optional[str] = None,
            files: Optional[List[Dict[str, str]]] = None,
            **kwargs
    ) -> AsyncGenerator[Tuple[str, str], None]:
        """Agent的主要调用方法，针对智谱AI的特定实现

        Args:
            content: 主要输入内容
            files: 可选的文件列表，每个文件是一个字典，包含文件路径和内容
            **kwargs: 其他参数

        Yields:
            Tuple[str, str]: (role, content) 元组
        """

        client, model_config = llm_service_manager.get_client(model_name=self.model_name)
        # 获取到的client是ZhipuClient
        res = await client.web_search_api(search_engine=self.search_engine,
                                          search_query=content)
        self.format_res = res
        
        # print(res, end="", flush=True)
        
        yield "content", res

