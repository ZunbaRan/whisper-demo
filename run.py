import argparse
import sys
import logging
import importlib.util

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='启动 Whisper 或 Deep Research 应用')
    parser.add_argument('app', choices=['whisper', 'deep-research', 'all'], 
                        help='要启动的应用: whisper, deep-research, 或 all (合并)')
    parser.add_argument('--host', default='0.0.0.0', help='服务器主机名')
    parser.add_argument('--port', type=int, default=8000, help='服务器端口')
    
    args = parser.parse_args()
    
    if args.app == 'whisper':
        # 启动 Whisper 应用
        import uvicorn
        logger.info("启动 Whisper 应用...")
        uvicorn.run("whisper_app.api.app:app", host=args.host, port=args.port)
        
    elif args.app == 'deep-research':
        # 检查 Deep Research 依赖是否可用
        if not is_deep_research_available():
            logger.error("Deep Research 依赖未安装，请先安装依赖")
            sys.exit(1)
            
        import uvicorn
        logger.info("启动 Deep Research 应用...")
        uvicorn.run("deep_research_app.api.app:app", host=args.host, port=args.port)
        
    elif args.app == 'all':
        # 启动合并应用
        import uvicorn
        logger.info("启动合并应用...")
        uvicorn.run("main:app", host=args.host, port=args.port)

def is_deep_research_available():
    """检查 Deep Research 依赖是否可用"""
    try:
        import arkitect
        import tavily_python
        return True
    except ImportError:
        return False

if __name__ == "__main__":
    main()