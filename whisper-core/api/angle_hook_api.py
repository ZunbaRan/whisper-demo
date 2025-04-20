from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import json
import os
from services.article_agent.angle_hook_strategist import AngleHookStrategist
from services.llm.agent.output_manager import OutputManager

router = APIRouter()
output_manager = OutputManager()

@router.post("/generate-angles")
async def generate_angles(podcast_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    生成文章角度的API端点
    
    Args:
        podcast_result: 包含以下字段的字典
            - thesis: 播客的核心论点
            - actionable_advice: 可执行的建议列表
            - examples: 示例列表
    
    Returns:
        Dict[str, Any]: 包含生成的角度和状态信息的字典
    """
    try:
        # 创建策略师实例
        strategist = AngleHookStrategist()
        
        # 生成角度
        angles = []
        async for result in strategist.generate_angles(podcast_result):
            if result.startswith("data: "):
                data = json.loads(result[6:])
                if data.get("role") == "assistant":
                    angles.append(data.get("content", ""))
        
        # 获取完整的分析结果
        analysis_result = await strategist.get_step_output("angle_hook_strategies")
        
        # 保存结果到文件
        output_dir = os.path.join("output", "angle_hook")
        os.makedirs(output_dir, exist_ok=True)
        
        # 为每个角度创建单独的文件
        for i, angle in enumerate(analysis_result.get("angles", [])):
            angle_file = os.path.join(output_dir, f"angle_{i+1}.json")
            with open(angle_file, "w", encoding="utf-8") as f:
                json.dump(angle, f, ensure_ascii=False, indent=2)
        
        # 保存完整的分析结果
        summary_file = os.path.join(output_dir, "summary.json")
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        
        return {
            "status": "success",
            "message": "角度生成完成",
            "angles": angles,
            "analysis_result": analysis_result,
            "output_files": {
                "summary": summary_file,
                "individual_angles": [f"angle_{i+1}.json" for i in range(len(analysis_result.get("angles", [])))]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get-angles/{angle_id}")
async def get_angle(angle_id: int) -> Dict[str, Any]:
    """
    获取特定角度的详细信息
    
    Args:
        angle_id: 角度的ID（从1开始）
    
    Returns:
        Dict[str, Any]: 包含角度详细信息的字典
    """
    try:
        angle_file = os.path.join("output", "angle_hook", f"angle_{angle_id}.json")
        if not os.path.exists(angle_file):
            raise HTTPException(status_code=404, detail=f"角度 {angle_id} 不存在")
        
        with open(angle_file, "r", encoding="utf-8") as f:
            return json.load(f)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get-summary")
async def get_summary() -> Dict[str, Any]:
    """
    获取所有角度的摘要信息
    
    Returns:
        Dict[str, Any]: 包含所有角度摘要的字典
    """
    try:
        summary_file = os.path.join("output", "angle_hook", "summary.json")
        if not os.path.exists(summary_file):
            raise HTTPException(status_code=404, detail="摘要文件不存在")
        
        with open(summary_file, "r", encoding="utf-8") as f:
            return json.load(f)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 