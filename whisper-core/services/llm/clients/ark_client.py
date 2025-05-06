"""VolcEngine Ark 客户端类,使用 VolcEngine Ark API"""

from typing import AsyncGenerator, Optional, Dict, Any, List, Union
import os
from openai import AsyncStream
from volcenginesdkarkruntime import AsyncArk
from volcenginesdkarkruntime._exceptions import ArkAPIError
from volcenginesdkarkruntime.types.bot_chat import BotChatCompletion, BotChatCompletionChunk
from volcenginesdkarkruntime.types.bot_chat.bot_reference import Reference

from ..clients.base_client import BaseClient
from ..utils.logger import logger


class ArkClient(BaseClient):
    """VolcEngine Ark 客户端类

    使用 VolcEngine Ark API 实现对话功能
    """

    def __init__(
            self,
            api_key: str,
            api_url: str,
            api_request_address: str,
            timeout: Optional[int] = None,
            proxy: str = None,
            reasoner: bool = False,
    ):
        """初始化 VolcEngine Ark 客户端

        Args:
            api_key: API密钥
            api_url: API地址
            timeout: 请求超时设置,None则使用默认值
            proxy: 代理服务器地址(Ark客户端不需要代理)
        """
        super().__init__(api_key, api_url, api_request_address, timeout, proxy=None, reasoner=reasoner)

        # 初始化 Ark 客户端，设置较长的超时时间以支持深度推理
        self.client = AsyncArk(
            api_key=api_key,
            timeout=timeout or 1800,  # 默认30分钟超时
        )

    def _patch_proxy(self, client, proxy: str) -> None:
        """Ark客户端不需要代理设置"""
        pass

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头

        Returns:
            Dict[str, str]: 请求头字典
        """
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def _prepare_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """处理消息格式

        Args:
            messages: 原始消息列表

        Returns:
            List[Dict[str, str]]: 处理后的消息列表
        """
        # Ark 的消息格式已经是正确的，无需特殊处理
        return messages

    async def stream_chat(
            self,
            messages: List[Dict[str, str]],
            model: str,
            config: Optional[Any] = None
    ) -> AsyncGenerator[tuple[str, str], None]:
        """流式对话

        Args:
            messages: 消息列表
            model: 模型名称
            config: 配置参数

        Yields:
            tuple[str, str]: (内容类型, 内容)
                内容类型: "reasoning" 或 "content"
                内容: 实际的文本内容
        """
        try:
            # 准备请求参数
            params = {
                "model": model,
                "messages": self._prepare_messages(messages),
                "stream": True,
                "temperature": 0.7
            }

            # 如果提供了配置，更新参数
            if config:
                params.update(config)

            # 调用 Ark API 进行流式响应
            stream = await self.client.chat.completions.create(**params)

            # 处理流式响应
            async for chunk in stream:
                if not chunk.choices:
                    continue

                # 处理推理内容
                if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content:
                    yield "reasoning", chunk.choices[0].delta.reasoning_content

                # 处理普通内容
                if chunk.choices[0].delta.content:
                    yield "content", chunk.choices[0].delta.content

        except ArkAPIError as e:
            error_msg = f"Ark API 错误: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"流式对话失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    async def stream_bot_chat(
            self,
            messages: List[Dict[str, str]],
            model: str,
            config: Optional[Any] = None,
            stream: bool = True
    ) -> tuple[AsyncGenerator[tuple[str, str], None], List[Reference]]:
        """Bot 流式对话

        Args:
            messages: 消息列表
            model: 模型名称
            config: 配置参数
            stream: 是否使用流式响应，默认为 True

        Returns:
            tuple[AsyncGenerator[tuple[str, str], None], List[Reference]]: 
                第一个元素是流式响应的异步生成器
                第二个元素是收集到的所有 references 列表
        """
        try:
            # 准备请求参数
            params = {
                "model": model,
                "messages": messages,
                "stream": stream
            }

            # 如果提供了配置，更新参数
            if config:
                params.update(config)

            # 调用 Bot Chat API
            response = await self.client.bot_chat.completions.create(**params)

            references = []
            
            async def generate_content():
                async for chunk in response:
                    if chunk.references:
                        references.extend(chunk.references)
                    if not chunk.choices:
                        continue
                    yield "content", chunk.choices[0].delta.content

            return generate_content(), references

        except ArkAPIError as e:
            error_msg = f"Bot Chat API 错误: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Bot Chat 请求失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
