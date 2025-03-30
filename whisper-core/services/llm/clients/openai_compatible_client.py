"""OpenAI 兼容格式的客户端类,用于处理符合 OpenAI API 格式的服务"""

import json
from typing import AsyncGenerator, Optional, Union, Dict, Any, List

import aiohttp
from aiohttp.client_exceptions import ClientError

from ..clients.base_client import BaseClient
from ..utils.logger import logger


class OpenAICompatibleClient(BaseClient):
    """OpenAI 兼容格式的客户端类

    用于处理符合 OpenAI API 格式的服务,如 Gemini 等
    """

    def __init__(
        self,
        api_key: str,
        api_url: str,
        api_request_address: str,
        timeout: Optional[aiohttp.ClientTimeout] = None,
        proxy: str = None,
        reasoner: bool = False,
    ):
        """初始化 OpenAI 兼容客户端

        Args:
            api_key: API密钥
            api_url: API地址
            timeout: 请求超时设置,None则使用默认值
            proxy: 代理服务器地址
        """
        super().__init__(api_key, api_url, api_request_address, timeout, proxy=proxy, reasoner=reasoner)
    
    def get_reasoner(self) -> bool:
        return self.reasoner

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头

        Returns:
            Dict[str, str]: 请求头字典
        """
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _prepare_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """处理消息格式

        Args:
            messages: 原始消息列表

        Returns:
            List[Dict[str, str]]: 处理后的消息列表
        """
        return messages

    async def chat(
        self, messages: List[Dict[str, str]], model: str
    ) -> Dict[str, Any]:
        """非流式对话

        Args:
            messages: 消息列表
            model: 模型名称

        Returns:
            Dict[str, Any]: OpenAI 格式的完整响应

        Raises:
            ClientError: 请求错误
        """
        headers = self._get_headers()
        processed_messages = self._prepare_messages(messages)

        data = {
            "model": model,
            "messages": processed_messages,
            "stream": False,
        }

        try:
            response_chunks = []
            async for chunk in self._make_request(headers, data):
                response_chunks.append(chunk)

            response_text = b"".join(response_chunks).decode("utf-8")
            return json.loads(response_text)

        except Exception as e:
            error_msg = f"Chat请求失败: {str(e)}"
            logger.error(error_msg)
            raise ClientError(error_msg)

    async def  stream_chat(
            self,
            messages: list,
            model: str = "deepseek-ai/DeepSeek-R1",
            is_origin_reasoning: bool = True,
    ) -> AsyncGenerator[tuple[str, str], None]:
        """流式对话

        Args:
            messages: 消息列表
            model: 模型名称

        Yields:
            tuple[str, str]: (内容类型, 内容)
                内容类型: "reasoning" 或 "content"
                内容: 实际的文本内容
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        data = {
            "model": model,
            "messages": messages,
            "stream": True
        }

        # 只在支持原生推理时采用｜ps: 如遇到支持原生推理字段的模型仍返回推理内容不足，可直接注释此区域
        if is_origin_reasoning:
            data["max_tokens"] = 8192

        logger.debug(f"开始流式对话：{data}")

        accumulated_content = ""
        is_collecting_think = False

        async for chunk in self._make_request(headers, data):
            chunk_str = chunk.decode("utf-8")

            try:
                lines = chunk_str.splitlines()
                for line in lines:
                    if line.startswith("data: "):
                        json_str = line[len("data: "):]
                        if json_str == "[DONE]":
                            return

                        data = json.loads(json_str)
                        if (
                                data
                                and data.get("choices")
                                and data["choices"][0].get("delta")
                        ):
                            delta = data["choices"][0]["delta"]

                            if is_origin_reasoning:
                                # 处理 reasoning_content
                                if delta.get("reasoning_content"):
                                    content = delta["reasoning_content"]
                                    yield "reasoning", content

                                if delta.get("reasoning_content") is None and delta.get(
                                        "content"
                                ):
                                    content = delta["content"]
                                    yield "content", content
                            else:
                                # 处理其他模型的输出
                                if delta.get("content"):
                                    content = delta["content"]
                                    if content == "":  # 只跳过完全空的字符串
                                        continue
                                    accumulated_content += content

                                    # 检查累积的内容是否包含完整的 think 标签对
                                    is_complete, processed_content = (
                                        self._process_think_tag_content(
                                            accumulated_content
                                        )
                                    )

                                    if "<think>" in content and not is_collecting_think:
                                        # 开始收集推理内容
                                        is_collecting_think = True
                                        yield "reasoning", content
                                    elif is_collecting_think:
                                        if "</think>" in content:
                                            # 推理内容结束
                                            is_collecting_think = False
                                            yield "reasoning", content
                                            # 输出空的 content 来触发 Claude 处理
                                            yield "content", ""
                                            # 重置累积内容
                                            accumulated_content = ""
                                        else:
                                            # 继续收集推理内容
                                            yield "reasoning", content
                                    else:
                                        # 普通内容
                                        yield "content", content

            except json.JSONDecodeError as e:
                logger.error(f"JSON 解析错误: {e}")
            except Exception as e:
                logger.error(f"处理 chunk 时发生错误: {e}")

    def _process_think_tag_content(self, content: str) -> tuple[bool, str]:
           """处理包含 think 标签的内容
    
           Args:
               content: 需要处理的内容字符串
    
           Returns:
               tuple[bool, str]:
                   bool: 是否检测到完整的 think 标签对
                   str: 处理后的内容
           """
           has_start = "<think>" in content
           has_end = "</think>" in content
    
           if has_start and has_end:
               return True, content
           elif has_start:
               return False, content
           elif not has_start and not has_end:
               return False, content
           else:
               return True, content