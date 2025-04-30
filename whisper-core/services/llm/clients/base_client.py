"""基础客户端类,定义通用接口"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional, Any

import aiohttp
from aiohttp.client_exceptions import ClientError, ServerTimeoutError

from ..utils.logger import logger


class BaseClient(ABC):
    """基础客户端类"""

    # 默认超时设置(秒)
    # total: 总超时时间
    # connect: 连接超时时间
    # sock_read: 读取超时时间
    # TODO: 默认时间的设置涉及到模型推理速度，需要根据实际情况进行调整
    DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=600, connect=10, sock_read=500)

    def __init__(
        self,
        api_key: str,
        api_url: str,
        api_request_address: str,
        timeout: Optional[aiohttp.ClientTimeout] = None,
        proxy: Optional[str] = None,
        reasoner: bool = False,
    ):
        """初始化基础客户端

        Args:
            api_key: API密钥
            api_url: API地址
            timeout: 请求超时设置,None则使用默认值
            proxy: 代理服务器地址，例如 "http://127.0.0.1:7890"
        """
        self.api_key = api_key
        self.api_url = api_url
        self.api_request_address = api_request_address
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.proxy = proxy
        self.reasoner = reasoner

    def set_proxy(self, proxy: str) -> None:
        """设置代理服务器地址

        Args:
            proxy: 代理服务器地址，例如 "127.0.0.1:7890"
        """
        # 如果代理地址不包含协议前缀，添加 http:// 前缀
        if proxy and not proxy.startswith(('http://', 'https://', 'socks://', 'socks5://')):
            self.proxy = f"http://{proxy}"
        else:
            self.proxy = proxy
        logger.info(f"设置代理: {self.proxy}")

    @abstractmethod
    def _patch_proxy(self, client, proxy: str) -> None:
        """为客户端应用代理补丁，由子类实现

        Args:
            client: 需要补丁的客户端实例
            proxy: 代理服务器地址
        """
        pass

    async def _make_request(
        self, headers: dict, data: dict, timeout: Optional[aiohttp.ClientTimeout] = None
    ) -> AsyncGenerator[bytes, None]:
        """发送请求并处理响应

        Args:
            headers: 请求头
            data: 请求数据
            timeout: 当前请求的超时设置,None则使用实例默认值

        Yields:
            bytes: 原始响应数据

        Raises:
            aiohttp.ClientError: 客户端错误
            ServerTimeoutError: 服务器超时
            Exception: 其他异常
        """
        request_timeout = timeout or self.timeout

        try:
            # 打印请求信息
            full_url = self.api_url + self.api_request_address
            logger.info(f"发送请求到: {full_url}")
            
            # 处理 headers 中的敏感信息
            safe_headers = headers.copy()
            if 'Authorization' in safe_headers:
                safe_headers['Authorization'] = 'Bearer ******'
            logger.info(f"请求头: {safe_headers}")
            
            # 处理 data 中的敏感信息
            safe_data = data.copy()
            if 'messages' in safe_data:
                safe_data['messages'] = [
                    {k: v if k != 'content' else '******' for k, v in msg.items()}
                    for msg in safe_data['messages']
                ]
            logger.info(f"请求数据: {safe_data}")

            if self.proxy:
                logger.info(f"使用代理: {self.proxy}")
            logger.info(f"超时设置: {request_timeout}")

            # 使用 connector 参数来优化连接池
            connector = aiohttp.TCPConnector(limit=100, force_close=True)
            
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(
                    full_url, 
                    headers=headers, 
                    json=data, 
                    timeout=request_timeout,
                    proxy=self.proxy,
                    verify_ssl=False,
                ) as response:
                    # 检查响应状态
                    if not response.ok:
                        error_text = await response.text()
                        error_msg = f"API 请求失败: 状态码 {response.status}, 错误信息: {error_text}"
                        logger.error(error_msg)
                        raise ClientError(error_msg)

                    # 流式读取响应内容
                    async for chunk in response.content.iter_any():
                        if chunk:  # 过滤空chunks
                            yield chunk

        except ServerTimeoutError as e:
            error_msg = f"请求超时: {str(e)}"
            logger.error(error_msg)
            raise

        except ClientError as e:
            error_msg = f"客户端错误: {str(e)}"
            logger.error(error_msg)
            raise

        except Exception as e:
            error_msg = f"请求处理异常: {str(e)}"
            logger.error(error_msg)
            raise

    @abstractmethod
    async def stream_chat(
        self, messages: list, model: str, config: Optional[Any] = None
    ) -> AsyncGenerator[tuple[str, str], None]:
        """流式对话，由子类实现

        Args:
            messages: 消息列表
            model: 模型名称
            config: 配置参数

        Yields:
            tuple[str, str]: (内容类型, 内容)
        """
        pass