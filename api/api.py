from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from transcriber import Transcriber, TranscriptionConfig
from json_processor import extract_segments_info
import torch

app = FastAPI(title="Whisper Transcription API")

# 配置信息
MODELS_DIR = r"./models"
WHISPER_MODEL_NAME = "large-v3-turbo"
ALIGN_MODEL_DIR = f"{MODELS_DIR}/wav2vec2_base"
PYANNOTE_CONFIG_PATH = "./pyannote_config.yaml"

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

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(request: TranscriptionRequest):
    # 验证文件是否存在
    if not os.path.exists(request.audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    try:
        import time
        transcriber = Transcriber(config)
        
        # 转写步骤
        start_time = time.time()
        transcriptions = transcriber.transcribe(audio_path=request.audio_path)
        transcribe_time = time.time() - start_time

        # 对齐步骤
        start_time = time.time()
        transcriptions = transcriber.align_transcriptions(transcriptions)
        align_time = time.time() - start_time

        # 说话人分离步骤
        start_time = time.time()
        transcriptions = transcriber.diarize_transcriptions(transcriptions)
        diarize_time = time.time() - start_time

        # 写入结果
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 