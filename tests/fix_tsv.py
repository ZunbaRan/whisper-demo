import os
import pandas as pd
import re
from typing import List, Dict


def clean_filename(title: str) -> str:
    """清理文件名，移除不合法字符"""
    
    # 检查输入是否为None或空字符串
    if not title:
        print("标题为空，返回 untitled")
        return "untitled"
        
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

def fix_tsv_file(tsv_path: str = "./output/feed/feed.tsv", output_dir: str = "./output") -> None:
    """修正 TSV 文件，添加和更新转写状态"""
    print("\n=== 开始修正 TSV 文件 ===")
    
    if not os.path.exists(tsv_path):
        print(f"错误: TSV 文件不存在: {tsv_path}")
        return
        
    try:
        # 读取 TSV 文件
        print(f"读取 TSV 文件: {tsv_path}")
        df = pd.read_csv(tsv_path, sep='\t')
        
        # 确保存在所需的列
        if 'isTranscription' not in df.columns:
            print("添加 isTranscription 列")
            df['isTranscription'] = 'false'
            
        # 重置所有状态为 false
        df['isDownload'] = 'false'
        df['isTranscription'] = 'false'
        
        # 获取所有文本文件
        txt_files = set()
        for root, _, files in os.walk(output_dir):
            for file in files:
                if file.endswith('.txt') and not file.endswith('_simplified.txt'):
                    txt_files.add(os.path.splitext(file)[0])
        
        print(f"\n在输出目录中找到 {len(txt_files)} 个文本文件")
        
        # 更新状态
        updated_count = 0
        for index, row in df.iterrows():
            title = row['title']
            clean_name = clean_filename(title)
            
            if clean_name in txt_files:
                df.at[index, 'isDownload'] = 'true'
                df.at[index, 'isTranscription'] = 'true'
                updated_count += 1
                print(f"更新状态: {title}")
        
        # 保存更新后的文件
        df.to_csv(tsv_path, sep='\t', index=False)
        print(f"\n=== TSV 文件修正完成 ===")
        print(f"总条目数: {len(df)}")
        print(f"更新条目数: {updated_count}")
        
    except Exception as e:
        print(f"修正过程出错: {str(e)}")
        import traceback
        print(f"错误详情:\n{traceback.format_exc()}")

if __name__ == "__main__":
    fix_tsv_file() 