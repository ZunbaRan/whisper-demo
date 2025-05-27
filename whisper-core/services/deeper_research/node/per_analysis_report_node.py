import json
import os
import uuid
from datetime import datetime
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
        all_found_concrete_events: List[Dict] = []
        all_further_sub_queries: List[str] = []
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
        while len(all_found_concrete_events) < 20 and further_sub_queries and current_iteration < max_iterations:
            # 初始化搜索代理
            search_agent = SearchReportAgent()

            # 更新迭代次数并打印状态信息
            current_iteration += 1
            print(
                f"\n--- Iteration {current_iteration} --- Events found: {len(all_found_concrete_events)}, Further sub-queries available: {len(further_sub_queries)} ---")

            # 子查询随机取5个
            import random
            random.shuffle(further_sub_queries)
            sub_queries_to_process = further_sub_queries[:5]

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

        # 把 all_found_concrete_events 和 all_further_sub_queries 保存到 public/output/event/{time} 文件夹中
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join("public/output/event", timestamp)
        os.makedirs(output_dir, exist_ok=True)

        events_file_path = os.path.join(output_dir, "all_found_concrete_events.json")
        with open(events_file_path, "w", encoding="utf-8") as f:
            json.dump(all_found_concrete_events, f, ensure_ascii=False, indent=4)

        queries_file_path = os.path.join(output_dir, "all_further_sub_queries.json")
        with open(queries_file_path, "w", encoding="utf-8") as f:
            json.dump(all_further_sub_queries, f, ensure_ascii=False, indent=4)

        print(f"Events saved to: {events_file_path}")
        print(f"Sub queries saved to: {queries_file_path}")

        # 更新输出结果
        self.outputs = {
            "all_found_concrete_events": all_found_concrete_events,
            "all_further_sub_queries": all_further_sub_queries,
        }

    def _update_events_and_queries(self, all_found_concrete_events: List[Dict],
                                   all_further_sub_queries: List[str],
                                   further_sub_queries: List[str]) -> List[str] :
        if self.agent.format_res:
            if isinstance(self.agent.format_res.get("found_concrete_events"), list):
                # self.agent.format_res["found_concrete_events"] 数组中的元素并去到 all_found_concrete_events 中
                for event in self.agent.format_res["found_concrete_events"]:
                    if event not in all_found_concrete_events:
                        all_found_concrete_events.append(event)

            if isinstance(self.agent.format_res.get("further_sub_queries"), list):
                for sub_query in self.agent.format_res["further_sub_queries"]:
                    if sub_query not in all_further_sub_queries:
                        all_further_sub_queries.append(sub_query)

                further_sub_queries = self.agent.format_res["further_sub_queries"]

        return further_sub_queries
