import json
from typing import AsyncGenerator, Tuple, Dict, Any, List

from google.genai.types import GenerateContentConfig
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel

from services.llm.article_agent.angle_hook_strategist import logger
from services.llm.agent.base_agent import BaseAgent

class OneStyle(BaseModel):
    tone_and_voice: List[str]
    sentence_structure: str
    average_sentence_length: int
    vocabulary: List[str]
    rhetorical_devices: List[str]
    paragraphing_and_flow: str
    opening_closing_patterns: List[str]
    few_shot: List[str]


class SingleArticleAnalyzer(BaseAgent):
    """单篇文章分析Agent"""

    PROMPT_TEMPLATE = """角色: 你是一位文学分析师，专注于识别独特的写作风格。
背景: 分析以下由 {author_name} 撰写的文章： "{content}"
任务: 识别并描述这篇具体文章的风格特征，重点关注：
1. 语气与语态 (Tone & Voice): (例如, 正式, 非正式, 讽刺, 权威, 共情, 客观) - 提供关键词。
2. 句式结构 (Sentence Structure): (例如, 长短句结合, 主要是复杂句, 简洁直接) - 描述模式。平均句长估计？
3. 词汇选择 (Vocabulary): (例如, 技术术语, 口语化表达, 富有感染力的形容词, 简洁易懂) - 列出值得注意的词语选择或类别。
4. 修辞手法 (Rhetorical Devices): (例如, 隐喻, 类比, 反问, 重复, 讲故事) - 列出观察到的手法。
5. 段落与流畅性 (Paragraphing & Flow): (例如, 短小精悍的段落; 详细的长段落; 过渡词的使用) - 描述结构。
6. 开头与结尾模式 (Opening & Closing Patterns): 作者通常如何开始和结束文章？ (例如, 轶事, 大胆陈述, 提问, 总结)
7. 少量极具代表性的样本(few shot)

输出格式: 请以JSON格式返回结果，包含以下字段：
- tone_and_voice: 语气与语态（字符串数组）
- sentence_structure: 句式结构（字符串）
- average_sentence_length: 平均句长（整数）
- vocabulary: 词汇选择（字符串数组）
- rhetorical_devices: 修辞手法（字符串数组）
- paragraphing_and_flow: 段落与流畅性（字符串）
- opening_closing_patterns: 开头与结尾模式（字符串数组）
- few_shot: 少量具有代表性的样本（字符串数组）
"""

    async def pre_process(self) -> None:
        config = GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=OneStyle
        )
        self.context["config"] = config

    async def build_messages(self) -> List[Dict[str, str]]:
        prompt = await self.build_prompt(
            self.PROMPT_TEMPLATE,
            author_name=self.context["author_name"],
            content=self.context["content"]
        )
        return [{'role': 'user', 'content': prompt}]

    async def process_response(self, response: AsyncGenerator[Tuple[str, str], None]) -> AsyncGenerator[
        Tuple[str, str], None]:
        async for role, content in response:
            yield role, content
        filename = self.context.get("filename", "unknown")
        yield 'assistant', f'完成文章分析: {filename}'

    async def parse_response(self, response: str) -> Dict:
        parser = JsonOutputParser()
        return parser.parse(response)