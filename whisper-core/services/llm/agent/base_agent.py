from typing import Dict, List, Any, Optional, AsyncGenerator, Tuple, Union
import json
import logging
from abc import ABC, abstractmethod
from services.llm.clients.LLM_client import llm_client

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    def __init__(self, model_name: str = "Gemini/Gemini-2.0-Flash-thinking"):
        """初始化Agent

        Args:
            model_name: 使用的模型名称
        """
        self.model_name = model_name
        self.context: Dict[str, Any] = {}  # 用于存储上下文信息
        self.response_stream: List[Tuple[str, str]] = []  # 用于存储流式响应

    async def call(
            self,
            content: Optional[str] = None,
            files: Optional[List[Dict[str, str]]] = None,
            **kwargs
    ) -> AsyncGenerator[Tuple[str, str], None]:
        """Agent的主要调用方法

        Args:
            content: 主要输入内容
            files: 可选的文件列表，每个文件是一个字典，包含文件路径和内容
            **kwargs: 其他参数

        Yields:
            Tuple[str, str]: (role, content) 元组
        """
        # try:
        # 初始化上下文
        self.context = {
            "content": content or '',
            "files": files or [],
            **kwargs
        }


        self.response_stream = []  # 清空响应流

        # 前置处理
        await self.pre_process()

        config:Any = self.context.get("config")


        # 构建消息
        messages = await self.build_messages()

        # 调用LLM并处理响应
        async for role, content in self.process_response(self.call_llm(messages, config)):
            self.response_stream.append((role, content))  # 保存响应
            if role == "error":
                yield "error", content
            else:
                yield "assistant", content

        # 后置处理
        await self.post_process()

    # except Exception as e:
    #     error_msg = f"Agent处理失败: {e.__traceback__}"
    #     logger.error(e.__traceback__)
    #     yield "error", error_msg

    @abstractmethod
    async def pre_process(self) -> None:
        """前置处理，在调用LLM之前的准备工作"""
        pass

    @abstractmethod
    async def build_messages(self) -> List[Dict[str, str]]:
        """构建发送给LLM的消息

        Returns:
            List[Dict[str, str]]: 消息列表
        """
        pass

    async def build_prompt(self, template: str, **kwargs) -> str:
        """构建prompt

        Args:
            template: prompt模板
            **kwargs: 模板参数

        Returns:
            str: 构建好的prompt
        """
        return template.format(**kwargs)

    async def call_llm(self, messages: List[Dict[str, str]], config: Any) -> AsyncGenerator[Tuple[str, str], None]:
        """调用LLM并流式返回响应

        Args:
            messages: 发送给LLM的消息列表
            config: 配置参数

        Yields:
            Tuple[str, str]: (role, content) 元组
        """
        async for role, content in llm_client.chat_stream(self.model_name, messages, config):
            yield role, content

        # try:
        #     async for role, content in llm_client.chat_stream(self.model_name, messages):
        #         yield role, content
        # except Exception as e:
        #     error_msg = f"LLM调用失败: {str(e)}"
        #     logger.error(error_msg)
        #     yield "error", error_msg

    @abstractmethod
    async def process_response(self, response: AsyncGenerator[Tuple[str, str], None]) -> AsyncGenerator[Tuple[str, str], None]:
        """处理LLM的响应

        Yields:
            Tuple[str, str]: (role, content) 元组
        """
        async for role, content in response:
            yield role, content

    @abstractmethod
    async def post_process(self) -> None:
        """后置处理，在所有处理完成后的清理工作"""
        content_list = [result[1] for result in self.response_stream]
        content_str = "".join(content_list)
        format_res = await self.parse_response(content_str)
        self.context["format_res"] = format_res

    @abstractmethod
    async def parse_response(self, response: str) ->  Union[dict, list, str, int, float, bool, None]:
        """解析LLM的响应

        Args:
            response: LLM的响应内容

        Returns:
            Dict[str, Any]: 解析后的结构化数据
        """
        pass