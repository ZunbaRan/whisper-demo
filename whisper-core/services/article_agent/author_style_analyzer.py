import os
import json
from typing import Dict, List, Any, AsyncGenerator
import logging
from services.llm.manager.llm_service_manager import llm_service_manager
from .output_manager import OutputManager

logger = logging.getLogger(__name__)

class AuthorStyleAnalyzer:
    def __init__(self, author_name: str):
        self.author_name = author_name
        self.llm_client = None
        self.llm_config = None
        self.output_manager = OutputManager()

    async def check_dir_exists(self, dir_path: str) -> str:
        """检查目录是否存在并返回绝对路径"""
        if not os.path.exists(dir_path):
            raise FileNotFoundError(f"目录不存在: {dir_path}")
        if not os.path.isdir(dir_path):
            raise NotADirectoryError(f"路径不是目录: {dir_path}")
        return os.path.abspath(dir_path)

    async def read_markdown_files(self, dir_path: str) -> List[Dict[str, str]]:
        """读取目录中的所有markdown文件"""
        articles = []
        for filename in os.listdir(dir_path):
            if filename.endswith('.md'):
                file_path = os.path.join(dir_path, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    articles.append({
                        "filename": filename,
                        "content": content
                    })
        return articles

    async def analyze_single_article(self, article: Dict[str, str]) -> Dict[str, Any]:
        """分析单篇文章的风格"""
        article_prompt = f"""角色: 你是一位文学分析师，专注于识别独特的写作风格。
背景: 分析以下由 {self.author_name} 撰写的文章： "{article['content']}"
任务: 识别并描述这篇具体文章的风格特征，重点关注：
1. 语气与语态 (Tone & Voice): (例如, 正式, 非正式, 讽刺, 权威, 共情, 客观) - 提供关键词。
2. 句式结构 (Sentence Structure): (例如, 长短句结合, 主要是复杂句, 简洁直接) - 描述模式。平均句长估计？
3. 词汇选择 (Vocabulary): (例如, 技术术语, 口语化表达, 富有感染力的形容词, 简洁易懂) - 列出值得注意的词语选择或类别。
4. 修辞手法 (Rhetorical Devices): (例如, 隐喻, 类比, 反问, 重复, 讲故事) - 列出观察到的手法。
5. 段落与流畅性 (Paragraphing & Flow): (例如, 短小精悍的段落; 详细的长段落; 过渡词的使用) - 描述结构。
6. 开头与结尾模式 (Opening & Closing Patterns): 作者通常如何开始和结束文章？ (例如, 轶事, 大胆陈述, 提问, 总结)
7. 文章标签(tag): 这篇文章大概属于什么类型的文章？ (例如：技术, 商业, 情感, 历史, 教育)

输出格式: 请以JSON格式返回结果，包含以下字段：
- tone_and_voice: 语气与语态（字符串数组）
- sentence_structure: 句式结构（字符串）
- average_sentence_length: 平均句长（整数）
- vocabulary: 词汇选择（字符串数组）
- rhetorical_devices: 修辞手法（字符串数组）
- paragraphing_and_flow: 段落与流畅性（字符串）
- opening_closing_patterns: 开头与结尾模式（字符串数组）
- tag: 文章标签（字符串）"""

        messages = [{'role': 'user', 'content': article_prompt}]
        article_response = []
        async for role, content in self.llm_client.stream_chat(
            messages=messages,
            model=self.llm_config.model_id
        ):
            article_response.append(content)

        # TODO: 解析article_response，提取风格分析结果
        result = {
            "tone_and_voice": [],
            "sentence_structure": "",
            "average_sentence_length": 0,
            "vocabulary": [],
            "rhetorical_devices": [],
            "paragraphing_and_flow": "",
            "opening_closing_patterns": [],
            "tag": ""
        }
        
        # 保存单篇文章的分析结果
        self.output_manager.save_step_output(f"article_analysis_{article['filename']}", result)
        return result

    async def aggregate_by_tag(self, all_analyses: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """根据tag聚合分析结果"""
        tag_groups = {}
        for analysis in all_analyses:
            tag = analysis.get("tag", "unknown")
            if tag not in tag_groups:
                tag_groups[tag] = []
            tag_groups[tag].append(analysis)
        return tag_groups

    async def generate_style_guide(self, tag: str, analyses: List[Dict[str, Any]]) -> str:
        """为特定tag的文章生成风格指南"""
        # 计算统计信息
        stats = {
            "common_tones": [],
            "avg_sentence_length": 0,
            "common_devices": [],
            "vocabulary_patterns": [],
            "structure_habits": []
        }
        # TODO: 计算统计数据

        # 准备综合分析的prompt
        guide_prompt = f"""角色: 你是一位大师级写作指导，将风格分析综合成一份实用的指南。
背景: 基于对 {self.author_name} 的 {len(analyses)} 篇{tag}类文章的分析，观察到以下模式：
{json.dumps(stats, ensure_ascii=False, indent=2)}

任务: 创建一份全面的"风格指南"，用于模仿 {self.author_name} 的{tag}类文章写作。这份指南应具有可操作性，并提供如何模仿其风格的清晰说明。涵盖语气、语态、句式结构、词汇、修辞策略、结构、开头/结尾。利用提供的数据和例子来构建指南。
输出格式: 一份详细、结构良好的 Markdown 文档，标题为"{self.author_name} {tag}类文章风格指南"。
"""

        messages = [{'role': 'user', 'content': guide_prompt}]
        guide_response = []
        async for role, content in self.llm_client.stream_chat(
            messages=messages,
            model=self.llm_config.model_id
        ):
            guide_response.append(content)

        # 合并响应内容
        guide_content = "".join(guide_response)
        
        # 保存风格指南
        self.output_manager.save_step_output(f"style_guide_{tag}", {"content": guide_content})
        return guide_content

    async def analyze_author_style(self, articles_dir: str) -> AsyncGenerator[str, None]:
        """分析作者风格的主方法"""
        # 获取LLM客户端
        logger.info('调用 ThinkingGemini 对话方法')
        result = llm_service_manager.get_client("Gemini/Gemini-2.0-Flash-thinking")
        self.llm_client, self.llm_config = result

        # 检查并读取目录
        dir_path = await self.check_dir_exists(articles_dir)
        articles = await self.read_markdown_files(dir_path)

        # 分析每篇文章
        all_analyses = []
        for article in articles:
            yield f"data: {json.dumps({'role': 'assistant', 'content': f'开始分析文章: {article["filename"]}'}, ensure_ascii=False)}\n\n"
            analysis = await self.analyze_single_article(article)
            all_analyses.append(analysis)
            yield f"data: {json.dumps({'role': 'assistant', 'content': f'完成文章分析: {article["filename"]}'}, ensure_ascii=False)}\n\n"

        # 按tag聚合分析结果
        tag_groups = await self.aggregate_by_tag(all_analyses)
        yield f"data: {json.dumps({'role': 'assistant', 'content': '开始生成风格指南'}, ensure_ascii=False)}\n\n"

        # 为每个tag生成风格指南
        for tag, analyses in tag_groups.items():
            guide_content = await self.generate_style_guide(tag, analyses)
            yield f"data: {json.dumps({'role': 'assistant', 'content': f'生成{tag}类文章风格指南完成'}, ensure_ascii=False)}\n\n"

        yield "data: [DONE]\n\n"

    def get_tid(self) -> str:
        """获取当前任务ID"""
        return self.output_manager.get_tid() 