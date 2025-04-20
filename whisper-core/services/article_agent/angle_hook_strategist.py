from typing import Dict, List, Any, AsyncGenerator
import json
import logging
from services.llm.agent.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class AngleHookStrategist(BaseAgent):
    """角度与引子策略师"""
    
    PROMPT_TEMPLATE = """角色: 你是一位创意内容策略师和专家级文案撰稿人，擅长制造病毒式内容的引子。
背景: 一个播客的核心信息是 '{thesis}'。关键要点包括 {actionable_advice}。
目标受众是: {target_audience}。
我们希望文章能融入 {emotional_elements} 的元素。

任务: 基于此播客内容，为文章构思 3-5 个不同的角度或"引子"。对于每个角度：
1. 清晰陈述该角度/引子。
2. 解释*为什么*它会与目标受众产生共鸣。
3. 建议它如何与播客的核心信息联系起来。
4. 简要说明期望的互动元素（'焦虑'/'争议'）可以如何融入这个角度。

输出格式: 请以JSON格式返回结果，包含以下字段：
- angles: 角度列表（数组，每个元素包含以下字段）
  - angle: 角度描述（字符串）
  - resonance: 与目标受众的共鸣点（字符串）
  - connection: 与核心信息的联系（字符串）
  - emotional_integration: 情感元素的融入方式（字符串）"""

    def __init__(self, target_audience: str = "寻求获取财富提升,以及阶级跨越的年轻人士",
                 emotional_elements: str = "落后的焦虑, 挑战传统智慧等等, 具有争议,冲突,对立,或者传播焦虑"):
        super().__init__()
        self.target_audience = target_audience
        self.emotional_elements = emotional_elements

    async def pre_process(self) -> None:
        """预处理：验证输入数据"""
        required_fields = ["thesis", "actionable_advice", "examples"]
        for field in required_fields:
            if field not in self.context:
                raise ValueError(f"缺少必要字段: {field}")

    async def build_messages(self) -> List[Dict[str, str]]:
        """构建消息"""
        # 从context中获取必要信息
        thesis = self.context["thesis"]
        key_points = self.context["actionable_advice"][:2]  # 取前两个关键点
        
        prompt = await self.build_prompt(
            self.PROMPT_TEMPLATE,
            thesis=thesis,
            key_points=json.dumps(key_points, ensure_ascii=False),
            target_audience=self.target_audience,
            emotional_elements=self.emotional_elements
        )
        return [{'role': 'user', 'content': prompt}]

    async def process_response(self, response: List[str]) -> AsyncGenerator[str, None]:
        """处理响应"""
        result = await self.parse_response(response)
        await self.save_step_output("angle_hook_strategies", result)
        
        # 输出每个角度的信息
        for angle in result.get("angles", []):
            yield f"data: {json.dumps({
                'role': 'assistant',
                'content': f"角度: {angle['angle']}\n"
                          f"共鸣点: {angle['resonance']}\n"
                          f"联系: {angle['connection']}\n"
                          f"情感融入: {angle['emotional_integration']}"
            }, ensure_ascii=False)}\n\n"

    async def post_process(self) -> None:
        """后处理：清理临时数据"""
        pass

    async def parse_response(self, response: List[str]) -> Dict[str, Any]:
        """解析响应"""
        try:
            return json.loads("".join(response))
        except json.JSONDecodeError as e:
            logger.error(f"解析JSON响应失败: {str(e)}")
            return {"angles": []}

    async def generate_angles(self, podcast_result: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """生成文章角度的主方法"""
        try:
            # 设置context
            self.context = {
                "thesis": podcast_result.get("thesis", ""),
                "actionable_advice": podcast_result.get("actionable_advice", []),
                "examples": podcast_result.get("examples", [])
            }
            
            # 调用LLM生成角度
            async for result in self.call():
                yield result
                
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            error_msg = f"生成文章角度时发生错误: {str(e)}"
            logger.error(error_msg)
            yield f"data: {json.dumps({'role': 'error', 'content': error_msg}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n" 