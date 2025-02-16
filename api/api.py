from fastapi import FastAPI
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

@app.post("/workflow/complete", response_model=Dict[str, List[str]])
async def run_complete_workflow(cookie: str):
    """运行完整的工作流程：获取数据、下载并处理文件"""
    return await workflow_service.run_complete_workflow(cookie)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 