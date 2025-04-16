import json
from typing import AsyncGenerator, Dict, Any
import logging
from services.llm.manager.llm_service_manager import llm_service_manager
from .output_manager import OutputManager

logger = logging.getLogger(__name__)

class PodcastDeconstructor:
    def __init__(self):
        self.llm_client = None
        self.llm_config = None
        self.output_manager = OutputManager()

    async def check_file_exists(self, file_path: str) -> str:
        """检查文件是否存在并返回绝对路径"""
        import os
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        return os.path.abspath(file_path)

    async def read_file(self, file_path: str) -> str:
        """读取文件内容"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    async def analyze_theme(self, text: str) -> Dict[str, Any]:
        """分析核心主题与论点"""
        theme_prompt = f"""角色: 你是一位专注于总结口语内容的专家级分析师。
背景: 以下是一期播客的文字稿。
文字稿: "{text}"
任务: 分析提供的文字稿，并识别：
1. 讨论的中心主题或主要议题。
2. 发言者提出的主要论点或主张。
3. 涵盖的关键子主题。
输出格式: 请以JSON格式返回结果，包含以下字段：
- main_theme: 中心主题（字符串）
- thesis: 主要论点（字符串）
- sub_topics: 子主题列表（字符串数组）"""

        messages = [{'role': 'user', 'content': theme_prompt}]
        theme_response = []
        async for role, content in self.llm_client.stream_chat(
            messages=messages,
            model=self.llm_config.model_id
        ):
            theme_response.append(content)

        # 解析LLM响应，提取主题信息
        result = {
            "main_theme": "",
            "thesis": "",
            "sub_topics": []
        }
        # TODO: 添加解析theme_response的逻辑，将结果填充到result中
        self.output_manager.save_step_output("theme_analysis", result)
        return result

    async def extract_elements(self, text: str) -> Dict[str, Any]:
        """提取关键元素"""
        # 获取主题分析结果
        theme_result = self.output_manager.get_step_output("theme_analysis")
        
        elements_prompt = f"""角色: 你是一位细致的内容提取者，专注于识别对话中的有影响力元素。
背景: 分析以下播客文字稿： "{text}"
已知主题信息：
- 中心主题: {theme_result.get('main_theme', '')}
- 主要论点: {theme_result.get('thesis', '')}
- 子主题: {', '.join(theme_result.get('sub_topics', []))}

任务: 基于以上主题信息，精确提取以下元素（原文引用或准确总结）：
1. 金句 (Golden Quotes): 识别并列出那些特别有见地、令人难忘、有力或完美概括核心观点的原话句子或短语。
2. 可行动建议/要点 (Actionable Advice/Takeaways): 列出发言者建议的清晰、简洁的建议或可执行步骤。
3. 例证/案例研究 (Illustrative Examples/Case Studies): 简要总结用于阐述观点的任何故事、轶事、具体的公司案例或个人经历。
4. 关键数据/统计 (Key Data/Statistics): 列出为支持主张而提及的任何具体数字、百分比或数据点。

输出格式: 请以JSON格式返回结果，包含以下字段：
- golden_quotes: 金句列表（字符串数组）
- actionable_advice: 可行动建议列表（字符串数组）
- examples: 例证列表（对象数组，每个对象包含summary和illustrates字段）
- data_points: 关键数据列表（字符串数组）"""

        messages = [{'role': 'user', 'content': elements_prompt}]
        elements_response = []
        async for role, content in self.llm_client.stream_chat(
            messages=messages,
            model=self.llm_config.model_id
        ):
            elements_response.append(content)

        result = {
            "golden_quotes": [],
            "actionable_advice": [],
            "examples": [],
            "data_points": []
        }
        # TODO: 添加解析elements_response的逻辑，将结果填充到result中
        self.output_manager.save_step_output("elements_extraction", result)
        return result

    async def analyze_structure(self, text: str) -> Dict[str, Any]:
        """分析结构大纲"""
        # 获取主题分析和关键元素提取的结果
        theme_result = self.output_manager.get_step_output("theme_analysis")
        elements_result = self.output_manager.get_step_output("elements_extraction")
        
        structure_prompt = f"""角色: 你是一位逻辑思考者，擅长辨别论证结构。
背景: 基于以下信息，判断原始讨论可能的逻辑流程或叙事结构：
- 中心主题: {theme_result.get('main_theme', '')}
- 主要论点: {theme_result.get('thesis', '')}
- 子主题: {', '.join(theme_result.get('sub_topics', []))}
- 关键元素: {json.dumps(elements_result, ensure_ascii=False)}

任务: 概述其结构。例如：
    - 提出问题 -> 分析原因 -> 提供解决方案 -> 举例说明
    - 概念介绍 -> 解释说明 -> 案例1 -> 案例2 -> 结论
    - 按时间顺序叙事 -> 关键经验教训

输出格式: 请以JSON格式返回结果，包含以下字段：
- structure_outline: 结构大纲列表（字符串数组）"""

        messages = [{'role': 'user', 'content': structure_prompt}]
        structure_response = []
        async for role, content in self.llm_client.stream_chat(
            messages=messages,
            model=self.llm_config.model_id
        ):
            structure_response.append(content)

        result = {
            "structure_outline": []
        }
        # TODO: 添加解析structure_response的逻辑，将结果填充到result中
        self.output_manager.save_step_output("structure_analysis", result)
        return result

    async def analyze_content(self, text: str) -> AsyncGenerator[str, None]:
        """分析播客内容并生成结构化数据"""
        # 获取LLM客户端
        logger.info('调用 ThinkingGemini 对话方法')
        result = llm_service_manager.get_client("Gemini/Gemini-2.0-Flash-thinking")
        self.llm_client, self.llm_config = result

        # 第一步：识别核心主题与论点
        theme_result = await self.analyze_theme(text)
        yield f"data: {json.dumps({'role': 'assistant', 'content': '主题分析完成'}, ensure_ascii=False)}\n\n"

        # 第二步：提取关键元素，使用原始文本和主题分析结果
        elements_result = await self.extract_elements(text)
        yield f"data: {json.dumps({'role': 'assistant', 'content': '关键元素提取完成'}, ensure_ascii=False)}\n\n"

        # 第三步：分析结构大纲，使用主题分析结果和关键元素
        structure_result = await self.analyze_structure(text)
        yield f"data: {json.dumps({'role': 'assistant', 'content': '结构分析完成'}, ensure_ascii=False)}\n\n"

        # 按照agent1.md中定义的结构化数据格式组合结果
        final_result = {
            # 来自主题分析
            "main_theme": theme_result.get("main_theme", ""),
            "thesis": theme_result.get("thesis", ""),
            "sub_topics": theme_result.get("sub_topics", []),
            
            # 来自关键元素提取
            "golden_quotes": elements_result.get("golden_quotes", []),
            "actionable_advice": elements_result.get("actionable_advice", []),
            "examples": elements_result.get("examples", []),
            "data_points": elements_result.get("data_points", []),
            
            # 来自结构分析
            "structure_outline": structure_result.get("structure_outline", [])
        }

        # 保存最终结果
        self.output_manager.save_step_output("final_result", final_result)

        # 流式输出最终结果
        for key, value in final_result.items():
            response_data = {
                "role": "assistant",
                "content": f"{key}: {json.dumps(value, ensure_ascii=False)}"
            }
            yield f"data: {json.dumps(response_data, ensure_ascii=False)}\n\n"

        yield "data: [DONE]\n\n"

    async def process_podcast(self, context_file_path: str) -> AsyncGenerator[str, None]:
        """处理播客文字稿的主方法"""
        # 验证文件存在
        absolute_path = await self.check_file_exists(context_file_path)

        # 读取文件内容
        content_text = await self.read_file(absolute_path)

        # 分析内容
        async for response in self.analyze_content(content_text):
            yield response

    def get_tid(self) -> str:
        """获取当前任务ID"""
        return self.output_manager.get_tid() 