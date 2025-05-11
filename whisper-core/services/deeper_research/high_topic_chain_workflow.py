import logging
from typing import AsyncGenerator, Tuple, Dict, Any

from services.deeper_research.node.high_topic_question_chain import HighTopicQuestionChainNode
from services.deeper_research.node.per_analysis_report_node import PerAnalysisReportNode
from services.deeper_research.node.search_report_node import SearchReportNode
from services.llm.workflow.base.workflow import Workflow
from services.deeper_research.node.initial_query_sub_queries_node import InitialQuerySubQueriesNode

logger = logging.getLogger(__name__)

class HighTopicChainWorkflow:
    def __init__(self):
        self.workflow = Workflow("high_topic_chain_workflow")
        
        # 获取工作流的唯一ID，用于节点tid
        workflow_tid = self.workflow.get_tid()

        # 创建节点
        # 确保 InitialQuerySubQueriesNode 的构造函数接受 tid 参数，或者调整节点类的 __init__
        # 基于提供的 InitialQuerySubQueriesNode 定义，它接受 tid
        self.high_topic_question_chain = HighTopicQuestionChainNode(tid=workflow_tid)

        # 添加节点到工作流
        self.workflow.add_node(self.high_topic_question_chain)

        
        # 设置节点执行顺序 (即使只有一个节点，也最好设置)
        self.workflow.set_node_order([self.high_topic_question_chain.name])

    async def astream_execute(self, question: str, initial_context: Dict[str, Any] = None) -> AsyncGenerator[Tuple[str, str], None]:
        """
        执行深度研究工作流并流式返回结果。
        每个节点的结果 (role, content) 将被流式输出。
        """
        logger.info(f"启动深度研究工作流，问题: '{question}'")

        # 准备初始输入
        # Workflow的execute方法会将initial_inputs合并到self.context中
        # InitialQuerySubQueriesNode在其prepare_context中加载固定文档，
        # 并在其call方法中将self.context传递给其agent。
        # 因此，问题需要作为initial_inputs的一部分传递。
        workflow_initial_inputs = {"one_high_potential_topic": question}
        if initial_context:
            workflow_initial_inputs.update(initial_context)

        # Workflow.execute 期望返回 Tuple[str, Any] 其中 str 是节点名称，Any 是节点的输出
        # InitialQuerySubQueriesNode.call 应该返回 Tuple[str, str] (role, content)
        async for role, content in self.workflow.execute(initial_inputs=workflow_initial_inputs):
            yield role, content
