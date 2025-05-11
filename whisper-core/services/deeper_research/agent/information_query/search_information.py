import asyncio
from typing import List, Optional, Any # Added Any for agent type hint in helper

from services.deeper_research.agent.information_query.gemini_information_search_agent import \
    GeminiInformationSearchAgent
from services.deeper_research.agent.information_query.kimi_information_search_agent import KimiInformationSearchAgent
from services.llm.search_agent.search_res import SearchRes


async def _execute_search_agent(agent: Any, agent_name: str, query: str) -> Optional[object]:
    print(f"\n=======================   Executing: {agent_name}  =======================")
    max_retries = 3
    
    for attempt in range(max_retries):
        print(f"Attempt {attempt + 1}/{max_retries} for {agent_name}...")
        try:

            async for _role, _content in agent.call(content=query):
                pass
            
            current_result = agent.format_res
            return current_result

        except Exception as e:
            print(f"Error: {agent_name} agent call failed on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt == max_retries - 1: # Last attempt
                print(f"Failure: Max retries reached for {agent_name} due to errors during call.")
                return None


    print(f"Failure: All {max_retries} attempts exhausted for {agent_name} without success.")
    return None


async def search_information(query: str) -> str:
    """
    args:
        query: 搜索关键词
    return:
        所有agent搜索结果汇总的JSON文件路径
    """
    gemini_web_search_agent = GeminiInformationSearchAgent()
    kimi_web_search_agent = KimiInformationSearchAgent()

    query_str = """'
    # role: 你是一位专业的搜索助手，用户现在正处于一个深度研究的情境。你需要借助搜索工具帮用户完成信息的收集。
    # background: 用户输入了一个 json 格式的问题， 其中 "question" 是用户思考的问题，"answer_focus" 是解答该问题时应侧重的分析方向或内容要点， "information_needed_queries" 是你需要帮助用户搜索总结的内容。
    # content：以下为用户输入的内容
        <query>
        {query}
        </query>
    # workflow：请把 "question" 和 "answer_focus" 作为背景思考，然后根据 "information_needed_queries" 中的关键词，使用搜索工具进行搜索，获取相关信息。
    # output_format: 在<search_results>输出对information_needed_queries的搜索结果，在<link>搜索结果的来源网站的url
        ## output_example：
        <search_results>
            对于 "information_needed_queries" 的搜索结果
        </search_results>
        <link>
            对于 "information_needed_queries" 的搜索结果的来源网站url
        </link>
        """

    query_content = query_str.format(query=query)

    tasks = [
        _execute_search_agent(gemini_web_search_agent, "Gemini", query_content),
        _execute_search_agent(kimi_web_search_agent, "Kimi", query_content),
    ]

    # Run all search tasks concurrently
    results = await asyncio.gather(*tasks)

    # Filter out None results (e.g., if an agent failed or returned no data)
    all_search_results = [res for res in results if res is not None]

    combined_summary = ''
    if all_search_results:
        combined_summary = "\n".join(res for res in all_search_results)

    return combined_summary