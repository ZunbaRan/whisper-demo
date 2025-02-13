from core.transcriber import Transcriber, TranscriptionConfig
from config.paths import PROJECT_ROOT
import torch
import time
import os

# all required models are available in the models directory
MODELS_DIR = PROJECT_ROOT + "/models"

# FASTER_WHISPER_PATH = f"{MODELS_DIR}/faster_whisper_base"
WHISPER_MODEL_NAME = "large-v3-turbo"
ALIGN_MODEL_DIR = f"{MODELS_DIR}/wav2vec2_base"
PYANNOTE_CONFIG_PATH = PROJECT_ROOT + "/config/pyannote_config.yaml"

# 检查 CUDA 是否可用
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")
if device == "cuda":
    print(f"GPU: {torch.cuda.get_device_name(0)}")

# change the config as per your requirements
config = TranscriptionConfig(
    whisper_model_name=WHISPER_MODEL_NAME,  # provide whisper model name or path
    whisper_download_root=MODELS_DIR,
    device=device,                           # 直接使用cuda
    device_index=0,                         # 指定GPU索引
    compute_type="float16" if device == "cuda" else "float32",  # CPU 使用 float32
    align_model_dir=ALIGN_MODEL_DIR,
    pyannote_config_path=PYANNOTE_CONFIG_PATH,
    language="en",                          # 指定语言，避免语言检测
    diarize=True,
    output_dir="./output",
    output_format="json",
)

# audio_file = "./data/sample.wav"
audio_file = "G:\\project\\whisper-demo\\whisper-demo\\Lynn_Peters.mp3"

print("Current working directory:", os.getcwd())
print("Model directory:", os.path.abspath(MODELS_DIR))
print("Full model path:", os.path.join(MODELS_DIR, WHISPER_MODEL_NAME))

transcriber = Transcriber(config)

# 转写步骤
print("\n=== 开始转写 ===")
start_time = time.time()
transcriptions = transcriber.transcribe(audio_path=audio_file)
transcribe_time = time.time() - start_time
print(f"转写耗时: {transcribe_time:.2f}秒")

# 对齐步骤
print("\n=== 开始对齐 ===")
start_time = time.time()
transcriptions = transcriber.align_transcriptions(transcriptions)
align_time = time.time() - start_time
print(f"对齐耗时: {align_time:.2f}秒")

# 说话人分离步骤
print("\n=== 开始说话人分离 ===")
start_time = time.time()
transcriptions = transcriber.diarize_transcriptions(transcriptions)
diarize_time = time.time() - start_time
print(f"说话人分离耗时: {diarize_time:.2f}秒")

# 写入结果
print("\n=== 开始写入结果 ===")
start_time = time.time()
transcriber.write_transcriptions(transcriptions=transcriptions)
write_time = time.time() - start_time
print(f"写入耗时: {write_time:.2f}秒")

# 总结
print("\n=== 总耗时统计 ===")
total_time = transcribe_time + align_time + diarize_time + write_time
print(f"转写步骤: {transcribe_time:.2f}秒 ({(transcribe_time/total_time)*100:.1f}%)")
print(f"对齐步骤: {align_time:.2f}秒 ({(align_time/total_time)*100:.1f}%)")
print(f"说话人分离: {diarize_time:.2f}秒 ({(diarize_time/total_time)*100:.1f}%)")
print(f"写入结果: {write_time:.2f}秒 ({(write_time/total_time)*100:.1f}%)")
print(f"总耗时: {total_time:.2f}秒")
