from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Dict, List, Optional, Any
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.transcriber import TranscriptionConfig
from config.paths import PROJECT_ROOT
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

app = FastAPI(title="Whisper Transcription API")

# 配置信息
MODELS_DIR = PROJECT_ROOT + "/models"
WHISPER_MODEL_NAME = "large-v3-turbo"
ALIGN_MODEL_DIR = f"{MODELS_DIR}/wav2vec2_base"
PYANNOTE_CONFIG_PATH = PROJECT_ROOT + "/config/pyannote_config.yaml"

# 使用 CUDA
device = "cuda"

# 基础配置
config = TranscriptionConfig(
    whisper_model_name=WHISPER_MODEL_NAME,
    whisper_download_root=MODELS_DIR,
    device=device,
    device_index=0,
    compute_type="float16",
    align_model_dir=ALIGN_MODEL_DIR,
    pyannote_config_path=PYANNOTE_CONFIG_PATH,
    language="en",
    diarize=True,
    output_dir="./output",
    output_format="json",
)

# 初始化服务
transcription_service = TranscriptionService(config)

# 初始化下载服务
download_service = DownloadService()

# 初始化工作流服务
workflow_service = WorkflowService(transcription_service)

# 初始化 RSS 服务
rss_service = RssService()

# 初始化 Apple RSS 服务
apple_rss_service = AppleRssService()

# 配置模板和静态文件
templates = Jinja2Templates(directory="templates")
# 暂时注释掉静态文件挂载
# app.mount("/static", StaticFiles(directory="static"), name="static")

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
    """下载指定ID的音频文件"""
    return await download_service.download_single_file(id)

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(request: TranscriptionRequest):
    """处理音频转写请求"""
    return await transcription_service.transcribe_audio(request.audio_path)


@app.get("/download/pending", response_model=DownloadResponse)
async def download_pending_audio():
    """下载所有未下载的音频文件"""
    return await download_service.download_pending_files()


@app.get("/transcribe/batch", response_model=BatchTranscriptionResponse)
async def batch_transcribe_audio():
    """批量转写已下载的音频文件"""
    return await transcription_service.batch_transcribe_downloaded_audio()


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

@app.get("/workflow/feed/{feed_name}", response_model=Dict[str, Any])
async def run_feed_workflow(feed_name: str, limit: int = 10):
    """处理指定 feed 的工作流程"""
    return await workflow_service.run_feed_workflow(feed_name, limit)

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

@app.get("/db/entries/count", response_model=Dict[str, int])
async def get_entries_count():
    """获取条目总数"""
    db_service = DBService()
    count = db_service.get_entries_count()
    return {"count": count}

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

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """处理 HTTP 异常"""
    return templates.TemplateResponse(
        "error.html", 
        {
            "request": request, 
            "status_code": exc.status_code,
            "detail": exc.detail
        },
        status_code=exc.status_code
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
    return templates.TemplateResponse(
        "error.html", 
        {
            "request": request, 
            "status_code": 500,
            "detail": "服务器内部错误"
        },
        status_code=500
    )

# 在应用启动时创建数据库表和必要的目录
@app.on_event("startup")
async def startup_event():
    # 创建 @data 目录
    os.makedirs("@data", exist_ok=True)
    
    # 创建数据库表
    db_service = DBService()
    db_service.create_tables()
    print("数据库表已创建")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 