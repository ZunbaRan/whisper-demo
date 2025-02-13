import os

# 获取项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 定义各种路径
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

# 具体模型路径
ALIGN_MODEL_DIR = os.path.join(MODELS_DIR, "wav2vec2_base")
PYANNOTE_CONFIG_PATH = os.path.join(CONFIG_DIR, "pyannote_config.yaml") 