import os
from docx import Document

def convert_docx_to_md(input_path, output_dir=None):
    """
    转换docx文件为markdown格式

    Args:
        input_path: docx文件路径或包含docx文件的目录路径
        output_dir: 转换结果输出目录（可选，默认为当前目录）

    Returns:
        list: 成功转换的文件路径列表
    """
    if output_dir is None:
        output_dir = os.path.dirname(input_path) or '.'

    converted_files = []

    # 处理单个文件
    if os.path.isfile(input_path) and input_path.endswith('.docx'):
        return [process_single_file(input_path, output_dir)]

    # 处理目录
    for filename in os.listdir(input_path):
        if filename.endswith('.docx'):
            file_path = os.path.join(input_path, filename)
            converted_files.append(process_single_file(file_path, output_dir))

    return converted_files

def process_single_file(docx_path, output_dir):
    """处理单个docx文件"""
    doc = Document(docx_path)
    md_filename = os.path.splitext(os.path.basename(docx_path))[0] + '.md'
    md_path = os.path.join(output_dir, md_filename)

    with open(md_path, 'w', encoding='utf-8') as f:
        for para in doc.paragraphs:
            # 处理不同样式的段落
            if para.style.name.startswith('Heading'):
                level = int(para.style.name.split()[-1])
                f.write('#' * level + ' ' + para.text + '\n\n')
            elif para.style.name == 'List Bullet':
                f.write('- ' + para.text + '\n')
            else:
                f.write(para.text + '\n\n')

    return md_path

# 转换整个目录
convert_docx_to_md('G:\\project\\whis-server\\whisper-demo\\whisper-core\\input\\banfo_word', 'G:\\project\\whis-server\\whisper-demo\\whisper-core\\input')