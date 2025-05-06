"""LLM 服务管理器"""

from typing import Dict, Optional, Tuple

from services.llm.clients.ark_client import ArkClient
from ..clients.base_client import BaseClient
from ..clients.openai_client import OpenAIClient
from ..clients.openai_compatible_client import OpenAICompatibleClient
from ..clients.gemini_client import GeminiClient
from ..clients.zhipu_client import ZhipuClient
from ..utils.logger import logger
from .model_manager import model_manager, ModelConfig


class LLMServiceManager:
    """LLM 服务管理器，用于管理多个 LLM 实例"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMServiceManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.clients: Dict[str, Tuple[BaseClient, ModelConfig]] = {}
            self._initialized = True

    def initialize_clients(self) -> None:
        """初始化所有配置的客户端"""
        try:
            # 获取所有目标模型配置
            target_models = model_manager.config.get("target_models", {})
            for model_name in target_models:
                if target_models[model_name].get("is_valid", False):
                    self._get_client(model_name)

            # 获取所有推理模型配置
            reasoner_models = model_manager.config.get("reasoner_models", {})
            for model_name in reasoner_models:
                if reasoner_models[model_name].get("is_valid", False):
                    self._get_client(model_name)

            logger.info(f"已初始化 {len(self.clients)} 个 LLM 客户端")
        except Exception as e:
            logger.error(f"初始化 LLM 客户端失败: {e}")

    def _get_client(self, model_name: str) -> Optional[Tuple[BaseClient, ModelConfig]]:
        """获取对应的客户端实例

        Args:
            model_name: 模型名称

        Returns:
            Optional[Tuple[BaseClient, ModelConfig]]: (客户端实例, 配置) 元组，如果模型不存在则返回 None
        """
        try:
            reasoner = False
            # 获取模型配置
            config = model_manager.get_target_config(model_name)
            if not config:
                config = model_manager.get_reasoner_config(model_name)
                reasoner = True
                if not config:
                    logger.error(f"无法获取模型 {model_name} 的配置")
                    return None

            # 获取代理配置
            proxy_open, proxy_address = model_manager.get_proxy_config()
            proxy = proxy_address if proxy_open else None

            # 根据模型类型创建对应的客户端
            if model_name.startswith("Gemini/"):
                client = GeminiClient(
                    api_key=config.api_key,
                    api_url=config.api_base_url,
                    api_request_address=config.api_request_address,
                    proxy=proxy,
                    reasoner=reasoner
                )
            elif model_name.startswith("Kimi/"):
                # Kimi 客户端需要额外的配置
                client = OpenAIClient(
                    api_key=config.api_key,
                    api_url=config.api_base_url,
                    api_request_address=config.api_request_address,
                    proxy=proxy,
                    reasoner=reasoner
                )
            elif model_name.startswith("GLM/"):
                client = ZhipuClient(
                    api_key=config.api_key,
                    api_url=config.api_base_url,
                    api_request_address=config.api_request_address,
                    proxy=proxy,
                    reasoner=reasoner
                )
            elif model_name.startswith("Volcengine/"):
                client = ArkClient(
                    api_key=config.api_key,
                    api_url=config.api_base_url,
                    api_request_address=config.api_request_address,
                    proxy=proxy,
                    reasoner=reasoner
                )
            else:
                # 默认使用 OpenAI 兼容客户端
                client = OpenAICompatibleClient(
                    api_key=config.api_key,
                    api_url=config.api_base_url,
                    api_request_address=config.api_request_address,
                    proxy=proxy,
                    reasoner=reasoner
                )

            return client, config

        except Exception as e:
            logger.error(f"创建客户端失败: {e}")
            return None

    def get_client(self, model_name: str) -> Optional[Tuple[BaseClient, ModelConfig]]:
        """获取或创建客户端实例

        Args:
            model_name: 模型名称

        Returns:
            Optional[Tuple[BaseClient, ModelConfig]]: (客户端实例, 配置) 元组，如果模型不存在则返回 None
        """
        if model_name not in self.clients:
            result = self._get_client(model_name)
            if result:
                self.clients[model_name] = result
            else:
                return None
        return self.clients[model_name]

    def get_all_clients(self) -> Dict[str, Tuple[BaseClient, ModelConfig]]:
        """获取所有已初始化的客户端

        Returns:
            Dict[str, Tuple[BaseClient, ModelConfig]]: 客户端字典
        """
        return self.clients


# 创建单例实例
llm_service_manager = LLMServiceManager() 