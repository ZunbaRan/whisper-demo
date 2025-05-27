"""模型配置管理工具"""

import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

from ..utils.logger import logger


@dataclass
class ModelConfig:
    """模型配置数据类"""
    model_id: str
    api_key: str
    api_base_url: str
    api_request_address: str
    is_valid: bool
    proxy_open: bool
    model_format: str = ""  # target_models 专用
    is_origin_reasoning: bool = False  # reasoner_models 专用


class ModelManager:
    """模型配置管理器"""

    def __init__(self):
        """初始化配置管理器"""
        self.config_path = os.path.join(os.path.dirname(__file__), "model_config.json")
        self.config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> None:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            logger.info("成功加载模型配置文件")
        except Exception as e:
            logger.error(f"加载模型配置文件失败: {e}")
            raise

    # 返回client 和
    def get_reasoner_config(self, model_name: str) -> Optional[ModelConfig]:
        """获取推理模型配置

        Args:
            model_name: 模型名称，例如 "DeepSeek/DeepSeek-Reasoner"

        Returns:
            ModelConfig: 模型配置对象，如果模型不存在或无效则返回 None
        """
        try:
            if model_name not in self.config["reasoner_models"]:
                logger.warning(f"推理模型 {model_name} 不存在")
                return None

            config = self.config["reasoner_models"][model_name]
            if not config["is_valid"]:
                logger.warning(f"推理模型 {model_name} 未启用")
                return None

            return ModelConfig(
                model_id=config["model_id"],
                api_key=config["api_key"],
                api_base_url=config["api_base_url"],
                api_request_address=config["api_request_address"],
                is_valid=config["is_valid"],
                proxy_open=config["proxy_open"],
                is_origin_reasoning=config["is_origin_reasoning"]
            )
        except KeyError as e:
            logger.error(f"获取推理模型 {model_name} 配置失败: {e}")
            return None

    def get_target_config(self, model_name: str) -> Optional[ModelConfig]:
        """获取目标模型配置

        Args:
            model_name: 模型名称，例如 "Gemini/Gemini-2.0-Flash"

        Returns:
            ModelConfig: 模型配置对象，如果模型不存在或无效则返回 None
        """
        try:
            if model_name not in self.config["target_models"]:
                logger.warning(f"目标模型 {model_name} 不存在")
                return None

            config = self.config["target_models"][model_name]
            if not config["is_valid"]:
                logger.warning(f"目标模型 {model_name} 未启用")
                return None

            return ModelConfig(
                model_id=config["model_id"],
                api_key=config["api_key"],
                api_base_url=config["api_base_url"],
                api_request_address=config["api_request_address"],
                is_valid=config["is_valid"],
                proxy_open=config["proxy_open"],
                model_format=config["model_format"]
            )
        except KeyError as e:
            logger.error(f"获取目标模型 {model_name} 配置失败: {e}")
            return None

    def get_composite_config(self, composite_name: str) -> Optional[tuple[str, str]]:
        """获取组合模型配置

        Args:
            composite_name: 组合名称，例如 "deepgeminiflash"

        Returns:
            tuple[str, str]: (reasoner_model_name, target_model_name)，如果不存在或无效则返回 None
        """
        try:
            if composite_name not in self.config["composite_models"]:
                logger.warning(f"组合模型 {composite_name} 不存在")
                return None

            config = self.config["composite_models"][composite_name]
            if not config["is_valid"]:
                logger.warning(f"组合模型 {composite_name} 未启用")
                return None

            return (config["reasoner_models"], config["target_models"])
        except KeyError as e:
            logger.error(f"获取组合模型 {composite_name} 配置失败: {e}")
            return None

    def get_proxy_config(self) -> tuple[bool, str]:
        """获取代理配置

        Returns:
            tuple[bool, str]: (是否启用代理, 代理地址)
        """
        proxy_config = self.config.get("proxy", {})
        logger.info(f"获取代理配置: {proxy_config}")
        return (
            proxy_config.get("proxy_open", False),
            proxy_config.get("proxy_address", "")
        )

    def get_system_config(self) -> Dict[str, Any]:
        """获取系统配置

        Returns:
            Dict[str, Any]: 系统配置字典
        """
        return self.config.get("system", {})


# 创建单例实例
model_manager = ModelManager() 