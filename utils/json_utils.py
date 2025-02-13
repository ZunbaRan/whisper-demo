import json
import os

def extract_segments_info(input_json_path, output_dir="output"):
    """
    从原始JSON文件中提取简化的segments信息
    """
    try:
        with open(input_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 提取需要的信息
        simplified_data = {
            "segments": []
        }
        
        for segment in data.get("segments", []):
            words = " ".join([word["word"] for word in segment.get("words", []) if "word" in word])
            speaker = segment.get("speaker", "")
            
            if words and speaker:
                simplified_data["segments"].append({
                    "words": words,
                    "speaker": speaker
                })
        
        # 创建简化版本的输出文件
        filename = os.path.basename(input_json_path)
        base_name = os.path.splitext(filename)[0]
        output_path = os.path.join(output_dir, f"{base_name}_simplified.json")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(simplified_data, f, ensure_ascii=False, indent=2)
            
        return output_path
    
    except Exception as e:
        raise Exception(f"处理JSON文件时出错: {str(e)}")

def format_transcription_to_text(simplified_json_path: str, output_txt_path: str) -> None:
    """
    将简化的JSON转换为文本格式
    Args:
        simplified_json_path: 简化版JSON文件的路径
        output_txt_path: 输出文本文件的路径
    """
    try:
        # 读取简化的JSON文件
        with open(simplified_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 格式化为 [speaker]: words 格式
        formatted_lines = []
        for segment in data.get("segments", []):
            speaker = segment.get("speaker", "Unknown")
            words = segment.get("words", "")
            if words:
                formatted_lines.append(f"[{speaker}]: {words}")
        
        # 写入文本文件
        with open(output_txt_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(formatted_lines))
            
    except Exception as e:
        raise Exception(f"处理转写文本时出错: {str(e)}") 