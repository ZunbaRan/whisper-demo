# Offline WhisperX

## Pre-Trained Model(s) Download Links
whisperx (使用 3.2.0 版本以上，因为低版本需要VAD(Voice Activity Detection) Model，而这个模型作者已经不再提供下载)
所以使用 3.2.0 版本以上之后不再使用VAD Model

- [mobiuslabsgmbh/faster-whisper-large-v3-turbo](https://huggingface.co/mobiuslabsgmbh/faster-whisper-large-v3-turbo)
- [pyannote diairzation 3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
  - [pyannote/wespeaker-voxceleb-resnet34-LM](https://huggingface.co/pyannote/wespeaker-voxceleb-resnet34-LM)
  - [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)
- Wav2Vec2 - [PyTorch link](https://download.pytorch.org/torchaudio/models/wav2vec2_fairseq_base_ls960_asr_ls960.pth)

### 模型本地路径
![model-tree](./doc/model-tree.png "模型树")

- 或者修改配置到自己指定的路径(以最新的代码为主)
```python

MODELS_DIR = r"./models"
WHISPER_MODEL_NAME = "large-v3-turbo"
ALIGN_MODEL_DIR = f"{MODELS_DIR}/wav2vec2_base"
PYANNOTE_CONFIG_PATH = "./pyannote_config.yaml"
...
# change the config as per your requirements
config = TranscriptionConfig(
    whisper_model_name=WHISPER_MODEL_NAME,  # provide whisper model name or path
    whisper_download_root=MODELS_DIR,
    ...
    align_model_dir=ALIGN_MODEL_DIR,
    pyannote_config_path=PYANNOTE_CONFIG_PATH,
```

## required
1. python 3.9.7 (Python 版本太高无法兼容 numpy 版本)
2. 查看 requirements.txt 文件，安装依赖

## run
0. 执行代理（如果需要）
```bash
export https_proxy=http://127.0.0.1:7890
export http_proxy=http://127.0.0.1:7890
```
1. 创建venv
```bash
G:\env\python3.9.7\python -m venv whenv
```
2. 激活venv
```bash
.\whenv\Scripts\activate
```
3. 安装新的依赖:
```bash
pip install -r requirements.txt
```
4. 启动服务:
```bash
python .\run.py 
```
5. 测试服务:

- 测试cuda

```bash
python tests/test_cuda.py
```

服务启动后:
- API 文档访问地址: http://localhost:8000/docs
- 可以通过 POST 请求 http://localhost:8000/transcribe 端点来处理音频文件
- 返回结果包含处理时间和输出文件路径

主要特点:
1. 使用 FastAPI 框架提供 RESTful API
2. 保持了原有的转写功能和配置
3. 提供了详细的API文档
4. 包含错误处理
5. 返回处理时间统计
6. 支持异步处理

注意事项:
1. 确保音频文件路径是服务器可访问的
2. 输出文件会保存在 output 目录下
3. 服务默认运行在 8000 端口，可以根据需要修改
4. 建议在生产环境中添加适当的安全措施（如认证）
