"""LLM服务主入口"""

import asyncio
from typing import List, Dict, Optional, AsyncGenerator

from services.llm.manager.model_manager import ModelConfig, model_manager
from services.llm.clients.openai_compatible_client import OpenAICompatibleClient
from services.llm.clients.gemini_client import GeminiClient
from services.llm.utils.logger import logger


class LLMService:
    """LLM服务主类"""

    def __init__(self):
        """初始化LLM服务"""
        self.clients: Dict[str, OpenAICompatibleClient] = {}

    def _get_client(self, model_name: str) -> tuple[Optional[OpenAICompatibleClient], Optional[ModelConfig]]:
        """获取对应的客户端实例

        Args:
            model_name: 模型名称

        Returns:
            Optional[OpenAICompatibleClient]: 客户端实例，如果模型不存在则返回 None
        """
        try:
            reasoner = False
            # 获取模型配置
            config = model_manager.get_target_config(model_name)
            if not config:
                config = model_manager.get_reasoner_config(model_name)
                reasoner = True
                if not config:
                    logger.error(f"无法获取模型 {model_name} 的配置")
                    return None

            # 获取代理配置
            proxy_open, proxy_address = model_manager.get_proxy_config()
            proxy = proxy_address if proxy_open else None

            logger.info(f"proxy: {proxy}")
            logger.info(f"proxy_open: {proxy_open}")

            # 根据模型名称选择对应的客户端
            if model_name.startswith("Gemini/"):
                return GeminiClient(
                    api_key=config.api_key,
                    api_url=config.api_base_url,
                    api_request_address=config.api_request_address,
                    proxy=proxy,
                    reasoner=reasoner
                ), config
            else:
                # 默认使用 OpenAI 兼容客户端
                return OpenAICompatibleClient(
                    api_key=config.api_key,
                    api_url=config.api_base_url,
                    api_request_address=config.api_request_address,
                    proxy=proxy,
                    reasoner=reasoner
                ), config

        except Exception as e:
            logger.error(f"创建客户端失败: {e}")
            return None

    async def chat_stream(
        self,
        model_name: str,
        messages: List[Dict[str, str]]
    ) -> AsyncGenerator[tuple[str, str], None]:
        """执行流式对话

        Args:
            model_name: 模型名称
            messages: 对话消息列表

        Yields:
            tuple[str, str]: (role, content) 消息元组
        """
        client, config = self._get_client(model_name)
        if not client:
            raise ValueError(f"无法创建模型 {model_name} 的客户端")

        try:
            # 打印config
            logger.info(f"模型配置: {config}")
            logger.info(f"开始与 {model_name} 进行对话")
            async for role, content in client.stream_chat(
                messages=messages,
                model=config.model_id
            ):
                yield role, content

        except Exception as e:
            logger.error(f"对话过程中发生错误: {e}")
            raise
