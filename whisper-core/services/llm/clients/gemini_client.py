"""Gemini 客户端类,使用 Google GenAI SDK"""

from typing import AsyncGenerator, Optional, Dict, Any, List
import json

from google import genai
from google.genai import types
from google.genai import _api_client
from ..clients.base_client import BaseClient
from ..utils.logger import logger


class GeminiClient(BaseClient):
    """Gemini 客户端类

    使用 Google GenAI SDK 实现 Gemini 模型的对话功能
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
        """初始化 Gemini 客户端

        Args:
            api_key: API密钥
            api_url: API地址
            timeout: 请求超时设置,None则使用默认值
            proxy: 代理服务器地址
        """
        super().__init__(api_key, api_url, api_request_address, timeout, proxy=proxy, reasoner=reasoner)
        
        # 初始化 Google GenAI 客户端
        self.client = genai.Client(api_key=api_key)
        
        # 如果设置了代理，应用代理补丁
        if self.proxy:
            logger.info(f"为 Gemini 客户端应用代理补丁: {self.proxy}")
            try:
                self._patch_proxy(self.client, self.proxy)
            except Exception as e:
                logger.error(f"应用代理补丁失败: {e}")
                raise

    def _patch_proxy(self, client, proxy: str) -> None:
        """为 Gemini 客户端应用代理补丁

        Args:
            client: 需要补丁的客户端实例
            proxy: 代理服务器地址
        """

        http_options = types.HttpOptions(
            client_args={"proxy": proxy}
        )

        # 修改客户端实例中的_http_options
        patched = _api_client._patch_http_options(
            client._api_client._http_options,
            http_options)

        client._api_client._http_options = patched

        # 重新创建带有代理的httpx客户端
        client_args, async_client_args = client._api_client._ensure_ssl_ctx(
            client._api_client._http_options
        )

        # 关闭现有连接
        client._api_client._httpx_client.close()
        client._api_client._async_httpx_client.aclose()

        # 创建新的连接池
        from google.genai._api_client import SyncHttpxClient, AsyncHttpxClient
        client._api_client._httpx_client = SyncHttpxClient(**client_args)
        client._api_client._async_httpx_client = AsyncHttpxClient(**async_client_args)

        return client

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头

        Returns:
            Dict[str, str]: 请求头字典
        """
        return {
            "Content-Type": "application/json",
        }

    def _prepare_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """处理消息格式

        Args:
            messages: 原始消息列表

        Returns:
            List[Dict[str, str]]: 处理后的消息列表
        """
        # Gemini 的消息格式与 OpenAI 兼容，无需特殊处理
        return messages

    async def chat(
        self, messages: List[Dict[str, str]], model: str
    ) -> Dict[str, Any]:
        """非流式对话

        Args:
            messages: 消息列表
            model: 模型名称

        Returns:
            Dict[str, Any]: 响应数据

        Raises:
            Exception: 请求错误
        """
        try:
            # 构建提示
            prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            
            # 调用 Gemini API
            response = self.client.models.generate_content(
                model=model,
                contents=prompt,
                stream=False
            )
            
            # 转换为 OpenAI 兼容格式
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": response.text
                    }
                }]
            }

        except Exception as e:
            error_msg = f"Chat请求失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        is_origin_reasoning: bool = True,
    ) -> AsyncGenerator[tuple[str, str], None]:
        """流式对话

        Args:
            messages: 消息列表
            model: 模型名称
            is_origin_reasoning: 是否使用原生推理

        Yields:
            tuple[str, str]: (内容类型, 内容)
                内容类型: "reasoning" 或 "content"
                内容: 实际的文本内容
        """
        config = types.GenerateContentConfig(
            temperature=0.7
        )

        try:
            #  提取messages中的第一个key为system的值
            system_prompt = [msg for msg in messages if msg['role'] == 'system']
            if system_prompt:
                 config.system_instruction = system_prompt[0]['content']

            # 提取messages中的key为user的值
            user_content = [msg for msg in messages if msg['role'] == 'user']
            if user_content:
                user_content = user_content[-1]['content']

            
            # 调用 Gemini API 进行流式响应
            response = self.client.models.generate_content_stream(
                model=model,
                config = config,
                contents=user_content
            )

            # 处理流式响应
            for chunk in response:
                if chunk.text:
                    # Gemini 目前不支持原生推理，所有内容都作为普通内容返回
                    yield "content", chunk.text

        except Exception as e:
            error_msg = f"流式对话失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) 