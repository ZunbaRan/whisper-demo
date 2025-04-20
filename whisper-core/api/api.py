import os
import sys
from datetime import datetime

from services.deep_research.deep_research import DeepResearch
from services.deep_research.models import ChatRequest, Message
from services.deep_research.markdown_report import MarkdownReport

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(project_root))

from fastapi import FastAPI, Request, HTTPException, APIRouter, Body
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from services.llm.utils.logger import logger
from services.workflow.longTextToArticle import LongTextToSimpleArticle

import json

from typing import Dict, List, Optional, Any
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.transcriber import TranscriptionConfig
# from config.paths import PROJECT_ROOT
from services import (
    TranscriptionService,
    DownloadService,
    WorkflowService
)

# 从本地 models 导入
from .models import (
    TranscriptionRequest,
    TranscriptionResponse,
    BatchTranscriptionResponse,
    FollowRequest,
    FollowCountRequest,
    FollowEntriesResponse,
    SingleDownloadResponse,
    DownloadResponse
)

# 导入新的服务
from services.rss_service import RssService
from services.apple_rss_service import AppleRssService
from services.db_service import DBService
from services.llm.manager.llm_service_manager import llm_service_manager
from services.llm.composite.composite import CompatibleComposite
from services.llm.clients.LLM_client import llm_client

# 引入 Deep Research 相关依赖
import logging
import os
import sys
from typing import AsyncIterable, Union, Dict, Any, List
from pathlib import Path

# 确保 deep_research 模块可以被导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 确保模板目录存在
templates_dir = Path("templates")
if not templates_dir.exists():
    templates_dir.mkdir(parents=True)

# 修改 FastAPI 实例化，添加更多文档信息
app = FastAPI(
    title="Whisper Transcription API",
    description="音频转写和处理服务 API",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI 地址，可以通过 /docs 访问
    redoc_url="/redoc",  # ReDoc 地址，可以通过 /redoc 访问
    openapi_url="/openapi.json"  # OpenAPI 文档地址
)

# 配置信息
# MODELS_DIR = PROJECT_ROOT + "/models"
# WHISPER_MODEL_NAME = "large-v3-turbo"
# ALIGN_MODEL_DIR = f"{MODELS_DIR}/wav2vec2_base"
# PYANNOTE_CONFIG_PATH = PROJECT_ROOT + "/config/pyannote_config.yaml"

# 使用 CUDA
device = "cuda"

# 基础配置
# config = TranscriptionConfig(
#     whisper_model_name=WHISPER_MODEL_NAME,
#     whisper_download_root=MODELS_DIR,
#     device=device,
#     device_index=0,
#     compute_type="float16",
#     align_model_dir=ALIGN_MODEL_DIR,
#     pyannote_config_path=PYANNOTE_CONFIG_PATH,
#     language="en",
#     diarize=True,
#     output_dir="./output",
#     output_format="json",
# )
#
# # 初始化服务
# transcription_service = TranscriptionService(config)

# 初始化下载服务
download_service = DownloadService()

# 初始化工作流服务
# workflow_service = WorkflowService(transcription_service)

# 初始化 RSS 服务
rss_service = RssService()

# 初始化 Apple RSS 服务
apple_rss_service = AppleRssService()

# 配置模板和静态文件
templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.post("/follow/entries/batch", response_model=FollowEntriesResponse)
async def get_entries_batch(request: FollowCountRequest):
    """获取指定数量的条目"""
    return await rss_service.fetch_entries_with_count(
        cookie=request.cookie,
        num=request.num,
        fetch_mode=request.fetch_mode
    )


@app.get("/download/{id}", response_model=SingleDownloadResponse)
async def download_single_audio(id: str):
    """
    下载指定ID的音频文件
    
    Parameters:
    - id: 音频文件的唯一标识符
    
    Returns:
    - SingleDownloadResponse: 下载结果响应
    """
    return await download_service.download_single_file(id)


# @app.post("/transcribe", response_model=TranscriptionResponse)
# async def transcribe_audio(request: TranscriptionRequest):
#     """
#     处理音频转写请求
#
#     Parameters:
#     - audio_path: 音频文件路径
#
#     Returns:
#     - TranscriptionResponse: 包含转写结果的响应对象
#     """
#     return await transcription_service.transcribe_audio(request.audio_path)


@app.get("/download/pending", response_model=DownloadResponse)
async def download_pending_audio():
    """
    下载所有未下载的音频文件
    
    Returns:
    - DownloadResponse: 批量下载结果响应
    """
    return await download_service.download_pending_files()

#
# @app.get("/transcribe/batch", response_model=BatchTranscriptionResponse)
# async def batch_transcribe_audio():
#     """批量转写已下载的音频文件"""
#     return await transcription_service.batch_transcribe_downloaded_audio()


@app.get("/rss/download/{feed_name}", response_model=Dict[str, Any])
async def download_rss_audio_by_feed(feed_name: str):
    """下载指定 feed 的未下载音频文件"""
    return await apple_rss_service.download_feed_audio(feed_name)


@app.get("/rss/transcribe/{feed_name}", response_model=Dict[str, Any])
async def transcribe_rss_audio_by_feed(feed_name: str):
    """转写指定 feed 的已下载但未转写的音频文件"""
    return await apple_rss_service.transcribe_feed_audio(feed_name)


@app.get("/rss/workflow/{feed_name}", response_model=Dict[str, Any])
async def run_rss_workflow(feed_name: str):
    """运行指定 feed 的完整工作流：获取数据、下载并转写"""
    return await apple_rss_service.process_feed_workflow(feed_name)


@app.get("/rss/process/{feed_name}", response_model=Dict[str, Any])
async def process_single_rss_feed(feed_name: str):
    """处理指定名称的 RSS 源"""
    print(f"收到处理 RSS 源请求: {feed_name}")
    try:
        result = await apple_rss_service.process_single_feed(feed_name)
        print(f"处理 RSS 源完成: {feed_name}, 状态: {result.get('status')}")
        return result
    except Exception as e:
        print(f"处理 RSS 源时发生异常: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"处理 RSS 源失败: {str(e)}")


@app.get("/db/entries", response_model=Dict[str, Any])
async def get_all_entries(limit: int = 100, offset: int = 0, count: bool = False):
    """获取数据库中的所有条目"""
    db_service = DBService()
    entries = db_service.get_entries(limit, offset)

    if count:
        total = db_service.get_entries_count()
        return {"entries": entries, "total": total}
    else:
        return {"entries": entries}


@app.get("/db/entries/count", response_model=Dict[str, int])
async def get_entries_count():
    """获取条目总数"""
    try:
        db_service = DBService()
        count = db_service.get_entries_count()
        return {"count": count}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"获取条目总数失败: {str(e)}"}
        )


@app.get("/db/entries/{id}", response_model=Dict[str, Any])
async def get_entry_by_id(id: str):
    """根据 ID 获取特定条目"""
    db_service = DBService()
    entry = db_service.get_entry_by_id(id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Entry with ID {id} not found")
    return entry


@app.get("/db/stats", response_model=Dict[str, Any])
async def get_database_stats():
    """获取数据库统计信息"""
    db_service = DBService()
    return db_service.get_stats()


# @app.get("/workflow/feed/{feed_name}", response_model=Dict[str, Any])
# async def run_feed_workflow(feed_name: str, limit: int = 10):
#     """处理指定 feed 的工作流程"""
#     return await workflow_service.run_feed_workflow(feed_name, limit)


@app.post("/db/clear", response_model=Dict[str, bool])
async def clear_database():
    """清空数据库中的所有数据"""
    db_service = DBService()
    success = db_service.clear_database()
    return {"success": success}


@app.post("/rss/feeds", response_model=Dict[str, Any])
async def add_rss_feed(title: str, url: str):
    """添加新的 RSS 源"""
    db_service = DBService()
    feed = db_service.save_rss_feed(title, url)
    if not feed:
        raise HTTPException(status_code=400, detail="Failed to add RSS feed")
    return feed


@app.get("/rss/feeds", response_model=List[Dict[str, Any]])
async def get_rss_feeds():
    """获取所有 RSS 源"""
    db_service = DBService()
    return db_service.get_all_rss_feeds()


@app.delete("/rss/feeds/{feed_id}", response_model=Dict[str, bool])
async def delete_rss_feed(feed_id: int):
    """删除 RSS 源"""
    db_service = DBService()
    success = db_service.delete_rss_feed(feed_id)
    return {"success": success}


# 添加 HTML 页面路由
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """首页"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/feeds", response_class=HTMLResponse)
async def feeds_page(request: Request):
    """Feed 列表页面"""
    return templates.TemplateResponse("feeds.html", {"request": request})


@app.get("/entries", response_class=HTMLResponse)
async def entries_page(request: Request):
    """条目列表页面"""
    return templates.TemplateResponse("entries.html", {"request": request})


@app.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    """统计信息页面"""
    return templates.TemplateResponse("stats.html", {"request": request})


@app.get("/rss/config", response_class=HTMLResponse)
async def rss_config_page(request: Request):
    """RSS 配置页面"""
    return templates.TemplateResponse("rss_config.html", {"request": request})


@app.get("/composite_chat", response_class=HTMLResponse)
async def composite_chat_page(request: Request):
    """组合模型对话页面"""
    return templates.TemplateResponse(
        "composite_chat.html",
        {"request": request, "is_stream_page": True}
    )


@app.get("/article_convert")
async def article_convert_page(request: Request):
    """
    文章转换页面
    """
    return templates.TemplateResponse(
        "article_convert.html",
        {"request": request, "is_stream_page": True}
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """处理 HTTP 异常"""
    if request.headers.get("accept") == "application/json":
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail}
        )
    try:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "status_code": exc.status_code,
                "detail": exc.detail
            },
            status_code=exc.status_code
        )
    except:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail}
        )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证错误"""
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "status_code": 422,
            "detail": "请求参数验证失败"
        },
        status_code=422
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理一般异常"""
    error_msg = str(exc)
    if request.headers.get("accept") == "application/json":
        return JSONResponse(
            status_code=500,
            content={"error": error_msg}
        )
    try:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "status_code": 500,
                "detail": error_msg
            },
            status_code=500
        )
    except:
        return JSONResponse(
            status_code=500,
            content={"error": error_msg}
        )


# 在应用启动时创建数据库表和必要的目录
@app.on_event("startup")
async def startup_event():
    try:
        # 创建必要的目录
        os.makedirs("@data", exist_ok=True)
        os.makedirs("templates", exist_ok=True)

        # 确保错误模板文件存在
        if not Path("templates/error.html").exists():
            with open("templates/error.html", "w", encoding="utf-8") as f:
                f.write("""{% extends "base.html" %}
{% block title %}Error {{ status_code }}{% endblock %}
{% block content %}
<div class="container mt-5">
    <div class="alert alert-danger">
        <h4 class="alert-heading">Error {{ status_code }}</h4>
        <p>{{ detail }}</p>
    </div>
    <a href="/" class="btn btn-primary">返回首页</a>
</div>
{% endblock %}""")

        if not Path("templates/base.html").exists():
            with open("templates/base.html", "w", encoding="utf-8") as f:
                f.write("""<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    {% block content %}{% endblock %}
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>""")

        # 创建数据库表
        db_service = DBService()
        db_service.create_tables()
        print("数据库表已创建")

    except Exception as e:
        print(f"启动时出错: {str(e)}")
        raise


# 修改启动函数
def start_app():
    import uvicorn
    # 注意这里的模块路径
    uvicorn.run("whisper-core.api.api:app", host="0.0.0.0", port=8001, reload=True)


# @app.post("/workflow/entry/{entry_id}", response_model=Dict[str, Any])
# async def process_single_entry(entry_id: str):
#     """
#     处理单个条目的下载和转写
#
#     Parameters:
#     - entry_id: 条目的唯一标识符
#
#     Returns:
#     - Dict: 包含处理结果的响应对象，包括：
#         - id: 条目ID
#         - title: 条目标题
#         - success: 是否处理成功
#         - steps: 处理步骤的详细信息
#         - error: 如果处理失败，包含错误信息
#     """
#     try:
#         result = await workflow_service.process_single_entry(entry_id)
#         return result
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"处理条目失败: {str(e)}"
#         )


@app.get("/output/{entry_id}.txt")
async def get_transcription(entry_id: str):
    """获取转写文件内容的API"""
    try:
        # 构建文件路径
        file_path = os.path.join("output", f"{entry_id}.txt")

        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="转写文件不存在")

        # 读取文件内容
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        return content

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取转写文件失败: {str(e)}")


@app.post("/llm/chat/{model_name}")
async def chat_with_llm(
        model_name: str,
        messages: List[Dict[str, str]] = Body(..., example=[{
            "role": "user",
            "content": "你好，请介绍一下你自己"
        }])
):
    """与 LLM 模型进行对话"""
    model_name = "Gemini/Gemini-2.0-Flash-thinking"
    print(f"\n开始调用模型 {model_name}")
    print(f"输入消息: {json.dumps(messages, ensure_ascii=False, indent=2)}")
    print("\n模型响应内容:")

    async def generate_response():
        try:
            # 获取客户端和配置
            result = llm_service_manager.get_client(model_name)
            if not result:
                raise ValueError(f"无法获取模型 {model_name} 的客户端")

            client, config = result

            # 打印请求信息
            print(f"请求地址: {config.api_base_url + config.api_request_address}")
            print(f"模型ID: {config.model_id}")
            if client.proxy:
                print(f"使用代理: {client.proxy}")

            full_response = []  # 用于收集完整响应
            async for role, content in client.stream_chat(
                    messages=messages,
                    model=config.model_id
            ):
                # 打印每个片段的内容（不换行）
                print(content, end="", flush=True)

                full_response.append(content)
                response_data = {
                    "role": role,
                    "content": content
                }
                yield f"data: {json.dumps(response_data, ensure_ascii=False)}\n\n"

            # 打印完整响应的分隔线
            print("\n" + "-" * 50)

            yield "data: [DONE]\n\n"

        except Exception as e:
            error_msg = f"对话发生错误: {str(e)}"
            print(f"\n{error_msg}")
            print("-" * 50 + "\n")

            error_data = {
                "error": error_msg
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream"
    )


@app.post("/llm/composite/chat")
async def composite_chat(
        request: Dict[str, Any] = Body(
            ...,
            example={
                "messages": [{"role": "user", "content": "你好"}],
                "deepseek_model": "deepseek-reasoner",
                "target_model": "Gemini/Gemini-2.0-Flash"
            }
        )
):
    try:
        messages = request.get("messages", [])
        deepseek_model = request.get("deepseek_model", "")
        target_model = request.get("target_model", "")
        logger.info(f"Composite chat request: {request}")

        deepseek_model = "Volcengine/DeepSeek-R1"
        target_model = "Gemini/Gemini-2.0-Flash"

        if not messages or not deepseek_model or not target_model:
            raise HTTPException(status_code=400, detail="缺少必要的参数")

        async def generate_response():
            composite = CompatibleComposite()

            async for chunk in composite.chat_completions_with_stream(
                    messages=messages,
                    deepseek_model=deepseek_model,
                    target_model=target_model
            ):
                yield chunk

        return StreamingResponse(generate_response(), media_type="text/event-stream")
    except Exception as e:
        logger.error(f"Composite chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/workflow/convert_article", response_model=Dict[str, Any])
async def convert_article(
        request: Dict[str, Any] = Body(
            ...,
            example={
                "task_id": "20250329153000"
            }
        )
):
    """
    处理长文本转文章的请求
    请求体需要包含文件路径
    """
    try:
        file_path = 'output/' + request.get('task_id') + '.txt'

        if not file_path:
            return JSONResponse(
                status_code=400,
                content={"error": "缺少文件路径参数"}
            )

        # 生成任务ID（使用时间戳）
        task_id = request.get('task_id')

        # 创建服务实例
        service = LongTextToSimpleArticle()

        # 使用 stream_with_context 处理流式响应
        return StreamingResponse(
            service.execute_workflow(file_path, task_id),
            media_type='text/event-stream'
        )

    except Exception as e:
        logger.error('处理文章转换请求失败', extra={'error': str(e)})
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/deep_research")
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


@app.post("/llm/test_gemini")
async def test_gemini(
    message: str = Body(
        ...,
        description="请介绍一下你自己"
    ),
    model_name: str = Body(
        "Gemini/Gemini-2.0-Flash",
        description="要使用的 Gemini 模型名称"
    )
):
    """测试 Gemini 模型调用

    Args:
        messages: 对话消息列表
        model_name: 要使用的 Gemini 模型名称

    Returns:
        StreamingResponse: 流式响应
    """
    print(f"\n开始测试 Gemini 模型: {model_name}")
    print(f"输入消息: {message}")
    print("\n模型响应内容:")

    async def generate_response():
        result = llm_client.chat_stream(model_name, [{"role": "user", "content": message}])

        full_response = []  # 用于收集完整响应
        async for role, content in result:
            # 打印每个片段的内容（不换行）
            print(content, end="", flush=True)

            full_response.append(content)

            yield f"data: full_response: {json.dumps(content, ensure_ascii=False)}\n\n"

        # 打印完整响应的分隔线
        print("\n" + "-" * 50)


    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream"
    )


if __name__ == "__main__":
    start_app()

from api.angle_hook_api import router as angle_hook_router
app.include_router(angle_hook_router, prefix="/angle-hook", tags=["angle-hook"])

from api.author_style_api import router as author_style_router
app.include_router(author_style_router, prefix="/author-style", tags=["author-style"])
