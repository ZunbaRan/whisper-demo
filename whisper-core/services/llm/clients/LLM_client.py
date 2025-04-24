"""LLM服务主入口"""

from typing import List, Dict, AsyncGenerator

from services.llm.utils.logger import logger
from services.llm.manager.llm_service_manager import llm_service_manager


class LLM_client:
    """LLM服务主类"""

    async def chat_stream(
            self,
            model_name: str,
            messages: List[Dict[str, str]]
    ) -> AsyncGenerator[tuple[str, str], None]:
        """执行流式对话

        Args:
            model_name: 模型名称
            messages: 对话消息列表

        Yields:
            tuple[str, str]: (role, content) 消息元组，当content为[DONE]时表示对话结束
        """
        client, config = llm_service_manager.get_client(model_name)
        if not client:
            error_msg = f"无法创建模型 {model_name} 的客户端"
            logger.error(error_msg)
            yield "error", error_msg
            yield "done", "[DONE]"
            return

        # try:
        # 打印config
        logger.info(f"模型配置: {config}")
        logger.info(f"开始与 {model_name} 进行对话")
        async for role, content in client.stream_chat(
                messages=messages,
                model=config.model_id
        ):
            print(content, end='', flush=True)
            yield role, content

        # 发送完成标记
        yield "done", "[DONE]"

        # except Exception as e:
        #     error_msg = f"对话过程中发生错误: {str(e)}"
        #     logger.error(error_msg)
        #     yield "error", error_msg
        #     yield "done", "[DONE]"


llm_client = LLM_client()
