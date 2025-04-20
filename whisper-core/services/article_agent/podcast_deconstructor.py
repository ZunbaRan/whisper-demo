from typing import Dict, List, Any, AsyncGenerator
import json
import logging
from services.llm.agent.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class ThemeAnalysisAgent(BaseAgent):
    """主题分析Agent"""
    
    PROMPT_TEMPLATE = """角色: 你是一位专注于总结口语内容的专家级分析师。
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

    async def pre_process(self) -> None:
        pass

    async def build_messages(self) -> List[Dict[str, str]]:
        content = self.context["content"]
        prompt = await self.build_prompt(self.PROMPT_TEMPLATE, text=content)
        return [{'role': 'user', 'content': prompt}]

    async def process_response(self, response: List[str]) -> AsyncGenerator[str, None]:
        result = await self.parse_response(response)
        await self.save_step_output("theme_analysis", result)
        yield f"data: {json.dumps({'role': 'assistant', 'content': '主题分析完成'}, ensure_ascii=False)}\n\n"

    async def post_process(self) -> None:
        pass

    async def parse_response(self, response: List[str]) -> Dict[str, Any]:
        try:
            return json.loads("".join(response))
        except json.JSONDecodeError as e:
            logger.error(f"解析JSON响应失败: {str(e)}")
            return {"main_theme": "", "thesis": "", "sub_topics": []}

class ElementsExtractionAgent(BaseAgent):
    """元素提取Agent"""
    
    PROMPT_TEMPLATE = """角色: 你是一位细致的内容提取者，专注于识别对话中的有影响力元素。
背景: 分析以下播客文字稿： "{text}"
已知主题信息：{theme_info}

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

    async def pre_process(self) -> None:
        pass

    async def build_messages(self) -> List[Dict[str, str]]:
        content = self.context["content"]
        theme_result = self.context["theme_result"]
        prompt = await self.build_prompt(
            self.PROMPT_TEMPLATE,
            text=content,
            theme_info=json.dumps(theme_result, ensure_ascii=False)
        )
        return [{'role': 'user', 'content': prompt}]

    async def process_response(self, response: List[str]) -> AsyncGenerator[str, None]:
        result = await self.parse_response(response)
        await self.save_step_output("elements_extraction", result)
        yield f"data: {json.dumps({'role': 'assistant', 'content': '关键元素提取完成'}, ensure_ascii=False)}\n\n"

    async def post_process(self) -> None:
        pass

    async def parse_response(self, response: List[str]) -> Dict[str, Any]:
        try:
            return json.loads("".join(response))
        except json.JSONDecodeError as e:
            logger.error(f"解析JSON响应失败: {str(e)}")
            return {
                "golden_quotes": [],
                "actionable_advice": [],
                "examples": [],
                "data_points": []
            }

class StructureAnalysisAgent(BaseAgent):
    """结构分析Agent"""
    
    PROMPT_TEMPLATE = """角色: 你是一位逻辑思考者，擅长辨别论证结构。
背景: 基于以下信息，判断原始讨论可能的逻辑流程或叙事结构：
主题信息：{theme_info}
关键元素：{elements_info}

任务: 概述其结构。例如：
    - 提出问题 -> 分析原因 -> 提供解决方案 -> 举例说明
    - 概念介绍 -> 解释说明 -> 案例1 -> 案例2 -> 结论
    - 按时间顺序叙事 -> 关键经验教训

输出格式: 请以JSON格式返回结果，包含以下字段：
- structure_outline: 结构大纲列表（字符串数组）"""

    async def pre_process(self) -> None:
        pass

    async def build_messages(self) -> List[Dict[str, str]]:
        theme_result = self.context["theme_result"]
        elements_result = self.context["elements_result"]
        prompt = await self.build_prompt(
            self.PROMPT_TEMPLATE,
            theme_info=json.dumps(theme_result, ensure_ascii=False),
            elements_info=json.dumps(elements_result, ensure_ascii=False)
        )
        return [{'role': 'user', 'content': prompt}]

    async def process_response(self, response: List[str]) -> AsyncGenerator[str, None]:
        result = await self.parse_response(response)
        await self.save_step_output("structure_analysis", result)
        yield f"data: {json.dumps({'role': 'assistant', 'content': '结构分析完成'}, ensure_ascii=False)}\n\n"

    async def post_process(self) -> None:
        pass

    async def parse_response(self, response: List[str]) -> Dict[str, Any]:
        try:
            return json.loads("".join(response))
        except json.JSONDecodeError as e:
            logger.error(f"解析JSON响应失败: {str(e)}")
            return {"structure_outline": []}

class PodcastDeconstructor:
    """播客解构协调器"""
    
    def __init__(self):
        self.theme_agent = ThemeAnalysisAgent()
        self.elements_agent = ElementsExtractionAgent()
        self.structure_agent = StructureAnalysisAgent()
        
    async def process_podcast(self, content: str) -> AsyncGenerator[str, None]:
        try:
            # 1. 主题分析
            async for result in self.theme_agent.call(content=content):
                yield result
            theme_result = await self.theme_agent.get_step_output("theme_analysis")
            
            # 2. 元素提取
            async for result in self.elements_agent.call(
                content=content,
                theme_result=theme_result
            ):
                yield result
            elements_result = await self.elements_agent.get_step_output("elements_extraction")
            
            # 3. 结构分析
            async for result in self.structure_agent.call(
                theme_result=theme_result,
                elements_result=elements_result
            ):
                yield result
            structure_result = await self.structure_agent.get_step_output("structure_analysis")
            
            # 4. 生成最终结果
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
            
            # 输出最终结果
            for key, value in final_result.items():
                response_data = {
                    "role": "assistant",
                    "content": f"{key}: {json.dumps(value, ensure_ascii=False)}"
                }
                yield f"data: {json.dumps(response_data, ensure_ascii=False)}\n\n"
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            error_msg = f"处理播客内容时发生错误: {str(e)}"
            logger.error(error_msg)
            yield f"data: {json.dumps({'role': 'error', 'content': error_msg}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n" 