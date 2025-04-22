import uuid
from typing import Dict, Any, AsyncGenerator, List, Optional, Tuple
from .node import Node


class Workflow:
    """工作流管理器"""

    def __init__(self, name: str):
        self.name = name
        self.nodes: Dict[str, Node] = {}
        self.node_order: List[str] = []
        self.context: Dict[str, Any] = {}
        self.tid: str = str(uuid.uuid4())

    def add_node(self, node: Node) -> None:
        """添加节点
        
        Args:
            node: 要添加的节点
        """
        self.nodes[node.name] = node
        self.node_order.append(node.name)

    def set_node_order(self, order: List[str]) -> None:
        """设置节点执行顺序
        
        Args:
            order: 节点名称列表
        """
        self.node_order = order

    async def execute(self, initial_inputs: Dict[str, Any]) -> AsyncGenerator[Tuple[str, str], None]:
        """执行工作流
        
        Args:
            initial_inputs: 初始输入数据
            
        Yields:
            str: 处理过程中的流式输出
        """
        try:
            # 初始化上下文
            self.context = initial_inputs.copy()

            # 按顺序执行节点
            for node_name in self.node_order:
                node = self.nodes.get(node_name)
                if not node:
                    continue

                # 准备节点输入
                node_inputs = self._prepare_node_inputs(node)

                # 执行节点
                async for result in node.execute(node_inputs):
                    yield result

                # 更新上下文
                self._update_context(node)

            yield "done", ""

        except Exception as e:
            error_msg = f"工作流 {self.name} 执行失败: {str(e)}"
            yield "error", error_msg
            yield "done", ""

    def _prepare_node_inputs(self, node: Node) -> Dict[str, Any]:
        """准备节点输入数据
        
        Args:
            node: 目标节点
            
        Returns:
            Dict[str, Any]: 节点输入数据
        """
        # TODO: 实现输入数据准备逻辑
        return self.context.copy()

    def _update_context(self, node: Node) -> None:
        """更新工作流上下文
        
        Args:
            node: 已执行的节点
        """
        # 将节点输出添加到上下文
        self.context.update(node.get_all_outputs())

    def get_context(self) -> Dict[str, Any]:
        """获取工作流上下文
        
        Returns:
            Dict[str, Any]: 上下文数据
        """
        return self.context.copy()

    def get_tid(self) -> str:
        """获取当前任务ID

        Returns:
            str: 任务ID
        """
        return self.tid