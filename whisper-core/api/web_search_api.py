import json
import logging
from typing import Dict, Any, List, Tuple

from fastapi import APIRouter, HTTPException, Body
from starlette.responses import StreamingResponse

from services.deep_research.deep_research import DeepResearch
from services.deep_research.markdown_report import MarkdownReport
from services.deep_research.models import ChatRequest, Message
from services.llm.search_agent.gemini_web_search_agent import GeminiWebSearchAgent
from services.llm.search_agent.kimi_web_search_agent import KimiWebSearchAgent
from services.llm.search_agent.zhipu_web_search_agent import ZhipuWebSearchAgent

router = APIRouter()
logger = logging.getLogger(__name__)
@router.post("/gemini-search")
async def web_search_api(query:str) -> str:
    """
    args:
        query: 搜索关键词
    return:
        搜索结果
    """
    web_search_agent = GeminiWebSearchAgent()
    kimi_web_search_agent = KimiWebSearchAgent()

    # call_results: List[str] = []
    # async for role, content in web_search_agent.call(query = query):
    #     call_results.append(content)

    # res_content = web_search_agent.context["res_content"]
    # parts = web_search_agent.context["parts"]
    
    # kimi_call_results: List[str] = []
    # async for role, content in kimi_web_search_agent.call(query = query):
    #     kimi_call_results.append(content)

    call_results: list[str]  = []
    zhipuai_agent = ZhipuWebSearchAgent(search_engine = "Search-Std")
    async for role, content in zhipuai_agent.call(content = "帮我查询一下最近一周有什么 “社会热点与现象观察”的内容 ，并且具有爆款特征"):
        call_results.append(content)

    # return "".join(kimi_call_results)
    return ""

@router.post("/deep_research")
async def deep_research(
        request: Dict[str, Any] = Body(
            ...,
            example={
                "question": "请研究一下量子计算机的发展现状",
                "stream": True
            }
        )
):
    """
    深度研究接口

    Parameters:
    - question: 研究问题
    - stream: 是否使用流式输出

    Returns:
    - StreamingResponse: 流式响应
    """
    question = request.get("question")
    stream = request.get("stream", True)

    if not question:
        raise HTTPException(status_code=400, detail="缺少研究问题")

    # 创建请求
    chat_request = ChatRequest(
        messages=[
            Message(
                role="user",
                content=question
            )
        ],
        stream=stream
    )

    # 创建深度研究实例
    deep_research = DeepResearch()
    report = MarkdownReport(question)

    print(f"\n开始深度研究问题：{question}")
    print("-" * 50)

    async def generate_response():
        if stream:
            async for chunk in deep_research.astream_deep_research(chat_request, question):
                chunk_str = chunk.decode('utf-8')
                if chunk_str.startswith('data: '):
                    if str.replace(chunk_str[6:], "\n", "", ) == "[PLANNING_DONE]":
                        print("\n" + "-" * 50)
                        print("规划完成")
                        report.add_planning_done()
                        yield chunk
                        pass

                    try:
                        data = json.loads(chunk_str[6:])
                        if data == "[DONE]":
                            print("\n" + "-" * 50)
                            print("研究完成")
                            report.add_research_done()
                            yield chunk
                            break
                        else:
                            pass
                    except Exception as e:
                        print("出现错误")
                        print(e)

                    # 处理元数据
                    if 'metadata' in data:
                        metadata = data['metadata']
                        if metadata.get('search_state') == 'searching':
                            search_keywords = metadata['search_keywords']
                            print(f"\n正在搜索关键词：{', '.join(search_keywords)}")
                            report.add_search_keywords(search_keywords)
                        elif metadata.get('search_state') == 'searched':
                            if metadata.get('search_keywords'):
                                search_results = metadata['search_results']
                                print(f"搜索完成，找到 {len(search_results)} 条结果")

                                # 打印搜索结果
                                for idx, result in enumerate(search_results, 1):
                                    print(f"\n结果 {idx}:")
                                    print(f"查询词: {result['query']}")
                                    print(f"摘要: {result['summary_content']}")
                                    print("参考来源:")
                                    for ref in result['search_references']:
                                        print(f"- {ref['title']}")
                                        print(f"  来源: {ref['site']}")
                                        print(f"  链接: {ref['url']}")
                                        print(f"  内容: {ref['content'][:200]}...")

                                    # 存储单个搜索结果
                                    report.add_search_result(result)
                            else:
                                print("搜索完成---")
                        yield chunk
                        continue

                    # 处理内容
                    if 'choices' in data and data['choices'][0]['delta']:
                        delta = data['choices'][0]['delta']
                        if delta.get('reasoning_content'):
                            content = delta['reasoning_content']
                            print(content, end='', flush=True)
                            report.add_content(content)
                        if delta.get('content'):
                            content = delta['content']
                            print(content, end='', flush=True)
                            report.add_content(content)
                        yield chunk

            # 保存 markdown 文档
            filename = report.save()
            print(f"\n研究报告已保存到: {filename}")

    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream"
    )
