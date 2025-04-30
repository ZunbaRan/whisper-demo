"""OpenAI 客户端类,使用 OpenAI API"""

from typing import AsyncGenerator, Optional, Dict, Any, List
import json
import httpx

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionChunk

from ..clients.base_client import BaseClient
from ..utils.logger import logger


class OpenAIClient(BaseClient):
    """OpenAI 客户端类

    使用 OpenAI API 实现对话功能
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
        """初始化 OpenAI 客户端

        Args:
            api_key: API密钥
            api_url: API地址
            timeout: 请求超时设置,None则使用默认值
            proxy: 代理服务器地址
        """
        super().__init__(api_key, api_url, api_request_address, timeout, proxy=proxy, reasoner=reasoner)
        
        # 创建 httpx 客户端配置
        http_client = None
        if self.proxy:
            logger.info(f"为 OpenAI 客户端设置代理: {self.proxy}")
            http_client = httpx.AsyncClient(
                proxy=self.proxy,
                transport=httpx.AsyncHTTPTransport(local_address="0.0.0.0"),
                verify=False
            )
        
        # 初始化 OpenAI 客户端
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=api_url,
            timeout=timeout or self.DEFAULT_TIMEOUT.total,
            max_retries=0,
            http_client=http_client
        )

    def _patch_proxy(self, client, proxy: str) -> None:
        """为 OpenAI 客户端应用代理补丁

        Args:
            client: 需要补丁的客户端实例
            proxy: 代理服务器地址
        """
        # 不再需要此方法，因为代理设置已经在初始化时完成
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
        # OpenAI 的消息格式已经是正确的，无需特殊处理
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
                
            if config.get("tools"):
                # 获取 tools 数组中第一个元素的  type 
                tool_type = config.get("tools")[0].get("type")
                if tool_type == "builtin_function":
                     # 第一次请求或工具调用时使用非流式请求
                    tool_call = {
                         "model": "moonshot-v1-auto",
                         "messages": messages,
                         "temperature": 0.3,
                         "tools": config.get("tools"),
                         "stream": False,
                    }
                    response = await self.client.chat.completions.create(**tool_call)
                    choice = response.choices[0]
                    if choice.finish_reason == "tool_calls":
                       messages.append(choice.message)
                    
                       for tool_call in choice.message.tool_calls:
                           tool_call_name = tool_call.function.name
                           tool_call_args = json.loads(tool_call.function.arguments)
                           if tool_call.function.name == "$web_search":
                               msg = {
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "name": tool_call_name,
                                    "content": json.dumps(tool_call_args)
                               }

                               messages.append(msg)

                

            # 调用 OpenAI API 进行流式响应
            response = await self.client.chat.completions.create(**params)

            # 处理流式响应
            async for chunk in response:
                if isinstance(chunk, ChatCompletionChunk):
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        # OpenAI 目前不支持原生推理，所有内容都作为普通内容返回
                        yield "content", content



        except Exception as e:
            error_msg = f"流式对话失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) 