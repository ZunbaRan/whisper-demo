import re

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

    # 3. 移出所有的标点符号
    clean_title = re.sub(r'[^\w\s]', '', clean_title)
    
    # 4. 限制长度（Windows 文件名长度限制为 255 字符）
    if len(clean_title) > 200:  # 留一些余地给扩展名
        clean_title = clean_title[:200]
        
    # 4. 确保文件名不为空
    if not clean_title:
        clean_title = "untitled"
        
    return clean_title 