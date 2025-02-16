import json
import xmltodict
from pathlib import Path

def convert_xml_to_json():
    """将 XML 文件转换为 JSON 格式"""
    # 设置输入输出路径
    input_path = Path("../doc/1.xml")
    output_path = input_path.with_suffix('.json')
    
    if not input_path.exists():
        print(f"错误: 找不到XML文件: {input_path}")
        return
        
    try:
        print("\n=== 开始转换 XML 到 JSON ===")
        print(f"输入文件: {input_path}")
        print(f"输出文件: {output_path}")
        
        # 读取XML文件
        with open(input_path, 'r', encoding='utf-8') as xml_file:
            xml_content = xml_file.read()
            
        # 转换为Python字典
        data_dict = xmltodict.parse(xml_content)
        
        # 转换为JSON并保存
        with open(output_path, 'w', encoding='utf-8') as json_file:
            json.dump(data_dict, json_file, ensure_ascii=False, indent=2)
            
        print("\n转换成功!")
        
        # 显示文件大小
        xml_size = input_path.stat().st_size
        json_size = output_path.stat().st_size
        print(f"\n文件大小对比:")
        print(f"XML  文件: {format_size(xml_size)}")
        print(f"JSON 文件: {format_size(json_size)}")
        
    except Exception as e:
        print(f"\n转换失败:")
        print(f"错误信息: {str(e)}")
        import traceback
        print(f"错误详情:\n{traceback.format_exc()}")

def format_size(size_in_bytes):
    """格式化文件大小显示"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} TB"

if __name__ == "__main__":
    convert_xml_to_json() 