"""使用 LLM 服务管理器的搜索引擎实现"""

import asyncio
import json
from abc import ABC
from typing import List, Optional, Dict, Any

from services.llm.manager.llm_service_manager import llm_service_manager
from .search_engine import SearchEngine, SearchResult, SearchReference


class VolcBotSearchEngine(SearchEngine, ABC):
    """基于 LLM 服务的搜索引擎实现"""

    def __init__(
            self,
            model: str = "Volcengine/search-bot"
    ):
        """初始化搜索引擎

        Args:
            model: 使用的模型名称
        """
        super().__init__()
        self._model = model
        result = llm_service_manager.get_client(model)
        client, config = result
        self._client = client
        self._model_id = config.model_id

    def search(self, queries: List[str]) -> List[SearchResult]:
        """同步搜索

        Args:
            queries: 搜索查询列表

        Returns:
            List[SearchResult]: 搜索结果列表
        """
        return asyncio.run(self.asearch(queries=queries))

    async def asearch(self, queries: List[str]) -> List[SearchResult]:
        """异步搜索

        Args:
            queries: 搜索查询列表

        Returns:
            List[SearchResult]: 搜索结果列表
        """
        tasks = [self._single_search(query) for query in queries]
        task_results = await asyncio.gather(*tasks)
        return [result for result in task_results if result is not None]

    async def _single_search(self, query: str) -> Optional[SearchResult]:
        """执行单个查询

        Args:
            query: 查询字符串

        Returns:
            Optional[SearchResult]: 搜索结果，如果失败则返回 None
        """
        try:
            response = await self._run_search(query)
            return self._format_result(response, query)
        except Exception as e:
            print(f"搜索失败: {str(e)}")
            return None

    async def _run_search(self, query: str) -> Dict[str, Any]:
        """执行搜索请求

        Args:
            query: 查询字符串

        Returns:
            Dict[str, Any]: API 响应数据
        """
        return await self._client.chat(
            messages=[{
                "role": "user",
                "content": query
            }],
            model=self._model_id
        )

    @classmethod
    def _format_result(cls, response: Dict[str, Any], query: str) -> SearchResult:
        """格式化 API 响应为搜索结果

        Args:
            response: API 响应数据
            query: 原始查询字符串

        Returns:
            SearchResult: 格式化后的搜索结果
        """
        # 从响应中提取内容
        content = response["choices"][0]["message"]["content"]
        
        # 尝试从响应中提取参考信息
        references = []
        if "references" in response:
            for ref in response["references"]:
                references.append(SearchReference(
                    site=ref.get("site_name", ""),
                    url=ref.get("url", ""),
                    content=ref.get("summary", ""),
                    title=ref.get("title", "")
                ))

        return SearchResult(
            query=query,
            summary_content=content,
            search_references=references
        ) 