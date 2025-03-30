"""OpenAI 兼容的组合模型服务，用于协调 DeepSeek 和其他 OpenAI 兼容模型的调用"""

import asyncio
import json
import time
from typing import AsyncGenerator, Dict, Any, List

from ..utils.logger import logger
from ..manager.llm_service_manager import llm_service_manager

class CompatibleComposite:
    """处理 DeepSeek 和其他 OpenAI 兼容模型的流式输出衔接"""

    def __init__(
        self
    ):
        """初始化 composite 客户端
        """


    async def chat_completions_with_stream(
        self,
        messages: List[Dict[str, str]],
        deepseek_model: str = "deepseek-reasoner",
        target_model: str = "",
    ) -> AsyncGenerator[bytes, None]:
        """处理完整的流式输出过程

        Args:
            messages: 初始消息列表
            model_arg: 模型参数 (temperature, top_p, presence_penalty, frequency_penalty)
            deepseek_model: DeepSeek 模型名称
            target_model: 目标 OpenAI 兼容模型名称

        Yields:
            字节流数据，格式如下：
            {
                "id": "chatcmpl-xxx",
                "object": "chat.completion.chunk",
                "created": timestamp,
                "model": model_name,
                "choices": [{
                    "index": 0,
                    "delta": {
                        "role": "assistant",
                        "reasoning_content": reasoning_content,
                        "content": content
                    }
                }]
            }
        """
        # 生成唯一的会话ID和时间戳
        chat_id = f"chatcmpl-{hex(int(time.time() * 1000))[2:]}"
        created_time = int(time.time())

        # 创建队列，用于收集输出数据
        output_queue = asyncio.Queue()
        # 队列，用于传递 DeepSeek 推理内容
        reasoning_queue = asyncio.Queue()

        # 用于存储 DeepSeek 的推理累积内容
        reasoning_content = []

        async def process_deepseek():
            logger.info(f"开始处理 DeepSeek 流，使用模型：{deepseek_model}")
            print(f"\n开始 DeepSeek 推理阶段:")
            print("-" * 50)
            try:
                client, config = llm_service_manager.get_client(deepseek_model)
                print(f"请求地址: {config.api_base_url + config.api_request_address}")
                print(f"模型ID: {config.model_id}")
                if client.proxy:
                    print(f"使用代理: {client.proxy}")
                
                async for content_type, content in client.stream_chat(
                    messages, config.model_id
                ):
                    if content_type == "reasoning":
                        reasoning_content.append(content)
                        # 只打印推理内容，不打印 JSON 响应
                        print(content, end="", flush=True)
                        
                        response = {
                            "id": chat_id,
                            "object": "chat.completion.chunk",
                            "created": created_time,
                            "model": deepseek_model,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {
                                        "role": "assistant",
                                        "reasoning_content": content,
                                        "content": "",
                                    },
                                }
                            ],
                        }
                        await output_queue.put(
                            f"data: {json.dumps(response)}\n\n".encode("utf-8")
                        )
                    elif content_type == "content":
                        # 当收到 content 类型时，将完整的推理内容发送到 reasoning_queue
                        logger.info(
                            f"DeepSeek 推理完成，收集到的推理内容长度：{len(''.join(reasoning_content))}"
                            f"推理内容：{''.join(reasoning_content)}"
                        )
                        print("\n" + "-" * 50)
                        await reasoning_queue.put("".join(reasoning_content))
                        break
            except Exception as e:
                logger.error(f"处理 DeepSeek 流时发生错误: {e}")
                print(f"\nDeepSeek 推理阶段发生错误: {str(e)}")
                print("-" * 50)
                await reasoning_queue.put("")
            # 标记 DeepSeek 任务结束
            logger.info("DeepSeek 任务处理完成，标记结束")
            await output_queue.put(None)

        async def process_target():
            try:
                logger.info("等待获取 DeepSeek 的推理内容...")
                reasoning = await reasoning_queue.get()
                logger.debug(
                    f"获取到推理内容，内容长度：{len(reasoning) if reasoning else 0}"
                )
                if not reasoning:
                    logger.warning("未能获取到有效的推理内容，将使用默认提示继续")
                    reasoning = "获取推理内容失败"

                # 构造 OpenAI 的输入消息
                openai_messages = messages.copy()
                combined_content = f"""
                Here's my another model's reasoning process:\n{reasoning}\n\n
                Based on this reasoning, provide your response directly to me:"""

                # 检查过滤后的消息列表是否为空
                if not openai_messages:
                    raise ValueError("消息列表为空，无法处理请求")

                # 获取最后一个消息并检查其角色
                last_message = openai_messages[-1]
                if last_message.get("role", "") != "user":
                    raise ValueError("最后一个消息的角色不是用户，无法处理请求")

                # 修改最后一个消息的内容
                original_content = last_message["content"]
                fixed_content = f"Here's my original input:\n{original_content}\n\n{combined_content}"
                last_message["content"] = fixed_content

                logger.info(f"开始处理 OpenAI 兼容流，使用模型: {target_model}")
                print(f"\n开始目标模型响应阶段:")
                print("-" * 50)

                client, config = llm_service_manager.get_client(target_model)
                print(f"请求地址: {config.api_base_url + config.api_request_address}")
                print(f"模型ID: {config.model_id}")
                if client.proxy:
                    print(f"使用代理: {client.proxy}")
                
                async for role, content in client.stream_chat(
                    messages=openai_messages,
                    model=config.model_id,
                ):
                    # 只打印响应内容，不打印 JSON 响应
                    print(content, end="", flush=True)
                    
                    response = {
                        "id": chat_id,
                        "object": "chat.completion.chunk",
                        "created": created_time,
                        "model": target_model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"role": role, "content": content},
                            }
                        ],
                    }
                    await output_queue.put(
                        f"data: {json.dumps(response)}\n\n".encode("utf-8")
                    )
                print("\n" + "-" * 50)
            except Exception as e:
                logger.error(f"处理 OpenAI 兼容流时发生错误: {e}")
                print(f"\n目标模型响应阶段发生错误: {str(e)}")
                print("-" * 50)
            # 标记 OpenAI 任务结束
            logger.info("OpenAI 兼容任务处理完成，标记结束")
            await output_queue.put(None)

        # 创建并发任务
        asyncio.create_task(process_deepseek())
        asyncio.create_task(process_target())

        # 等待两个任务完成
        finished_tasks = 0
        while finished_tasks < 2:
            item = await output_queue.get()
            if item is None:
                finished_tasks += 1
                continue
            yield item

        # 发送结束标记
        yield b"data: [DONE]\n\n"

