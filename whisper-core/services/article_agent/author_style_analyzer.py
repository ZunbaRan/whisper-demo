import os
import json
from typing import Dict, List, Any, AsyncGenerator, Tuple
import logging
from services.llm.agent.base_agent import BaseAgent

logger = logging.getLogger(__name__)

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

输出格式: 请以JSON格式返回结果，包含以下字段：
- tone_and_voice: 语气与语态（字符串数组）
- sentence_structure: 句式结构（字符串）
- average_sentence_length: 平均句长（整数）
- vocabulary: 词汇选择（字符串数组）
- rhetorical_devices: 修辞手法（字符串数组）
- paragraphing_and_flow: 段落与流畅性（字符串）
- opening_closing_patterns: 开头与结尾模式（字符串数组）"""

    async def pre_process(self) -> None:
        pass

    async def build_messages(self) -> List[Dict[str, str]]:
        prompt = await self.build_prompt(
            self.PROMPT_TEMPLATE,
            author_name=self.context["author_name"],
            content=self.context["content"]
        )
        return [{'role': 'user', 'content': prompt}]

    async def process_response(self, response: AsyncGenerator[Tuple[str, str], None]) -> AsyncGenerator[Tuple[str, str], None]:
        async for role, content in response:
            yield role, content
        filename = self.context.get("filename", "unknown")
        yield 'assistant', f'完成文章分析: {filename}'

    async def post_process(self) -> None:
        pass

    async def parse_response(self, response: List[str]) -> Dict[str, Any]:
        try:
            # 合并所有响应内容
            full_response = "".join(response)
            
            # 提取JSON内容
            if "```json" in full_response:
                # 找到开始和结束标记
                start = full_response.find("```json") + 7
                end = full_response.find("```", start)
                if end != -1:
                    json_content = full_response[start:end].strip()
                    return json.loads(json_content)
            
            # 如果没有找到JSON标记，尝试直接解析
            return json.loads(full_response)
            
        except json.JSONDecodeError as e:
            logger.error(f"解析JSON响应失败: {str(e)}")
            return {
                "tone_and_voice": [],
                "sentence_structure": "",
                "average_sentence_length": 0,
                "vocabulary": [],
                "rhetorical_devices": [],
                "paragraphing_and_flow": "",
                "opening_closing_patterns": []
            }

class StyleGuideGenerator(BaseAgent):
    """风格指南生成Agent"""
    
    PROMPT_TEMPLATE = """角色: 你是一位大师级写作指导，将风格分析综合成一份实用的指南。
背景: 基于对 {author_name} 的 {article_count} 篇文章的分析，观察到以下模式：
{stats}

任务: 创建一份全面的"风格指南"，用于模仿 {author_name} 的写作风格。这份指南应具有可操作性，并提供如何模仿其风格的清晰说明。涵盖语气、语态、句式结构、词汇、修辞策略、结构、开头/结尾。利用提供的数据和例子来构建指南。
输出格式: 一份详细、结构良好的 Markdown 文档，标题为"{author_name} 写作风格指南"。"""

    async def pre_process(self) -> None:
        analyse_str = self.context["content"]
        if analyse_str:
            # 转化为 list Dict[str, Any]]
            analyses = json.loads(analyse_str)
        else:
            analyses = []

        self.context["stats"] = self.calculate_stats(analyses)

    def calculate_stats(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算统计信息"""
        stats = {
            "common_tones": [],
            "avg_sentence_length": 0,
            "common_devices": [],
            "vocabulary_patterns": [],
            "structure_habits": []
        }
        
        # 计算平均句长
        total_length = 0
        count = 0
        for analysis in analyses:
            if analysis.get("average_sentence_length"):
                total_length += analysis["average_sentence_length"]
                count += 1
        stats["avg_sentence_length"] = total_length / count if count > 0 else 0
        
        # 收集常见的语气和语态
        tone_counts = {}
        for analysis in analyses:
            for tone in analysis.get("tone_and_voice", []):
                tone_counts[tone] = tone_counts.get(tone, 0) + 1
        stats["common_tones"] = sorted(tone_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # 收集常见的修辞手法
        device_counts = {}
        for analysis in analyses:
            for device in analysis.get("rhetorical_devices", []):
                device_counts[device] = device_counts.get(device, 0) + 1
        stats["common_devices"] = sorted(device_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # 收集词汇模式
        vocab_counts = {}
        for analysis in analyses:
            for word in analysis.get("vocabulary", []):
                vocab_counts[word] = vocab_counts.get(word, 0) + 1
        stats["vocabulary_patterns"] = sorted(vocab_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # 收集结构习惯
        structure_counts = {}
        for analysis in analyses:
            structure = analysis.get("paragraphing_and_flow", "")
            if structure:
                structure_counts[structure] = structure_counts.get(structure, 0) + 1
        stats["structure_habits"] = sorted(structure_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return stats

    async def build_messages(self) -> List[Dict[str, str]]:
        prompt = await self.build_prompt(
            self.PROMPT_TEMPLATE,
            author_name=self.context["author_name"],
            article_count=len(self.context["stats"]),
            stats=json.dumps(self.context["stats"], ensure_ascii=False, indent=2)
        )
        return [{'role': 'user', 'content': prompt}]

    async def process_response(self, response: AsyncGenerator[Tuple[str, str], None]) -> AsyncGenerator[Tuple[str, str], None]:
        async for role, content in response:
            yield role, content
        yield 'assistant', '生成写作风格指南完成'

    async def post_process(self) -> None:
        pass

    async def parse_response(self, response: List[str]) -> Dict[str, Any]:
        return {"content": "".join(response)}

class AuthorStyleAnalyzer:
    """作者风格分析协调器"""
    
    def __init__(self, author_name: str):
        self.author_name = author_name
        self.article_analyzer = SingleArticleAnalyzer()
        self.guide_generator = StyleGuideGenerator()

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