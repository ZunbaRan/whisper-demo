import os
from pathlib import Path

def clean_non_txt_files():
    """删除 output 目录下不包含 feed 文件夹的所有非 .txt 文件"""
    output_dir = Path("../output")
    
    if not output_dir.exists():
        print(f"错误: 找不到目录: {output_dir}")
        return
        
    deleted_count = 0
    failed_count = 0
    skipped_count = 0
    
    print("\n=== 开始清理文件 ===")
    
    # 遍历 output 目录
    for root, dirs, files in os.walk(output_dir, topdown=True):
        # 跳过 feed 目录
        if "feed" in root:
            continue
            
        for file in files:
            file_path = Path(root) / file
            
            # 如果不是 .txt 文件，则删除
            if file_path.suffix.lower() != '.txt':
                try:
                    print(f"删除文件: {file_path.relative_to(output_dir)}")
                    file_path.unlink()
                    deleted_count += 1
                except Exception as e:
                    print(f"删除失败: {file_path.relative_to(output_dir)}")
                    print(f"错误信息: {str(e)}")
                    failed_count += 1
            else:
                skipped_count += 1
    
    print("\n=== 清理完成 ===")
    print(f"删除: {deleted_count} 个文件")
    print(f"保留: {skipped_count} 个 .txt 文件")
    print(f"失败: {failed_count} 个文件")

if __name__ == "__main__":
    clean_non_txt_files() 