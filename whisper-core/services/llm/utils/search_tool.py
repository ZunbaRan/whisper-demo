import asyncio
import json
import os
import uuid
from typing import List, Optional, Any # Added Any for agent type hint in helper

from services.llm.search_agent.ark_web_search_agent import ArkWebSearchAgent
from services.llm.search_agent.gemini_web_search_agent import GeminiWebSearchAgent
from services.llm.search_agent.kimi_web_search_agent import KimiWebSearchAgent
from services.llm.search_agent.search_res import SearchRes
from services.llm.search_agent.zhipu_web_search_agent import ZhipuWebSearchAgent
# Assuming SearchRes is implicitly handled by model_dump


async def _execute_search_agent(agent: Any, agent_name: str, query: str) -> Optional[object]:
    """Helper function to execute a single search agent's call and get format_res with retry logic."""
    print(f"\n*******************   Executing: {agent_name}   *******************")
    max_retries = 3
    
    for attempt in range(max_retries):
        print(f"Attempt {attempt + 1}/{max_retries} for {agent_name}...")
        try:
            # Fully consume the async generator from agent.call()
            # This is where the actual call to the agent happens.
            async for _role, _content in agent.call(content=query):
                pass  # We are interested in agent.format_res after the call completes.
            
            current_result = agent.format_res # Get the result after a potentially successful call

            if isinstance(current_result, SearchRes):
                print(f"Success: {agent_name} returned SearchRes on attempt {attempt + 1}.")
                return current_result  # Successful execution and correct type
            else:
                # agent.call() succeeded, but format_res is not of type SearchRes
                print(f"Warning: {agent_name} on attempt {attempt + 1} returned type {type(current_result)}, not SearchRes.")
                if attempt == max_retries - 1: # Last attempt
                    print(f"Failure: Max retries reached for {agent_name}. Final attempt did not return SearchRes.")
                    return None
                # No explicit 'continue' needed; loop will proceed to the next attempt.
                # Consider adding a small delay here if needed: await asyncio.sleep(1)

        except Exception as e:
            # An exception occurred during the agent.call() execution
            print(f"Error: {agent_name} agent call failed on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt == max_retries - 1: # Last attempt
                print(f"Failure: Max retries reached for {agent_name} due to errors during call.")
                return None
            # No explicit 'continue' needed; loop will proceed to the next attempt.
            # Consider adding a small delay here if needed: await asyncio.sleep(1)
            
    # This part is reached if all retries are exhausted (e.g., loop finishes without returning).
    # This primarily serves as a fallback, as specific failure returns are handled within the loop.
    print(f"Failure: All {max_retries} attempts exhausted for {agent_name} without success.")
    return None



# The @staticmethod decorator was present in the original image but seems out of place 
# for a top-level async function. Assuming it was for a class method previously.
# If this is a static method of a class, it should be part of that class definition.
# For now, removing it as it's presented as a standalone function.
async def web_search(query: str) -> str:
    """
    args:
        query: 搜索关键词
    return:
        所有agent搜索结果汇总的JSON文件路径
    """
    gemini_web_search_agent = GeminiWebSearchAgent()
    kimi_web_search_agent = KimiWebSearchAgent()
    ark_web_search_agent = ArkWebSearchAgent()
    zhipuai_agent = ZhipuWebSearchAgent(search_engine="Search-Std")

    tasks = [
        _execute_search_agent(gemini_web_search_agent, "Gemini", query),
        _execute_search_agent(kimi_web_search_agent, "Kimi", query),
        _execute_search_agent(zhipuai_agent, "Zhipu", query),
        _execute_search_agent(ark_web_search_agent, "Ark", query)
    ]

    # Run all search tasks concurrently
    results = await asyncio.gather(*tasks)

    # Filter out None results (e.g., if an agent failed or returned no data)
    all_search_results = [res for res in results if res is not None]
    # 把 all_search_results 中的内容合并成一个SearchRes对象
    if all_search_results:
        # 合并 summary_content
        combined_summary = "\n".join(
            res.summary_content for res in all_search_results 
            if res.summary_content
        )
        
        # 合并 search_references
        combined_references = []
        for res in all_search_results:
            if res.search_references:
                combined_references.extend(res.search_references)
        
        # 创建新的合并后的 SearchRes 对象
        # 使用第一个结果的 query（因为所有结果的 query 应该是一样的）
        merged_result = SearchRes(
            query=all_search_results[0].query,
            summary_content=combined_summary,
            search_references=combined_references
        )
        
        # 替换原来的结果列表
        all_search_results = [merged_result]

    # Generate UUID and create路径
    file_uuid = str(uuid.uuid4())
    output_dir = os.path.join("public", "output", "search_res", file_uuid)
    output_file_path = os.path.join(output_dir, "res.md")  # 改为 .md 扩展名

    os.makedirs(output_dir, exist_ok=True)

    markdown_content_str = ""
    # 将 SearchRes 转换为 Markdown 格式
    if all_search_results and isinstance(all_search_results[0], SearchRes):
        merged_result = all_search_results[0]
        markdown_content = [f"# 搜索查询\n{query}\n"]
        
        # 添加查询内容

        # 添加摘要内容
        if merged_result.summary_content:
            markdown_content.append(f"## 搜索结果摘要\n{merged_result.summary_content}\n")
        
        # 添加引用列表
        if merged_result.search_references:
            markdown_content.append("## 参考来源\n")
            for i, ref in enumerate(merged_result.search_references, 1):
                markdown_content.append(f"### 来源 {i}\n")
                markdown_content.append(f"- **标题**: {ref.title}")
                markdown_content.append(f"- **来源**: {ref.site}")
                markdown_content.append(f"- **链接**: {ref.url}")
                markdown_content.append(f"- **内容**: {ref.content}")
        
        # 写入 Markdown 文件
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(markdown_content))

        # markdown_content 转为 str
        markdown_content_str = "\n".join(markdown_content)
    else:
        # 如果没有有效结果，创建一个空的 Markdown 文件
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write("# 无搜索结果\n")

    print(f"\nSearch results saved to: {output_file_path}")

    return markdown_content_str