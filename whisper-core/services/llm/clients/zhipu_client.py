from typing import Optional, Any, AsyncGenerator

from zhipuai import ZhipuAI
from zhipuai.types.web_search.web_search_resp import WebSearchResp

from services.llm.clients.base_client import BaseClient
from services.llm.search_agent.search_res import SearchRes, References


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

    async def web_search_api(self, search_query: str, search_engine: str) -> SearchRes:
        res: WebSearchResp = self.client.web_search.web_search(
            search_engine=search_engine,
            search_query=search_query
        )

        search_references_list = []

        search_intent = res.search_intent[0]
        summary_content_str = getattr(search_intent, 'keywords', "") + "\n" + getattr(search_intent, 'intent', "")

        if res and res.search_result:
            zhipu_result = res.search_result
            
            for part_result in zhipu_result:

                reference = References(
                    title=getattr(part_result, 'title', ""),
                    url=getattr(part_result, 'link', ""),
                    content=getattr(part_result, 'content', ""),
                    site=getattr(part_result, 'media', "")
                )
                search_references_list.append(reference)
        
        search_res = SearchRes(
            query=search_query,
            summary_content=summary_content_str,
            search_references=search_references_list
        )
        return search_res
