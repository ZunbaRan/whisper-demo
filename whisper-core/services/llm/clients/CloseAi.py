from abc import ABC
from typing import Optional, List, Dict, Any, AsyncGenerator

from anthropic import Anthropic, TextEvent

from services.llm.clients.base_client import BaseClient
from ..utils.logger import logger

if __name__ == '__main__':
    client = Anthropic(
        base_url='https://api.openai-proxy.org/anthropic',
        api_key='sk-xxxx',
    )

    message = client.messages.create(
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": "Hello, Claude",
            }
        ],
        model="claude-3-opus-20240229",
    )
    print(message.content)


class CloseAnthropicClient(BaseClient):
    async def _patch_proxy(self, client, proxy: str) -> None:
        pass

    def __init__(
            self,
            api_key: str,
            api_url: str,
            api_request_address: str,
            timeout: Optional[int] = None,
            proxy: Optional[str] = None,
            reasoner: bool = False,
    ):
        super().__init__(api_key, api_url, api_request_address)


        # 初始化 OpenAI 客户端
        self.client = Anthropic(
            api_key=api_key,
            base_url=api_url,
        )

    async def stream_chat(
            self,
            messages: List[Dict[str, str]],
            model: str,
            config: Optional[Any] = None
    ) -> AsyncGenerator[tuple[str, str], None]:
        try:
            # 使用 with 上下文管理器创建流式响应（Claude 特定语法）
            with self.client.messages.stream(
                    model=model,
                    messages=messages,
                    max_tokens=8000
            ) as response:
                # 直接迭代响应对象
                for event in response:
                    if isinstance(event, TextEvent):  # 精准判断文本事件
                        # Claude 返回的 content 是直接字符串
                        yield "content", event.text  # 使用 event.text 替代 delta.content

        except Exception as e:
            error_msg = f"Claude 流式对话失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)