import uuid
import json
import os
from typing import Dict, Any, AsyncGenerator, List, Optional, Tuple
from services.llm.workflow.base.node import Node


class Workflow:
    """工作流管理器"""

    def __init__(self, name: str, tid: Optional[str] = None):
        """初始化工作流
        
        Args:
            name: 工作流名称
            tid: 任务ID，如果为None则自动生成
        """
        self.name = name
        self.nodes: Dict[str, Node] = {}
        self.node_order: List[str] = []
        self.context: Dict[str, Any] = {}
        self.tid = tid or str(uuid.uuid4())
        self._context_dir = "workflow_contexts"  # 上下文存储目录
        self._ensure_context_dir()

    def set_tid(self, tid: str) -> None:
        """设置任务ID
        
        Args:
            tid: 任务ID
        """
        self.tid = tid

    def _ensure_context_dir(self) -> None:
        """确保上下文存储目录存在"""
        if not os.path.exists(self._context_dir):
            os.makedirs(self._context_dir)

    def _get_context_file_path(self, tid: str) -> str:
        """获取上下文文件路径
        
        Args:
            tid: 任务ID
            
        Returns:
            str: 上下文文件路径
        """
        return os.path.join(self._context_dir, f"{tid}.json")

    def _save_context(self) -> None:
        """保存当前上下文到文件"""
        context_file = self._get_context_file_path(self.tid)
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(self.context, f, ensure_ascii=False, indent=2)

    def _load_context(self, tid: str) -> Dict[str, Any]:
        """从文件加载上下文
        
        Args:
            tid: 任务ID
            
        Returns:
            Dict[str, Any]: 加载的上下文
        """
        context_file = self._get_context_file_path(tid)
        if not os.path.exists(context_file):
            raise FileNotFoundError(f"Context file not found for tid: {tid}")
        
        with open(context_file, 'r', encoding='utf-8') as f:
            return json.load(f)

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

        # 初始化上下文
        self.context = initial_inputs.copy()
        self._save_context()  # 保存初始上下文

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
            self._save_context()  # 保存更新后的上下文

        # try:
        #     # 初始化上下文
        #     self.context = initial_inputs.copy()
        #     self._save_context()  # 保存初始上下文
        #
        #     # 按顺序执行节点
        #     for node_name in self.node_order:
        #         node = self.nodes.get(node_name)
        #         if not node:
        #             continue
        #
        #         # 准备节点输入
        #         node_inputs = self._prepare_node_inputs(node)
        #
        #         # 执行节点
        #         async for result in node.execute(node_inputs):
        #             yield result
        #
        #         # 更新上下文
        #         self._update_context(node)
        #         self._save_context()  # 保存更新后的上下文
        #
        #     yield "done", ""
        #
        # except Exception as e:
        #     error_msg = f"工作流 {self.name} 执行失败: {str(e)}"
        #     yield "error", error_msg
        #     yield "done", ""

    async def resume_from_node(self, node_name: str) -> AsyncGenerator[Tuple[str, str], None]:
        """从指定节点继续执行工作流
        
        Args:
            node_name: 要从中继续执行的节点名称
            
        Yields:
            str: 处理过程中的流式输出
        """
        try:
            # 加载上下文
            self.context = self._load_context(self.tid)

            # 找到指定节点的位置
            node_index = self.node_order.index(node_name)
            remaining_nodes = self.node_order[node_index:]

            # 从指定节点开始执行
            for node_name in remaining_nodes:
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
                self._save_context()  # 保存更新后的上下文

            yield "done", ""

        except Exception as e:
            error_msg = f"工作流 {self.name} 从节点 {node_name} 恢复执行失败: {str(e)}"
            yield "error", error_msg
            yield "done", ""

    def _prepare_node_inputs(self, node: Node) -> Dict[str, Any]:
        """准备节点输入数据
        
        Args:
            node: 目标节点
            
        Returns:
            Dict[str, Any]: 节点输入数据
        """
        node.context = self.context.copy()
        return node.context

    def _update_context(self, node: Node) -> None:
        """更新工作流上下文
        
        Args:
            node: 已执行的节点
        """
        # 将节点输出添加到上下文
        out = node.get_all_outputs()
        self.context.update(out)
        print(f"update context: {self.context}")


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