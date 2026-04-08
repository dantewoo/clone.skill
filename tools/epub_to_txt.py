#!/usr/bin/env python3
"""
EPUB 转 TXT 工具

用法：
    python3 epub_to_txt.py --input 文件.epub --output 文件.txt
"""

import zipfile
import argparse
from pathlib import Path
from html.parser import HTMLParser
import re


class HTMLTextExtractor(HTMLParser):
    """提取 HTML 中的纯文本"""
    def __init__(self):
        super().__init__()
        self.text = []

    def handle_data(self, data):
        self.text.append(data)

    def get_text(self):
        return ''.join(self.text)


def epub_to_txt(epub_path: str, output_path: str):
    """将 EPUB 转换为 TXT"""
    print(f"正在解析：{epub_path}")

    text_content = []

    try:
        with zipfile.ZipFile(epub_path, 'r') as zip_ref:
            # 获取所有文件列表
            file_list = zip_ref.namelist()

            # 找到所有 HTML/XHTML 文件
            html_files = [f for f in file_list if f.endswith(('.html', '.xhtml', '.htm'))]
            html_files.sort()  # 按文件名排序

            print(f"✓ 找到 {len(html_files)} 个内容文件")

            for html_file in html_files:
                try:
                    content = zip_ref.read(html_file).decode('utf-8', errors='ignore')

                    # 提取纯文本
                    parser = HTMLTextExtractor()
                    parser.feed(content)
                    text = parser.get_text()

                    # 清理文本
                    text = re.sub(r'\s+', ' ', text)  # 多个空白符替换为单个空格
                    text = text.strip()

                    if text:
                        text_content.append(text)

                except Exception as e:
                    print(f"  跳过文件 {html_file}: {e}")
                    continue

        # 合并所有文本
        full_text = '\n\n'.join(text_content)

        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_text)

        print(f"✓ 转换完成")
        print(f"✓ 输出文件：{output_path}")
        print(f"✓ 总字数：{len(full_text)}")

    except Exception as e:
        print(f"✗ 转换失败：{e}")
        raise


def main():
    parser = argparse.ArgumentParser(description='EPUB 转 TXT 工具')
    parser.add_argument('--input', required=True, help='输入 EPUB 文件路径')
    parser.add_argument('--output', required=True, help='输出 TXT 文件路径')

    args = parser.parse_args()

    epub_to_txt(args.input, args.output)


if __name__ == "__main__":
    main()
