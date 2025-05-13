import os
import json
from typing import AsyncGenerator, Tuple, Optional
import logging
from pathlib import Path
from datetime import datetime

from .nodes.angle_hook_strategist_node import AngleHookStrategistNode
from .nodes.chapter_and_style_node import ChapterAndStyleNode
from .nodes.depth_enhancer_node import DepthEnhancerNode
from .nodes.elements_extraction_node import ElementsExtractionNode
from .nodes.engagement_injector_node import EngagementInjectorNode
from .nodes.structure_analysis_node import StructureAnalysisNode
from .nodes.structured_draft_node import StructuredDraftNode
from .nodes.theme_analysis_node import ThemeAnalysisNode
from services.llm.workflow.base.workflow import Workflow

logger = logging.getLogger(__name__)


class ArticleCreateFlow:
    """文章分析工作流"""

    def __init__(self, author_name: str, tid: Optional[str] = None):
        """初始化文章创建工作流
        
        Args:
            author_name: 作者名称
            tid: 任务ID，如果为None则自动生成
        """
        self.author_name = author_name
        self.workflow = Workflow("article_create_flow", tid=tid)
        self.context = self.workflow.context
        self._output_dir = Path("output/articles")  # 输出目录
        self._ensure_output_dir()

        print(f"tid: {self.workflow.get_tid()}")

        # 主题分析节点
        self.theme_analysis_node = ThemeAnalysisNode()
        # 元素提取节点
        self.elements_extraction_node = ElementsExtractionNode()
        # 结构分析节点
        self.structure_analysis_node = StructureAnalysisNode()
        # 角度钩选策略节点
        self.angle_hook_strategist_node = AngleHookStrategistNode()
        # 结构化草稿节点
        self.structured_draft_node = StructuredDraftNode()
        # 章节创作节点
        self.chapter_and_style_node = ChapterAndStyleNode()
        # 深度与细微差别增强节点
        self.depth_enhancer_node = DepthEnhancerNode()
        # 互动与争议注入节点
        self.engagement_injector_node = EngagementInjectorNode()

        # 添加节点到工作流
        self.workflow.add_node(self.theme_analysis_node)
        self.workflow.add_node(self.elements_extraction_node)
        self.workflow.add_node(self.structure_analysis_node)
        self.workflow.add_node(self.angle_hook_strategist_node)
        self.workflow.add_node(self.structured_draft_node)
        self.workflow.add_node(self.structured_draft_node)
        self.workflow.add_node(self.chapter_and_style_node)
        self.workflow.add_node(self.depth_enhancer_node)
        self.workflow.add_node(self.engagement_injector_node)

        # 设置节点执行顺序
        self.workflow.set_node_order([self.theme_analysis_node.name,
                                      self.elements_extraction_node.name,
                                      self.structure_analysis_node.name,
                                      self.angle_hook_strategist_node.name,
                                      self.structured_draft_node.name,
                                      self.structured_draft_node.name,
                                      self.chapter_and_style_node.name,
                                      self.depth_enhancer_node.name,
                                      self.engagement_injector_node.name,
                                      ])

    def _ensure_output_dir(self) -> None:
        """确保输出目录存在"""
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def _get_tid_dir(self, tid: str) -> Path:
        """获取任务ID对应的目录
        
        Args:
            tid: 任务ID
            
        Returns:
            Path: 任务目录路径
        """
        # 确保tid是字符串类型
        tid_str = str(tid)
        tid_dir = self._output_dir / tid_str
        tid_dir.mkdir(parents=True, exist_ok=True)
        return tid_dir

    def _save_markdown(self, content: str, file_path: Path) -> None:
        """保存Markdown内容到文件
        
        Args:
            content: Markdown内容
            file_path: 文件路径
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"文件已保存到: {file_path}")

    async def create_article(self, content: str) -> AsyncGenerator[Tuple[str, str], None]:
        """创建文章
        
        Args:
            content: 播客内容
            
        Yields:
            str: 处理过程中的流式输出
        """
        file_path = os.path.join("services/llm/article_agent/style/bi_sytle2.md")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                style_guide = f.read()

        # 准备初始输入
        initial_inputs = {
            "content": content,
            "style_guide": style_guide
        }

        # 执行工作流
        async for result in self.workflow.execute(initial_inputs):
            yield result

        # 获取各个阶段的结果
        draft = self.workflow.context.get("draft", "")
        enhancement_result = self.workflow.context.get("enhancement_result", "")
        engagement_injector = self.workflow.context.get("engagement_injector", "")
        
        # 获取任务ID并创建对应的目录
        tid = self.workflow.get_tid()
        tid_dir = self._get_tid_dir(tid)

        # 保存各个阶段的Markdown内容
        self._save_markdown(draft, tid_dir / "draft.md")
        self._save_markdown(enhancement_result, tid_dir / "enhancement.md")
        self._save_markdown(engagement_injector, tid_dir / "engagement.md")

        # 创建元信息文件
        meta_info = {
            "author": self.author_name,
            "tid": str(tid),  # 确保tid是字符串
            "created_at": datetime.now().isoformat(),
            "files": ["draft.md", "enhancement.md", "engagement.md"]
        }
        with open(tid_dir / "meta.json", 'w', encoding='utf-8') as f:
            json.dump(meta_info, f, ensure_ascii=False, indent=2)

    async def resume_from_node(self, node_name: str) -> AsyncGenerator[Tuple[str, str], None]:
        """从指定节点继续执行工作流
        
        Args:
            node_name: 要从中继续执行的节点名称
            
        Yields:
            str: 处理过程中的流式输出
        """
        async for result in self.workflow.resume_from_node(node_name):
            yield result
