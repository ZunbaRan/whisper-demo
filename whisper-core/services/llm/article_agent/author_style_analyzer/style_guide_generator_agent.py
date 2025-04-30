import json
from typing import List, Dict, Any, AsyncGenerator, Tuple

from services.llm.agent.base_agent import BaseAgent


class StyleGuideGenerator(BaseAgent):
    """风格指南生成Agent"""

    PROMPT_TEMPLATE = """角色: 你是一位大师级写作指导，将风格分析综合成一份实用的指南。
背景: 基于对 {author_name} 的 {article_count} 篇文章的分析，观察到以下模式：
{stats}

任务: 创建一份全面的"风格指南"，用于模仿 {author_name} 的写作风格。这份指南应具有可操作性，并提供如何模仿其风格的清晰说明。涵盖语气、语态、句式结构、词汇、修辞策略、结构、开头/结尾。利用提供的数据和例子来构建指南。
输出格式: 一份详细、结构良好的 Markdown 文档，标题为"{author_name} 写作风格指南"。"""

    async def pre_process(self) -> None:
        analyses = self.context["content"]
        if not analyses:
            analyses = []

        self.context["stats"] = self.calculate_stats(analyses)

    def calculate_stats(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算统计信息"""
        stats = {
            "common_tones": [],
            "avg_sentence_length": 0,
            "common_devices": [],
            "vocabulary_patterns": [],
            "structure_habits": [],
            "paragraphing_and_fLow": [],
            "opening_closing_patterns": []
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

        # 收集开头/结尾习惯
        pattern_counts = {}
        for analysis in analyses:
            for pattern in analysis.get("opening_closing_patterns", []):
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        stats["opening_closing_patterns"] = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:3]

        # 收集段落与流畅性
        flow_counts = {}
        for analysis in analyses:
            flow = analysis.get("paragraphing_and_flow", "")
            if flow:
                flow_counts[flow] = flow_counts.get(flow, 0) + 1
        stats["paragraphing_and_fLow"] = sorted(flow_counts.items(), key=lambda x: x[1], reverse=True)[:3]

        return stats

    async def build_messages(self) -> List[Dict[str, str]]:
        prompt = await self.build_prompt(
            self.PROMPT_TEMPLATE,
            author_name=self.context["author_name"],
            article_count=len(self.context["stats"]),
            stats=json.dumps(self.context["stats"], ensure_ascii=False, indent=2)
        )
        return [{'role': 'user', 'content': prompt}]

    async def process_response(self, response: AsyncGenerator[Tuple[str, str], None]) -> AsyncGenerator[
        Tuple[str, str], None]:
        async for role, content in response:
            yield role, content
        yield 'assistant', '生成写作风格指南完成'

    async def post_process(self) -> None:
        pass

    async def parse_response(self, response: str) -> Dict[str, Any]:
        return json.loads(response)
