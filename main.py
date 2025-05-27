from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
import logging
import importlib.util

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建主应用
app = FastAPI(title="Whisper & Deep Research")

# 加载 Whisper 相关路由
from whisper_app.api.routes import register_whisper_routes
register_whisper_routes(app)

# 检测并加载 Deep Research 相关路由
def is_deep_research_available():
    """检查 Deep Research 依赖是否可用"""
    try:
        import arkitect
        import tavily_python
        return True
    except ImportError:
        return False

if is_deep_research_available():
    try:
        logger.info("Deep Research 依赖已安装，加载相关路由...")
        # 导入并注册 Deep Research 相关路由
        from deep_research_app.api.routes import register_deep_research_routes
        register_deep_research_routes(app)
    except Exception as e:
        logger.error(f"加载 Deep Research 路由失败: {str(e)}")
else:
    logger.warning("Deep Research 依赖未安装，相关功能不可用")

# 启动服务器的入口点
def start_all():
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start_all() 