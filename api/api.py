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
from .services import FollowService

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

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(request: TranscriptionRequest):
    # 验证文件是否存在
    if not os.path.exists(request.audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    try:
        import time
        transcriber = Transcriber(config)
        
        # 转写步骤
        print("\n=== 开始转写 ===")
        start_time = time.time()
        transcriptions = transcriber.transcribe(audio_path=request.audio_path)
        transcribe_time = time.time() - start_time
        print(f"转写耗时: {transcribe_time:.2f}秒")

        # 对齐步骤
        print("\n=== 开始对齐 ===")
        start_time = time.time()
        transcriptions = transcriber.align_transcriptions(transcriptions)
        align_time = time.time() - start_time
        print(f"对齐耗时: {align_time:.2f}秒")

        # 说话人分离步骤
        print("\n=== 开始分离说话人 ===")
        start_time = time.time()
        transcriptions = transcriber.diarize_transcriptions(transcriptions)
        diarize_time = time.time() - start_time
        print(f"分离耗时: {diarize_time:.2f}秒")

        start_time = time.time()
        transcriber.write_transcriptions(transcriptions=transcriptions)
        write_time = time.time() - start_time

        # 计算总时间
        total_time = transcribe_time + align_time + diarize_time + write_time
        
        # 获取输出文件路径
        filename = os.path.basename(request.audio_path)
        output_file = os.path.join("output", f"{os.path.splitext(filename)[0]}.json")

        # 处理JSON并创建简化版本
        simplified_output_file = extract_segments_info(output_file)

        return TranscriptionResponse(
            status="success",
            message="Transcription completed successfully",
            transcribe_time=round(transcribe_time, 2),
            align_time=round(align_time, 2),
            diarize_time=round(diarize_time, 2),
            write_time=round(write_time, 2),
            total_time=round(total_time, 2),
            output_file=output_file,
            simplified_output_file=simplified_output_file
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 