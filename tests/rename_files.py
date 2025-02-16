import os
import pandas as pd
import re
from pathlib import Path

def clean_filename(title: str) -> str:
    """清理文件名，移除不合法字符"""
    # 替换 Windows 文件名中不允许的字符
    invalid_chars = r'[<>:"/\\|?*]'
    # 1. 替换非法字符为下划线
    clean_title = re.sub(invalid_chars, '_', title)
    # 2. 移除前后空格
    clean_title = clean_title.strip()
    # 3. 限制长度（Windows 文件名长度限制为 255 字符）
    if len(clean_title) > 200:  # 留一些余地给扩展名
        clean_title = clean_title[:200]
    # 4. 确保文件名不为空
    if not clean_title:
        clean_title = "untitled"
    return clean_title

def rename_files():
    # 读取TSV文件
    tsv_path = "../output/feed/feed.tsv"
    if not os.path.exists(tsv_path):
        print(f"错误: 找不到TSV文件: {tsv_path}")
        return
    
    # 读取TSV文件
    df = pd.read_csv(tsv_path, sep='\t', dtype={'id': str, 'title': str})
    
    # 创建id到title的映射
    id_to_title = dict(zip(df['id'], df['title']))
    
    # 获取output目录下的所有文件
    output_dir = "../output"
    renamed_count = 0
    failed_count = 0
    
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            # 检查文件是否符合 id_simplified.txt 格式
            if file.endswith('_simplified.txt'):
                file_id = file.replace('_simplified.txt', '')
                
                if file_id in id_to_title:
                    old_path = os.path.join(root, file)
                    clean_title = clean_filename(id_to_title[file_id])
                    new_filename = f"{clean_title}.txt"
                    new_path = os.path.join(root, new_filename)
                    
                    try:
                        # 如果目标文件已存在，先删除
                        if os.path.exists(new_path):
                            os.remove(new_path)
                            
                        os.rename(old_path, new_path)
                        print(f"重命名成功: {file} -> {new_filename}")
                        renamed_count += 1
                        
                        # 同时重命名对应的JSON文件（如果存在）
                        json_old_path = old_path.replace('.txt', '.json')
                        if os.path.exists(json_old_path):
                            json_new_path = new_path.replace('.txt', '.json')
                            if os.path.exists(json_new_path):
                                os.remove(json_new_path)
                            os.rename(json_old_path, json_new_path)
                            print(f"重命名成功: {os.path.basename(json_old_path)} -> {os.path.basename(json_new_path)}")
                            renamed_count += 1
                            
                    except Exception as e:
                        print(f"重命名失败: {file} -> {new_filename}")
                        print(f"错误信息: {str(e)}")
                        failed_count += 1
                else:
                    print(f"警告: 在TSV中找不到ID对应的标题: {file_id}")
                    failed_count += 1
    
    print("\n=== 重命名完成 ===")
    print(f"成功: {renamed_count} 个文件")
    print(f"失败: {failed_count} 个文件")

if __name__ == "__main__":
    rename_files() 