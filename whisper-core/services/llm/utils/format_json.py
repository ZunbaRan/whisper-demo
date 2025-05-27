import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class FormatJson:
    """JSON格式化工具类"""

    @staticmethod
    async def llm_parse(response: str, default: Optional[Any] = None) -> Any:
        """解析响应
        
        Args:
            response: 要解析的响应字符串
            default: 解析失败时返回的默认值，默认为None
            
        Returns:
            Any: 解析后的Python对象，可能是dict、list等，解析失败时返回default值
        """
        try:
            if "[DONE]" in response:
                response = response.replace("[DONE]", "")

            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end != -1:
                    json_content = response[start:end].strip()
                    return json.loads(json_content)
            else:
                return json.loads("".join(response))
        
        except json.JSONDecodeError as e:
            logger.error(f"解析JSON响应失败: {str(e)}, 原始响应: {response}")
            if default is not None:
                return default
            else:
                return None

