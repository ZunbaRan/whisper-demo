import logging
import os
from logging.handlers import RotatingFileHandler

import colorlog
import sys


def setup_logger(name: str = "DeepClaude") -> logging.Logger:
    """设置一个彩色的logger

    Args:
        name (str, optional): logger的名称. Defaults to "DeepClaude".

    Returns:
        logging.Logger: 配置好的logger实例
    """
    logger_instance = colorlog.getLogger(name)

    if logger_instance.handlers:
        return logger_instance

    # 设置日志级别
    logger_instance.setLevel(logging.DEBUG)

    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # 设置彩色日志格式
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )

    console_handler.setFormatter(formatter)
    logger_instance.addHandler(console_handler)

    return logger_instance

def setup_llm_client_logger() -> logging.Logger:
    """设置LLM_client专用logger（控制台+文件双输出）"""
    # 继承通用logger的控制台配置（名称设为"llm_client"避免冲突）
    logger_instance = setup_logger("llm_client")

    # 检查是否已添加文件处理器（避免重复添加）
    has_file_handler = any(
        isinstance(handler, RotatingFileHandler)
        for handler in logger_instance.handlers
    )
    if not has_file_handler:
        # 新增文件处理器（仅LLM_client使用）
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            filename=os.path.join(log_dir, "llm_chat.log"),
            maxBytes=1024 * 1024 * 5,
            backupCount=3,
            encoding="utf-8",
            delay=True
        )
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter("%(message)s")  # 仅消息内容
        file_handler.setFormatter(file_formatter)
        logger_instance.addHandler(file_handler)

    return logger_instance

# 全局通用logger（其他模块使用，无文件输出）
logger = setup_logger()
# LLM_client专用logger（带文件输出）
llm_client_logger = setup_llm_client_logger()