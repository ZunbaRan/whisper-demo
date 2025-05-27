"""LLM服务主入口"""

from typing import List, Dict, AsyncGenerator, Optional, Any

from services.llm.utils.logger import logger
from services.llm.manager.llm_service_manager import llm_service_manager
from services.llm.utils.logger import llm_client_logger  # 新增：导入专用logger

class LLM_client:
    """LLM服务主类"""

    async def chat_stream(
            self,
            model_name: str,
            messages: List[Dict[str, str]],
            config: Optional[Any] = None
    ) -> AsyncGenerator[tuple[str, str], None]:
        """执行流式对话

        Args:
            model_name: 模型名称
            messages: 对话消息列表
            config: 对话配置

        Yields:
            tuple[str, str]: (role, content) 消息元组，当content为[DONE]时表示对话结束
        """
        client, model_config = llm_service_manager.get_client(model_name)
        if not client:
            error_msg = f"无法创建模型 {model_name} 的客户端"
            logger.error(error_msg)
            yield "error", error_msg
            yield "done", "[DONE]"
            return

        # try:
        # 打印config
        logger.info(f"模型配置: {model_config}")
        logger.info(f"开始与 {model_name} 进行对话")

        buffer = ""  # 新增：内容缓冲区
        async for role, content in client.stream_chat(
                messages=messages,
                model=model_config.model_id,
                config=config
        ):
            # context 凑够 20 个字符的时候再打印
            # context 凑够 20 个字符的时候再打印
            buffer += content
            if len(buffer) >= 20:
                llm_client_logger.info(buffer)
                buffer = ""  # 清空缓冲区

            yield role, content

        # 处理剩余缓冲区
        if buffer:
            llm_client_logger.info(buffer)

        # 发送完成标记
        # yield "done", "[DONE]"

        # except Exception as e:
        #     error_msg = f"对话过程中发生错误: {str(e)}"
        #     logger.error(error_msg)
        #     yield "error", error_msg
        #     yield "done", "[DONE]"


llm_client = LLM_client()
