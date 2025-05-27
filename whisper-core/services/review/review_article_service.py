import os
import json
from pathlib import Path
from typing import List, Dict, Any, AsyncGenerator, Union

from services.llm.composite.composite import CompatibleComposite
from services.llm.utils.logger import logger

class ReviewArticleService:
    def __init__(self):
        self.prompt_dir = 'services/workflow/prompt'
        self.local_prompt_file = 'local_review.md'
        self.deepbanfoty_prompt_file = 'deepbanfo_review.md'

    async def local_review(self, paragraph: str) -> AsyncGenerator[bytes, None]:
        """
        本地化审查
        Args:
            paragraph: 待审查的文本段落
        Returns:
            AsyncGenerator: 生成审查结果的流
        """
        # 加载审查提示词
        prompt_path = Path(os.getcwd()) / self.prompt_dir / self.local_prompt_file
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                review_prompt = f.read()
        except Exception as e:
            logger.error(f'读取本地审查提示词失败: {e}')
            raise

        # 审查段落
        async for chunk in self.base_review(
            paragraph, 
            review_prompt, 
            "Volcengine/DeepSeek-R1", 
            "Bailian/qwen-max"
        ):
            yield chunk

    async def banfo_review(self, paragraph: str) -> AsyncGenerator[bytes, None]:
        """
        特殊文风改编 - banfo风格
        Args:
            paragraph: 待改编的文本段落
        Returns:
            AsyncGenerator: 生成改编结果的流
        """
        # 加载审查提示词
        prompt_path = Path(os.getcwd()) / self.prompt_dir / self.deepbanfoty_prompt_file
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                review_prompt = f.read()
        except Exception as e:
            logger.error(f'读取banfo审查提示词失败: {e}')
            raise

        # 审查段落
        async for chunk in self.base_review(
            paragraph, 
            review_prompt, 
            "Volcengine/DeepSeek-R1", 
            "Volcengine/doubao-pro-1.5"
        ):
            yield chunk

    async def base_review(
        self, 
        paragraph: str, 
        review_prompt: str, 
        deepseek_model: str, 
        target_model: str
    ) -> AsyncGenerator[bytes, None]:
        """
        基础审查方法
        Args:
            paragraph: 待审查的文本段落
            review_prompt: 审查提示词
            deepseek_model: DeepSeek模型名称
            target_model: 目标模型名称
        Returns:
            AsyncGenerator: 生成审查结果的流
        """
        messages = [
            {
                'role': 'user',
                'content': f"{review_prompt}\n\n## 待审查文章：\n{paragraph}"
            }
        ]

        logger.info('调用基础审查方法', extra={
            'deepseek_model': deepseek_model,
            'target_model': target_model
        })

        composite = CompatibleComposite()
        async for chunk in composite.chat_completions_with_stream(
            messages=messages,
            deepseek_model=deepseek_model,
            target_model=target_model
        ):
            yield chunk

    async def process_stream_response(
        self, 
        stream_generator: AsyncGenerator[bytes, None]
    ) -> str:
        """
        处理流式响应，将其转换为字符串
        Args:
            stream_generator: 流式响应生成器
        Returns:
            str: 合并后的完整响应内容
        """
        full_response = []
        async for chunk in stream_generator:
            try:
                # 解析 SSE 数据
                if chunk.startswith(b'data: '):
                    data = chunk[6:].decode('utf-8').strip()
                    if data == '[DONE]':
                        break
                    
                    # 解析 JSON 数据
                    response_data = json.loads(data)
                    if 'choices' in response_data and response_data['choices']:
                        content = response_data['choices'][0].get('delta', {}).get('content', '')
                        if content:
                            print(content, end='', flush=True)
                            full_response.append(content)
            except Exception as e:
                logger.error(f'处理响应数据失败: {e}')
                continue

        return ''.join(full_response)

# 创建服务实例
review_article_service = ReviewArticleService()

