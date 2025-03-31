import os
import json
from typing import Dict, List, Any, Optional, AsyncGenerator, Tuple
from pathlib import Path

from services.review.review_article_service import review_article_service
from services.llm.utils.logger import logger
from services.llm.manager.llm_service_manager import llm_service_manager


class LongTextToSimpleArticle:
    """
    长文本转简单文章的处理类
    主要功能：将长文本（如播客文字稿）转换为结构化的文章
    """

    def __init__(self):
        # 提示词文件目录
        self.prompt_dir = 'src/prompt/long_text'
        # 输出文件保存目录
        self.output_dir = Path('public/output')
        logger.info('初始化 LongTextToSimpleArticle', extra={
            'prompt_dir': self.prompt_dir,
            'output_dir': str(self.output_dir),
            'current_working_dir': os.getcwd()
        })

    async def process_stream_response(self, stream: AsyncGenerator[str, None], phase: str) -> Tuple[
        List[str], AsyncGenerator[str, None]]:
        """
        处理流式响应的核心方法
        
        Args:
            stream: 输入的流式响应生成器
            phase: 当前处理阶段的名称

        Returns:
            返回一个元组，包含：
            - List[str]: 收集到的内容片段列表
            - AsyncGenerator[str, None]: 处理后的流式生成器，返回字符串类型数据
        """
        # 用于收集内容片段
        content_parts = []
        # 用于缓存当前正在处理的内容
        current_content = []

        def should_send_content(content: str, accumulated_content: List[str]) -> bool:
            """
            判断是否应该发送当前累积的内容
            """
            # 检查标点符号
            punctuation_marks = ['。', '！', '？', '；', '.', '!', '?', ';', '-']
            # 检查当前内容是否包含标点符号
            has_punctuation = any(mark in content for mark in punctuation_marks)
            # 检查当前内容是否包含换行符
            has_newline = '\n' in content
            # 检查累积内容的长度
            accumulated_length = len(''.join(accumulated_content))
            # 如果内容太长，也需要发送
            content_too_long = accumulated_length > 100

            return has_punctuation or has_newline or content_too_long

        async def process_stream() -> AsyncGenerator[str, None]:
            """
            内部函数：处理流数据
            - 解析每个数据块
            - 收集内容
            - 转发原始数据

            Returns:
                AsyncGenerator[str, None]: 生成字符串类型的数据流
            """
            async for chunk in stream:
                # 如果是字节类型，转换为字符串
                if isinstance(chunk, bytes):
                    chunk_str = chunk.decode('utf-8')
                else:
                    chunk_str = chunk

                # 检查数据块是否是SSE格式
                if chunk_str.startswith('data: '):
                    try:
                        # 解析JSON数据
                        data = json.loads(chunk_str.replace('data: ', ''))

                        # 处理不同类型的响应
                        if 'choices' in data and data['choices'] and 'delta' in data['choices'][0]:
                            delta = data['choices'][0]['delta']

                            # 处理推理内容
                            if 'reasoning_content' in delta and delta['reasoning_content']:
                                content = delta['reasoning_content']
                                content_parts.append(content)
                                current_content.append(content)

                                if should_send_content(content, current_content):
                                    response = {
                                        'phase': f"{phase}_reasoning",
                                        'content': ''.join(current_content)
                                    }
                                    yield f"data: {json.dumps(response, ensure_ascii=False)}\n\n"
                                    current_content.clear()

                            # 处理普通内容
                            if 'content' in delta and delta['content']:
                                content = delta['content']
                                content_parts.append(content)
                                current_content.append(content)

                                if should_send_content(content, current_content):
                                    response = {
                                        'phase': phase,
                                        'content': ''.join(current_content)
                                    }
                                    yield f"data: {json.dumps(response, ensure_ascii=False)}\n\n"
                                    current_content.clear()

                        # 处理普通的 content 字段（兼容旧格式）
                        elif 'content' in data and data['content']:
                            content = data['content']
                            content_parts.append(content)
                            current_content.append(content)

                            if should_send_content(content, current_content):
                                response = {
                                    'phase': phase,
                                    'content': ''.join(current_content)
                                }
                                yield f"data: {json.dumps(response, ensure_ascii=False)}\n\n"
                                current_content.clear()

                    except json.JSONDecodeError:
                        pass

            # 发送剩余的内容
            if current_content:
                response = {
                    'phase': phase,
                    'content': ''.join(current_content)
                }
                yield f"data: {json.dumps(response, ensure_ascii=False)}\n\n"

        # 返回收集的内容和处理后的流
        return content_parts, process_stream()

    def save_phase_result(self, content: str, task_id: str, phase: str) -> Path:
        """
        保存处理阶段的结果到文件
        
        Args:
            content: 要保存的内容
            task_id: 任务ID，用于文件命名
            phase: 处理阶段名称，用于文件命名

        Returns:
            Path: 保存文件的路径
        """
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # 构建输出文件路径：任务ID_阶段.md
        output_file = self.output_dir / f'{task_id}_{phase}.md'
        # 写入内容
        output_file.write_text(content, encoding='utf-8')
        logger.info('保存阶段结果', extra={
            'task_id': task_id,
            'phase': phase,
            'output_file': str(output_file),
            'output_dir': str(self.output_dir),
            'file_size': len(content)
        })
        return output_file

    async def process_prompt_with_gemini(self, prompt: str, task_id: str, phase: str) -> AsyncGenerator[str, None]:
        """
        使用 Gemini 处理提示词并生成内容
        
        Args:
            prompt: 提示词内容
            task_id: 任务ID
            phase: 处理阶段名称

        Returns:
            AsyncGenerator: 生成处理过程中的实时响应
        """
        logger.info('开始处理提示词', extra={
            'task_id': task_id,
            'phase': phase,
            'prompt_length': len(prompt)
        })

        # 准备对话消息
        messages = [
            {'role': 'user', 'content': prompt}
        ]

        # 获取AI客户端
        logger.info('调用 ThinkingGemini 对话方法', extra={
            'task_id': task_id,
            'phase': phase,
            'model': "Gemini/Gemini-2.0-Flash-thinking"
        })

        result = llm_service_manager.get_client("Gemini/Gemini-2.0-Flash-thinking")
        client, config = result

        # 用于收集内容片段
        content_parts = []

        # 进行流式对话
        async for role, content in client.stream_chat(
                messages=messages,
                model=config.model_id
        ):
            # 实时打印响应内容
            print(content, end="", flush=True)
            # 收集响应
            content_parts.append(content)
            # 构建响应数据
            response_data = {
                "role": role,
                "content": content
            }
            # 发送流式响应
            yield f"data: {json.dumps(response_data, ensure_ascii=False)}\n\n"

        # 合并所有内容
        full_content = ''.join(content_parts)

        # 保存处理结果
        output_file = self.save_phase_result(full_content, task_id, phase)

        logger.info('提示词处理完成', extra={
            'task_id': task_id,
            'phase': phase,
            'output_file': str(output_file),
            'content_length': len(full_content)
        })

        # 发送结束标记
        yield "data: [DONE]\n\n"

    async def convert_to_article(self, file_path: str, task_id: str) -> AsyncGenerator[str, None]:
        """
        将长文本转换为文章的主要方法
        整个过程分为多个阶段：基础文章生成、内容丰富、审查和优化
        
        Args:
            file_path: 输入文件路径
            task_id: 任务ID

        Returns:
            AsyncGenerator: 生成处理过程中的实时响应
        """
        # 记录开始处理的日志
        logger.info('开始从文件中提取和分析内容', extra={
            'file_path': file_path,
            'task_id': task_id,
            'current_working_dir': os.getcwd()
        })

        # 验证文件存在
        absolute_path = await self.check_file_exists(file_path)

        # 读取文件内容
        content_text = await self.read_file(absolute_path)

        # 读取 services/workflow/prompt/report.md 文件
        report_path = os.path.join("services/workflow/prompt/", 'report.md')  # 简报文件
        report_content = await self.read_file(report_path)
        # 替换 report_content 中的 {text} 为 content_text
        report_content_prompt = report_content.replace('{text}', content_text)

        # 读取 services/workflow/prompt/timeline.md 文件
        timeline_path = os.path.join("services/workflow/prompt/", 'timeline.md')  # 时间轴文件
        timeline_content = await self.read_file(timeline_path)
        # 替换 timeline_content 中的 {text} 为 content_text
        timeline_content_prompt = timeline_content.replace('{text}', content_text)

        logger.info('构建文件路径和提示词', extra={
            'file_path': file_path,
            'report_path': report_path,
            'timeline_path': timeline_path,
            'content_length': len(content_text),
            'report_prompt_length': len(report_content_prompt),
            'timeline_prompt_length': len(timeline_content_prompt)
        })

        # 1. 处理 report 提示词
        yield f"data: {json.dumps({'phase': 'report', 'content': '开始处理简报...'}, ensure_ascii=False)}\n\n"
        async for chunk in self.process_prompt_with_gemini(report_content_prompt, task_id, 'report'):
            yield chunk

        # 2. 处理 timeline 提示词
        yield f"data: {json.dumps({'phase': 'timeline', 'content': '开始处理时间轴...'}, ensure_ascii=False)}\n\n"
        async for chunk in self.process_prompt_with_gemini(timeline_content_prompt, task_id, 'timeline'):
            yield chunk

        # 3. 生成基础文章
        yield f"data: {json.dumps({'phase': 'start', 'content': '开始生成基础文章...'}, ensure_ascii=False)}\n\n"
        base_stream = self.base_article(file_path)
        content_parts, processed_stream = await self.process_stream_response(base_stream, 'start')
        async for chunk in processed_stream:
            yield chunk
        base_article_text = ''.join(content_parts)
        base_article_file = self.save_phase_result(base_article_text, task_id, 'base_article')

        timeline_file = "public/output/" + task_id + "_timeline.md"
        report_file = "public/output/" + task_id + "_report.md"
        # 4. 丰富文章内容
        yield f"data: {json.dumps({'phase': 'enrich', 'content': '开始丰富文章内容...'}, ensure_ascii=False)}\n\n"
        enrich_stream = self.enrich_article(base_article_text, timeline_file, report_file)
        content_parts, processed_stream = await self.process_stream_response(enrich_stream, 'enrich')
        async for chunk in processed_stream:
            yield chunk
        enriched_article = ''.join(content_parts)
        enriched_article_file = self.save_phase_result(enriched_article, task_id, 'enriched_article')

        # 5. 本地化处理
        yield f"data: {json.dumps({'phase': 'review_reasoning', 'content': '开始本地化处理...'}, ensure_ascii=False)}\n\n"
        review_stream = review_article_service.local_review(enriched_article)
        content_parts, processed_stream = await self.process_stream_response(review_stream, 'review')
        async for chunk in processed_stream:
            yield chunk
        local_review_results = ''.join(content_parts)
        review_file = self.save_phase_result(local_review_results, task_id, 'review')

        # 6. banfo风格处理
        yield f"data: {json.dumps({'phase': 'banfo_reasoning', 'content': '开始 banfo 处理...'}, ensure_ascii=False)}\n\n"
        banfo_stream = review_article_service.banfo_review(local_review_results)
        content_parts, processed_stream = await self.process_stream_response(banfo_stream, 'banfo')
        async for chunk in processed_stream:
            yield chunk
        free_banfo_results = ''.join(content_parts)
        banfo_file = self.save_phase_result(free_banfo_results, task_id, 'banfo')

        dump = json.dumps({'phase': 'complete', 'content': '文章生成完成', 'files': {
            'base': str(base_article_file),
            'enriched': str(enriched_article_file),
            'review': str(review_file),
            'banfo': str(banfo_file)
        }}, ensure_ascii=False)

        # 发送完成信号，包含所有生成文件的路径
        yield f"data: {dump}\n\n"
        yield "data: [DONE]\n\n"

    async def base_article(self, context_file_path: str) -> AsyncGenerator[str, None]:
        """
        生成基础文章的方法
        读取原始文本并使用AI生成初始文章
        
        Args:
            context_file_path: 原始文本文件路径

        Returns:
            AsyncGenerator: 生成的文章内容流
        """
        # 验证文件存在
        absolute_path = await self.check_file_exists(context_file_path)

        # 读取文件内容
        content_text = await self.read_file(absolute_path)

        # 构建AI提示词
        prompt = f"""请阅读分析这篇文稿, 根据文稿创作一篇爆款文章, 要求文笔细腻,情感真挚, 使用中文输出,
        文稿为播客的文字稿，创作文章时请着重于文稿的话题观点和内容，切记不要把广告，播客主持人，嘉宾等人物写入文章中。
        文稿内容为：
        {content_text}"""

        # 准备对话消息
        messages = [
            {'role': 'user', 'content': prompt}
        ]

        # 获取AI客户端
        logger.info('调用 ThinkingGemini 对话方法')
        result = llm_service_manager.get_client("Gemini/Gemini-2.0-Flash-thinking")
        client, config = result

        # 进行流式对话
        full_response = []  # 用于收集完整响应
        async for role, content in client.stream_chat(
                messages=messages,
                model=config.model_id
        ):
            # 实时打印响应内容
            print(content, end="", flush=True)
            # 收集响应
            full_response.append(content)
            # 构建响应数据
            response_data = {
                "role": role,
                "content": content
            }
            # 发送流式响应
            yield f"data: {json.dumps(response_data, ensure_ascii=False)}\n\n"

        # 打印分隔线
        print("\n" + "-" * 50)
        # 发送结束标记
        yield "data: [DONE]\n\n"

    async def enrich_article(self, base_article: str, timeline_file_path: str, report_file_path: str) -> AsyncGenerator[
        str, None]:
        """
        结合时间轴和简报丰富文章内容
        """
        # 检查并读取时间轴文件
        timeline_absolute_path = await self.check_file_exists(timeline_file_path)
        timeline_content = await self.read_file(timeline_absolute_path)

        # 检查并读取简报文件
        report_absolute_path = await self.check_file_exists(report_file_path)
        report_content = await self.read_file(report_absolute_path)

        prompt = f"""请结合这篇文稿的时间轴和简报, 丰富这篇文章, 要求文笔细腻,情感真挚, 使用中文输出
         文稿内容为：
         {base_article}

         时间轴：

         {timeline_content}

         简报：

         {report_content}"""

        messages = [
            {'role': 'user', 'content': prompt}
        ]

        logger.info('调用 ThinkingGemini 对话方法')
        result = llm_service_manager.get_client("Gemini/Gemini-2.0-Flash-thinking")

        client, config = result

        full_response = []  # 用于收集完整响应
        async for role, content in client.stream_chat(
                messages=messages,
                model=config.model_id
        ):
            # 打印每个片段的内容（不换行）
            print(content, end="", flush=True)

            full_response.append(content)
            response_data = {
                "role": role,
                "content": content
            }
            yield f"data: {json.dumps(response_data, ensure_ascii=False)}\n\n"

        # 打印完整响应的分隔线
        print("\n" + "-" * 50)

        yield "data: [DONE]\n\n"

    def parse_json_response(self, content: str) -> Any:
        """
        解析 JSON 响应
        """
        # 尝试从响应中提取 JSON
        import re
        json_regex = r'```(?:json)?([\s\S]*?)```'
        json_match = re.search(json_regex, content)

        if json_match and json_match.group(1):
            # 从代码块中提取 JSON
            return json.loads(json_match.group(1).strip())
        else:
            # 尝试直接解析整个响应
            return json.loads(content)

    # async def fix_json_with_backup_model(self, content: str) -> Any:
    #     """
    #     使用备用模型修复 JSON
    #     """
    #     prompt = f"""当前内容在程序中检测不符合 json 格式, 请你帮忙处理为正确的 json 格式并返回，
    #     只返回调整好的 json 文本即可，不要加入其他的说明和标识.
    #     当前内容为：
    #     {content}"""
    #
    #     messages = [
    #         {'role': 'user', 'content': prompt}
    #     ]
    #
    #     response = await openai_client.chat(
    #         messages=messages,
    #         model='deepseek-chat',
    #         temperature=1.0
    #     )
    #
    #     return json.loads(response['choices'][0]['message']['content'])

    async def check_file_exists(self, file_path: str) -> str:
        """
        检查文件是否存在
        
        Args:
            file_path: 要检查的文件路径

        Returns:
            str: 文件的绝对路径

        Raises:
            FileNotFoundError: 当文件不存在时抛出
        """
        # 转换为绝对路径
        absolute_path = file_path if os.path.isabs(file_path) else os.path.join(os.getcwd(), file_path)

        logger.info('检查文件是否存在', extra={
            'file_path': file_path,
            'absolute_path': absolute_path,
            'current_working_dir': os.getcwd(),
            'is_absolute': os.path.isabs(file_path),
            'file_exists': os.path.exists(absolute_path)
        })

        # 检查文件是否存在
        if not os.path.exists(absolute_path):
            logger.error('文件不存在', extra={
                'file_path': file_path,
                'absolute_path': absolute_path,
                'current_working_dir': os.getcwd()
            })
            raise FileNotFoundError(f'文件不存在: {file_path}')

        return absolute_path

    async def read_file(self, absolute_path: str) -> str:
        """
        读取文件内容
        
        Args:
            absolute_path: 文件的绝对路径

        Returns:
            str: 文件内容

        Raises:
            ValueError: 当文件为空时抛出
            Exception: 其他读取错误
        """
        logger.info('开始读取文件', extra={
            'absolute_path': absolute_path,
            'current_working_dir': os.getcwd(),
            'file_exists': os.path.exists(absolute_path),
            'file_size': os.path.getsize(absolute_path) if os.path.exists(absolute_path) else 0
        })

        try:
            # 读取文件
            with open(absolute_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查内容是否为空
            if not content or not content.strip():
                logger.warning('文件内容为空', extra={
                    'absolute_path': absolute_path,
                    'content_length': len(content)
                })
                raise ValueError(f'文件内容为空: {absolute_path}')

            logger.info('文件读取成功', extra={
                'absolute_path': absolute_path,
                'content_length': len(content)
            })
            return content
        except Exception as e:
            # 记录错误并重新抛出
            logger.error('读取文件失败', extra={
                'absolute_path': absolute_path,
                'error': str(e),
                'error_type': type(e).__name__
            })
            raise

    async def execute_workflow(self, file_path: str, task_id: str) -> AsyncGenerator[str, None]:
        """
        执行完整的工作流程
        
        Args:
            file_path: 输入文件路径
            task_id: 任务ID，用于文件命名

        Returns:
            AsyncGenerator: 生成处理过程中的实时响应
        """
        logger.info('开始执行工作流', extra={
            'file_path': file_path,
            'task_id': task_id,
            'current_working_dir': os.getcwd(),
            'output_dir': str(self.output_dir)
        })
        async for chunk in self.convert_to_article(file_path, task_id):
            yield chunk
