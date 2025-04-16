import os
import json
import uuid
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class OutputManager:
    def __init__(self, base_output_dir: str = "output"):
        self.base_output_dir = base_output_dir
        self.tid = str(uuid.uuid4())
        self.output_dir = os.path.join(base_output_dir, self.tid)
        self._ensure_output_dir()

    def _ensure_output_dir(self):
        """确保输出目录存在"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"创建输出目录: {self.output_dir}")

    def save_step_output(self, step_name: str, data: Dict[str, Any]):
        """保存步骤输出到文件"""
        output_file = os.path.join(self.output_dir, f"{step_name}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"保存步骤 {step_name} 的输出到 {output_file}")

    def get_step_output(self, step_name: str) -> Dict[str, Any]:
        """获取步骤输出"""
        output_file = os.path.join(self.output_dir, f"{step_name}.json")
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def get_tid(self) -> str:
        """获取当前任务ID"""
        return self.tid 