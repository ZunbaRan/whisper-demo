from typing import Dict, Any, Optional
import json
import os
import uuid
from datetime import datetime

class OutputManager:
    """输出管理器"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.tid = str(uuid.uuid4())
        self.outputs: Dict[str, Dict[str, Any]] = {}
        
    def save_step_output(self, step_name: str, data: Dict[str, Any]) -> None:
        """保存步骤输出
        
        Args:
            step_name: 步骤名称
            data: 要保存的数据
        """
        self.outputs[step_name] = data
        
        # 保存到文件
        output_path = os.path.join(self.output_dir, self.tid)
        os.makedirs(output_path, exist_ok=True)
        
        file_path = os.path.join(output_path, f"{step_name}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def get_step_output(self, step_name: str) -> Dict[str, Any]:
        """获取步骤输出
        
        Args:
            step_name: 步骤名称
            
        Returns:
            Dict[str, Any]: 步骤输出数据
        """
        # 首先从内存中获取
        if step_name in self.outputs:
            return self.outputs[step_name]
            
        # 如果内存中没有，尝试从文件读取
        file_path = os.path.join(self.output_dir, self.tid, f"{step_name}.json")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
                
        return {}
        
    def get_tid(self) -> str:
        """获取当前任务ID
        
        Returns:
            str: 任务ID
        """
        return self.tid
        
    def get_all_outputs(self) -> Dict[str, Dict[str, Any]]:
        """获取所有输出
        
        Returns:
            Dict[str, Dict[str, Any]]: 所有输出数据
        """
        return self.outputs.copy() 