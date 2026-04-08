#!/usr/bin/env python3
"""
通用文本解析器

支持任意文本格式，自动识别类型并提取特征。

支持的文本类型：
1. 聊天记录（微信、QQ、Telegram 等）
2. 书籍/文章（PDF、TXT、MD）
3. 日记/博客
4. 社交媒体内容
5. 邮件
6. 其他任意文本

用法：
    python3 text_parser.py --input 文件路径 --target-name "对象名" --output-dir ./knowledge
    python3 text_parser.py --input 文件路径 --target-name "对象名" --text-type chat  # 指定类型
"""

import re
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict


class TextParser:
    """通用文本解析器"""

    # 时间权重规则（天数 -> 权重）
    WEIGHT_RULES = [
        (30, 1.0),      # 近 1 个月：100%
        (90, 0.8),      # 1-3 个月：80%
        (180, 0.5),     # 3-6 个月：50%
        (365, 0.25),    # 6-12 个月：25%
        (1095, 0.1),    # 1-3 年：10%
        (float('inf'), 0.05)  # 3 年以上：5%
    ]

    def __init__(self, target_name: str, text_type: str = "auto"):
        self.target_name = target_name
        self.text_type = text_type  # auto/chat/book/article/diary/social/email/other
        self.content = ""
        self.metadata = {}
        self.now = datetime.now()

    def parse_file(self, file_path: str) -> None:
        """解析文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            self.content = f.read()

        # 自动识别文本类型
        if self.text_type == "auto":
            self.text_type = self._detect_text_type()

        print(f"✓ 文件读取完成")
        print(f"✓ 识别文本类型：{self.text_type}")

        # 根据类型解析
        if self.text_type == "chat":
            self._parse_chat()
        else:
            self._parse_general_text()

    def _detect_text_type(self) -> str:
        """自动识别文本类型"""
        # 检查是否是聊天记录格式
        chat_patterns = [
            r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',  # 微信格式
            r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]',  # QQ格式
        ]
        for pattern in chat_patterns:
            if re.search(pattern, self.content[:1000]):
                return "chat"

        # 检查是否是书籍/文章（有章节结构）
        if re.search(r'(第[一二三四五六七八九十\d]+章|Chapter \d+)', self.content[:2000]):
            return "book"

        # 检查是否是日记（有日期标题）
        if re.search(r'^\d{4}年\d{1,2}月\d{1,2}日', self.content[:500], re.MULTILINE):
            return "diary"

        # 默认为一般文本
        return "other"

    def _parse_chat(self) -> None:
        """解析聊天记录（调用原有的 chat_parser 逻辑）"""
        # 这里可以复用 chat_parser.py 的逻辑
        # 为了简化，这里只做基础统计
        lines = self.content.split('\n')
        self.metadata = {
            "type": "chat",
            "total_lines": len(lines),
            "has_timestamp": True
        }

    def _parse_general_text(self) -> None:
        """解析一般文本"""
        # 统计基础信息
        lines = self.content.split('\n')
        words = self.content.split()
        paragraphs = [p for p in self.content.split('\n\n') if p.strip()]

        self.metadata = {
            "type": self.text_type,
            "total_chars": len(self.content),
            "total_lines": len(lines),
            "total_words": len(words),
            "total_paragraphs": len(paragraphs),
            "has_timestamp": False
        }

    def export_markdown(self, output_path: str) -> None:
        """导出为 Markdown 格式"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# {self.target_name} 的文本资料\n\n")
            f.write(f"## 文本信息\n\n")
            f.write(f"- **文本类型**：{self.text_type}\n")

            if self.text_type == "chat":
                f.write(f"- **总行数**：{self.metadata.get('total_lines', 0)}\n")
            else:
                f.write(f"- **总字数**：{self.metadata.get('total_chars', 0)}\n")
                f.write(f"- **总段落数**：{self.metadata.get('total_paragraphs', 0)}\n")

            f.write(f"\n---\n\n")
            f.write(f"## 原文内容\n\n")
            f.write(self.content)

        print(f"✓ Markdown 导出完成：{output_path}")

    def export_json(self, output_path: str) -> None:
        """导出为 JSON 格式"""
        output = {
            "target_name": self.target_name,
            "text_type": self.text_type,
            "metadata": self.metadata,
            "content": self.content
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"✓ JSON 导出完成：{output_path}")


def main():
    parser = argparse.ArgumentParser(description='通用文本解析器')
    parser.add_argument('--input', required=True, help='输入文件路径')
    parser.add_argument('--target-name', required=True, help='对象名字')
    parser.add_argument('--text-type', default='auto',
                       choices=['auto', 'chat', 'book', 'article', 'diary', 'social', 'email', 'other'],
                       help='文本类型（默认自动识别）')
    parser.add_argument('--output-dir', required=True, help='输出目录')

    args = parser.parse_args()

    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"正在解析：{args.input}")

    # 解析文本
    text_parser = TextParser(args.target_name, args.text_type)
    text_parser.parse_file(args.input)

    # 导出
    text_parser.export_markdown(str(output_dir / f"{args.target_name}_text.md"))
    text_parser.export_json(str(output_dir / f"{args.target_name}_text.json"))

    print("\n" + "="*60)
    print(f"文本解析完成 - {args.target_name}")
    print("="*60)
    print(f"文本类型：{text_parser.text_type}")
    if text_parser.text_type == "chat":
        print(f"总行数：{text_parser.metadata.get('total_lines', 0)}")
    else:
        print(f"总字数：{text_parser.metadata.get('total_chars', 0)}")
        print(f"总段落数：{text_parser.metadata.get('total_paragraphs', 0)}")
    print("="*60)


if __name__ == "__main__":
    main()
