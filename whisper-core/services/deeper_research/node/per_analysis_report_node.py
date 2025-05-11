import uuid
from re import search
from typing import AsyncGenerator, Tuple, List, Dict, Any

from services.deeper_research.agent.per_analysis_report import PerAnalysisReport
from services.deeper_research.agent.search_report import SearchReportAgent
from services.llm.workflow.base.node import Node
from services.llm.workflow.base.output_manager import OutputManager


class PerAnalysisReportNode(Node):
    def __init__(self, tid: str = uuid.uuid4(), name: str = "per_analysis_report"):
        super().__init__(name, PerAnalysisReport(), tid)
        self.output_manager = OutputManager("public/output")

    async def call(self) -> AsyncGenerator[Tuple[str, str], None]:

        """
        异步调用方法，用于与主代理进行通信，获取事件信息。

        此方法通过异步生成器返回角色和内容的元组。
        它迭代地查询事件，直到满足停止条件。
        """
        # 初始化变量
        all_found_concrete_events: List[str] = []
        further_sub_queries: List[str] = []
        max_iterations = 5
        current_iteration = 0

        # 初始调用主代理
        print("Initial call to the main agent...")
        async for role, content in self.agent.call(**self.context):
            yield role, content

        # 处理主代理的响应
        further_sub_queries = self._update_events_and_queries(all_found_concrete_events, further_sub_queries)

        # 循环直到找到足够的具体事件或没有更多的子查询或达到最大迭代次数
        while len(all_found_concrete_events) < 10 and further_sub_queries and current_iteration < max_iterations:
            # 初始化搜索代理
            search_agent = SearchReportAgent()

            # 更新迭代次数并打印状态信息
            current_iteration += 1
            print(
                f"\n--- Iteration {current_iteration} --- Events found: {len(all_found_concrete_events)}, Further sub-queries available: {len(further_sub_queries)} ---")

            # 处理子查询
            sub_queries_to_process = further_sub_queries[:3]

            # 检查是否有子查询需要处理
            if not sub_queries_to_process:
                print("No more sub-queries to process in this iteration, but loop condition met. Breaking.")
                break

            # 更新上下文并调用搜索代理
            print(f"Processing {len(sub_queries_to_process)} sub_queries: {sub_queries_to_process}")
            self.context["sub_queries"] = sub_queries_to_process

            async for _s_role, _s_content in search_agent.call(**self.context):
                pass

            # 处理搜索代理的响应
            current_sub_search_report = search_agent.format_res
            self.context["preliminary_report_markdown"] = current_sub_search_report

            async for role, content in self.agent.call(**self.context):
                pass

            # 重置 further_sub_queries
            further_sub_queries = self._update_events_and_queries(all_found_concrete_events, further_sub_queries)

            # 打印当前迭代后的事件和子查询数量
            print(f"Events after iteration {current_iteration}: {len(all_found_concrete_events)}")
            print(
                f"Further sub-queries after iteration {current_iteration}: {len(further_sub_queries)} -> {further_sub_queries}")

        # 检查是否达到最大迭代次数
        if current_iteration == max_iterations:
            print(f"Max iterations ({max_iterations}) reached.")

        # 打印循环结束后的总事件数量
        print(f"\nLoop finished. Total concrete events found: {len(all_found_concrete_events)}")

        # 更新输出结果
        self.outputs = {
            "all_found_concrete_events": all_found_concrete_events,
        }

    def _update_events_and_queries(self, all_found_concrete_events: List[str],
                                   further_sub_queries: List[str]):
        if self.agent.format_res:
            if isinstance(self.agent.format_res.get("found_concrete_events"), list):
                all_found_concrete_events.append(self.agent.format_res["found_concrete_events"])
            if isinstance(self.agent.format_res.get("further_sub_queries"), list):
                further_sub_queries = self.agent.format_res["further_sub_queries"]
        return further_sub_queries
