from typing import Dict, List, Any, Optional, AsyncGenerator
import json
import logging
from abc import ABC, abstractmethod
from services.llm.clients.LLM_client import llm_client
from .output_manager import OutputManager

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    def __init__(self, model_name: str = "Gemini/Gemini-2.0-Flash-thinking"):
        """初始化Agent

        Args:
            model_name: 使用的模型名称
        """
        self.model_name = model_name
        self.output_manager = OutputManager()
        self.context: Dict[str, Any] = {}  # 用于存储上下文信息

    async def call(
        self, 
        content: str, 
        files: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Agent的主要调用方法

        Args:
            content: 主要输入内容
            files: 可选的文件列表，每个文件是一个字典，包含文件路径和内容
            **kwargs: 其他参数

        Yields:
            str: 处理过程中的流式输出
        """
        try:
            # 初始化上下文
            self.context = {
                "content": content,
                "files": files or [],
                **kwargs
            }

            # 前置处理
            await self.pre_process()

            # 构建消息
            messages = await self.build_messages()

            # 调用LLM
            response = await self.call_llm(messages)

            # 处理响应
            async for result in self.process_response(response):
                yield result

            # 后置处理
            await self.post_process()

        except Exception as e:
            error_msg = f"Agent处理失败: {str(e)}"
            logger.error(error_msg)
            yield f"data: {json.dumps({'role': 'error', 'content': error_msg}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

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

    async def call_llm(self, messages: List[Dict[str, str]]) -> List[str]:
        """调用LLM并收集响应

        Args:
            messages: 发送给LLM的消息列表

        Returns:
            List[str]: LLM的响应列表
        """
        response = []
        async for role, content in llm_client.chat_stream(self.model_name, messages):
            if role == "error":
                logger.error(f"LLM调用错误: {content}")
                continue
            if role == "done":
                break
            response.append(content)
        return response

    @abstractmethod
    async def process_response(self, response: List[str]) -> AsyncGenerator[str, None]:
        """处理LLM的响应

        Args:
            response: LLM的响应列表

        Yields:
            str: 处理后的输出
        """
        pass

    @abstractmethod
    async def post_process(self) -> None:
        """后置处理，在所有处理完成后的清理工作"""
        pass

    async def save_step_output(self, step_name: str, data: Dict[str, Any]) -> None:
        """保存步骤输出

        Args:
            step_name: 步骤名称
            data: 要保存的数据
        """
        self.output_manager.save_step_output(step_name, data)

    async def get_step_output(self, step_name: str) -> Dict[str, Any]:
        """获取步骤输出

        Args:
            step_name: 步骤名称

        Returns:
            Dict[str, Any]: 步骤输出数据
        """
        return self.output_manager.get_step_output(step_name)

    def get_tid(self) -> str:
        """获取当前任务ID"""
        return self.output_manager.get_tid()

    @abstractmethod
    async def parse_response(self, response: List[str]) -> Dict[str, Any]:
        """解析LLM的响应

        Args:
            response: LLM的响应列表

        Returns:
            Dict[str, Any]: 解析后的结构化数据
        """
        pass 