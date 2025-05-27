import logging
import uuid
from pathlib import Path
from typing import AsyncGenerator, Tuple, Dict, Any

from services.deeper_research.agent.create_chain_from_text.create_chain_from_text import CreateChainByMaterials
from services.deeper_research.node.CreateChainByMaterialsNode import CreateChainByMaterialsNode
from services.deeper_research.node.chain_report_node import ChainReportNode
from services.deeper_research.node.content_creator_node import ContentCreatorNode
from services.deeper_research.node.high_topic_question_chain import HighTopicQuestionChainNode
from services.deeper_research.node.per_analysis_report_node import PerAnalysisReportNode
from services.deeper_research.node.search_report_node import SearchReportNode
from services.llm.workflow.base.workflow import Workflow
from services.deeper_research.node.initial_query_sub_queries_node import InitialQuerySubQueriesNode

logger = logging.getLogger(__name__)


class CreateChainFromTextFlow:
    def  __init__(self, tid: str = None, podcast_name: str = None):
        self._output_dir = None
        if tid is None:
            tid = str(uuid.uuid4())
        self.workflow = Workflow("create_chain_from_text_flow", tid=tid)
        
        if podcast_name is not None:
            self.podcast_name = podcast_name

        # 获取工作流的唯一ID，用于节点tid
        workflow_tid = tid

        # 创建节点
        # 确保 InitialQuerySubQueriesNode 的构造函数接受 tid 参数，或者调整节点类的 __init__
        # 基于提供的 InitialQuerySubQueriesNode 定义，它接受 tid
        self.create_chain_by_materials = CreateChainByMaterialsNode(tid=workflow_tid)
        self.content_creator_node = ContentCreatorNode(tid=workflow_tid)

        # 添加节点到工作流
        self.workflow.add_node(self.create_chain_by_materials)
        self.workflow.add_node(self.content_creator_node)

        # 设置节点执行顺序 (即使只有一个节点，也最好设置)
        self.workflow.set_node_order([self.create_chain_by_materials.name,
                                      self.content_creator_node.name])

    async def astream_execute(self, question: str, initial_context: Dict[str, Any] = None) -> AsyncGenerator[
        Tuple[str, str], None]:
        """
        执行深度研究工作流并流式返回结果。
        每个节点的结果 (role, content) 将被流式输出。
        """
        logger.info(f"根据素材创建文章")

        # 准备初始输入
        workflow_initial_inputs = {"currently_collected_materials": question}
        if initial_context:
            workflow_initial_inputs.update(initial_context)

        async for role, content in self.workflow.execute(initial_inputs=workflow_initial_inputs):
            yield role, content

        content_create = self.workflow.context.get("content_create", "")

        # 获取任务ID并创建对应的目录
        tid = self.workflow.get_tid()
        tid_str = str(tid)

        # 创建输出目录
        output_dir = Path("public/output/materials_article")  # 输出目录
        if self.podcast_name is not None:
            output_dir = output_dir / self.podcast_name

        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)
        tid_dir = self._output_dir / tid_str
        tid_dir.mkdir(parents=True, exist_ok=True)


        # 保存各个阶段的Markdown内容
        self._save_markdown(content_create, tid_dir / "materials_article.md")
        # self._save_markdown(engagement_injector, tid_dir / "engagement.md")

    def _save_markdown(self, content: str, file_path: Path) -> None:
        """保存Markdown内容到文件

        Args:
            content: Markdown内容
            file_path: 文件路径
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"文件已保存到: {file_path}")

