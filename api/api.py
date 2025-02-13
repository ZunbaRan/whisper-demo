from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.transcriber import Transcriber, TranscriptionConfig
from utils.json_utils import extract_segments_info
from config.paths import PROJECT_ROOT
from typing import Optional, List, Dict, Any
import requests
from .models import FollowEntriesResponse
from .services import FollowService, TranscriptionService, DownloadService

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

class TranscriptionRequest(BaseModel):
    audio_path: str

class TranscriptionResponse(BaseModel):
    status: str
    message: str
    transcribe_time: float
    align_time: float
    diarize_time: float
    write_time: float
    total_time: float
    output_file: str
    simplified_output_file: str

class FollowEntry(BaseModel):
    read: bool
    view: int
    entries: Dict[str, Any]
    feeds: Dict[str, Any]
    collections: Optional[Dict[str, Any]]
    subscriptions: Dict[str, Any]
    settings: Dict[str, Any]

class FollowRequest(BaseModel):
    cookie: str
    is_archived: bool = False
    view: int = 4

class FollowCountRequest(BaseModel):
    cookie: str
    num: int = 10

class DownloadResponse(BaseModel):
    success: List[str]
    failed: List[str]

class BatchTranscriptionResponse(BaseModel):
    success: List[str]
    failed: List[str]

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(request: TranscriptionRequest):
    """处理音频转写请求"""
    return await transcription_service.transcribe_audio(request.audio_path)

@app.post("/follow/entries", response_model=FollowEntriesResponse)
async def get_follow_entries(request: FollowRequest):
    return await FollowService.feed_req(
        cookie=request.cookie,
        is_archived=request.is_archived,
        view=request.view
    )

@app.post("/follow/entries/batch", response_model=FollowEntriesResponse)
async def get_entries_batch(request: FollowCountRequest):
    """获取指定数量的条目，如果第一次请求不够，会继续请求直到达到指定数量"""
    return await FollowService.fetch_entries_with_count(
        cookie=request.cookie,
        num=request.num
    )

@app.get("/download/pending", response_model=DownloadResponse)
async def download_pending_audio():
    """下载所有未下载的音频文件"""
    return await download_service.download_pending_files()

@app.get("/transcribe/batch", response_model=BatchTranscriptionResponse)
async def batch_transcribe_audio():
    """批量转写已下载的音频文件"""
    return await transcription_service.batch_transcribe_downloaded_audio()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 