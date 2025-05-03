from typing import Optional, Any, AsyncGenerator

from zhipuai import ZhipuAI
from zhipuai.types.web_search.web_search_resp import WebSearchResp

from services.llm.clients.base_client import BaseClient


class ZhipuClient(BaseClient):
    def __init__(
            self,
            api_key: str,
            api_url: str,
            api_request_address: str,
            timeout: Optional[int] = None,
            proxy: Optional[str] = None,
            reasoner: bool = False,
    ):
        super().__init__(api_key, api_url, api_request_address, timeout, proxy, reasoner)
        self.client: ZhipuAI = ZhipuAI(api_key=api_key)

    def _patch_proxy(self, client, proxy: str) -> None:
        pass

    async def stream_chat(self, messages: list, model: str, config: Optional[Any] = None) -> AsyncGenerator[
        tuple[str, str], None]:
        pass

    async def web_search_api(self, search_query: str, search_engine: str) -> WebSearchResp:
        res = self.client.web_search.web_search(
            search_engine=search_engine,
            search_query=search_query
        )
        return res
