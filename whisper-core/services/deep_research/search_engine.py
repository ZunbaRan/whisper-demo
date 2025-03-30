"""搜索引擎基类定义"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SearchReference:
    """搜索结果的参考来源"""
    site: str
    url: str
    content: str
    title: str


@dataclass
class SearchResult:
    """搜索结果"""
    query: str
    summary_content: str
    search_references: List[SearchReference]


class SearchEngine(ABC):
    """搜索引擎基类"""

    def __init__(self):
        """初始化搜索引擎"""
        pass

    @abstractmethod
    def search(self, queries: List[str]) -> List[SearchResult]:
        """同步搜索方法

        Args:
            queries: 搜索查询列表

        Returns:
            List[SearchResult]: 搜索结果列表
        """
        pass

    @abstractmethod
    async def asearch(self, queries: List[str]) -> List[SearchResult]:
        """异步搜索方法

        Args:
            queries: 搜索查询列表

        Returns:
            List[SearchResult]: 搜索结果列表
        """
        pass 