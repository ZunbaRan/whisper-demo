import uuid
from typing import Dict, Any, AsyncGenerator, Optional, List, Tuple
from abc import ABC, abstractmethod
from services.llm.agent.base_agent import BaseAgent
import json
import logging

logger = logging.getLogger(__name__)

class Node(ABC):
    """工作流节点基类"""
    
    def __init__(self, name: str, agent: BaseAgent, tid: Optional[str]):
        self.name = name
        self.agent = agent
        self.context: Dict[str, Any] = {}
        self.inputs: Dict[str, Any] = {}
        self.outputs: Dict[str, Any] = {}
        self.call_results: List[Tuple[str, str]] = []
        self.tid: tid or uuid.uuid4()
        
    async def execute(self, inputs: Dict[str, Any]) -> AsyncGenerator[Tuple[str, str], None]:
        """执行节点
        
        Args:
            inputs: 输入数据
            
        Yields:
            Tuple[str, str]: (role, content) 元组
        """

        # 设置输入
        self.inputs = inputs

        # 准备上下文
        await self.prepare_context()

        # 执行节点逻辑
        async for role, content in self.call():
            self.call_results.append((role, content))
            yield role, content

        # 处理输出
        await self.process_output(self.call_results)

        # try:
        #     # 设置输入
        #     self.inputs = inputs
        #
        #     # 准备上下文
        #     await self.prepare_context()
        #
        #     # 执行节点逻辑
        #     async for role, content in self.call():
        #         self.call_results.append((role, content))
        #         yield role, content
        #
        #     # 处理输出
        #     await self.process_output(self.call_results)
        #
        # except Exception as e:
        #     error_msg = f"节点 {self.name} 执行失败: {str(e)}"
        #     logger.error(error_msg)
        #     yield "error", error_msg
        #     yield "done", ""
            
            
    @abstractmethod
    async def call(self) -> AsyncGenerator[Tuple[str, str], None]:
        """执行节点的主要逻辑"""
        pass
            
    async def prepare_context(self) -> None:
        """准备上下文"""
        pass
        
    async def process_output(self, results: List[Tuple[str, str]]) -> None:
        """处理输出结果"""
        pass
        
    def get_all_outputs(self) -> Dict[str, Any]:
        """获取所有输出数据
        
        Returns:
            Dict[str, Any]: 所有输出数据
        """
        return self.outputs.copy() 