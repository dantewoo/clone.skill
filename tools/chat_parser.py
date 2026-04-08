#!/usr/bin/env python3
"""
聊天记录解析器

支持微信 txt 格式导出，解析后按时间权重分层，输出统一格式供分析使用。

格式示例：
2025-04-11 10:42:15 '玮炜'
哈呀一得苏捏

2025-04-11 10:42:16 '玮炜'
啥意思

用法：
    python3 chat_parser.py --input 私聊_玮炜.txt --target-name "玮炜" --output parsed_output.json
    python3 chat_parser.py --input 私聊_玮炜.txt --target-name "玮炜" --output-dir ./knowledge/weiwei
"""

import re
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict


class Message:
    """单条消息"""
    def __init__(self, timestamp: datetime, sender: str, content: str):
        self.timestamp = timestamp
        self.sender = sender
        self.content = content
        self.weight = 0.0  # 时间权重，稍后计算

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "sender": self.sender,
            "content": self.content,
            "weight": self.weight
        }


class ChatParser:
    """微信聊天记录解析器"""

    # 时间权重规则（天数 -> 权重）
    WEIGHT_RULES = [
        (30, 1.0),      # 近 1 个月：100%
        (90, 0.8),      # 1-3 个月：80%
        (180, 0.5),     # 3-6 个月：50%
        (365, 0.25),    # 6-12 个月：25%
        (1095, 0.1),    # 1-3 年：10%
        (float('inf'), 0.05)  # 3 年以上：5%
    ]

    def __init__(self, target_name: str, user_name: str = "我"):
        self.target_name = target_name  # 要分析的对象
        self.user_name = user_name      # 用户自己的名字
        self.messages: List[Message] = []
        self.now = datetime.now()

    def parse_file(self, file_path: str) -> None:
        """解析微信 txt 文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 正则匹配：时间戳 + 发送者
        # 格式：2025-04-11 10:42:15 '玮炜'
        pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) '([^']+)'\n(.*?)(?=\n\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} '|$)"

        matches = re.finditer(pattern, content, re.DOTALL)

        for match in matches:
            timestamp_str = match.group(1)
            sender = match.group(2)
            message_content = match.group(3).strip()

            # 跳过空消息
            if not message_content:
                continue

            # 解析时间
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

            # 创建消息对象
            msg = Message(timestamp, sender, message_content)
            self.messages.append(msg)

        print(f"✓ 解析完成：共 {len(self.messages)} 条消息")

    def calculate_weights(self) -> None:
        """计算每条消息的时间权重"""
        for msg in self.messages:
            days_ago = (self.now - msg.timestamp).days

            # 根据时间距离分配权重
            for threshold, weight in self.WEIGHT_RULES:
                if days_ago <= threshold:
                    msg.weight = weight
                    break

        print(f"✓ 时间权重计算完成")

    def filter_target_messages(self) -> List[Message]:
        """只保留目标对象发送的消息"""
        target_msgs = [msg for msg in self.messages if msg.sender == self.target_name]
        print(f"✓ 筛选目标对象消息：{len(target_msgs)} 条（来自 {self.target_name}）")
        return target_msgs

    def get_statistics(self) -> Dict:
        """生成统计信息"""
        target_msgs = self.filter_target_messages()

        if not target_msgs:
            return {}

        # 时间跨度
        earliest = min(msg.timestamp for msg in target_msgs)
        latest = max(msg.timestamp for msg in target_msgs)

        # 按权重分层统计
        weight_distribution = defaultdict(int)
        for msg in target_msgs:
            if msg.weight == 1.0:
                weight_distribution["近1个月"] += 1
            elif msg.weight == 0.8:
                weight_distribution["1-3个月"] += 1
            elif msg.weight == 0.5:
                weight_distribution["3-6个月"] += 1
            elif msg.weight == 0.25:
                weight_distribution["6-12个月"] += 1
            elif msg.weight == 0.1:
                weight_distribution["1-3年"] += 1
            else:
                weight_distribution["3年以上"] += 1

        # 消息长度统计
        lengths = [len(msg.content) for msg in target_msgs]
        avg_length = sum(lengths) / len(lengths) if lengths else 0

        # 回复速度统计（简化版：相邻消息时间差）
        reply_times = []
        for i in range(1, len(self.messages)):
            if (self.messages[i].sender == self.target_name and
                self.messages[i-1].sender != self.target_name):
                time_diff = (self.messages[i].timestamp - self.messages[i-1].timestamp).total_seconds()
                if time_diff < 3600:  # 只统计1小时内的回复
                    reply_times.append(time_diff)

        avg_reply_time = sum(reply_times) / len(reply_times) if reply_times else 0

        return {
            "target_name": self.target_name,
            "total_messages": len(target_msgs),
            "time_range": {
                "earliest": earliest.isoformat(),
                "latest": latest.isoformat(),
                "days_span": (latest - earliest).days
            },
            "weight_distribution": dict(weight_distribution),
            "message_stats": {
                "avg_length": round(avg_length, 1),
                "min_length": min(lengths) if lengths else 0,
                "max_length": max(lengths) if lengths else 0
            },
            "reply_stats": {
                "avg_reply_seconds": round(avg_reply_time, 1),
                "reply_samples": len(reply_times)
            }
        }

    def export_json(self, output_path: str) -> None:
        """导出为 JSON 格式"""
        target_msgs = self.filter_target_messages()

        output = {
            "metadata": self.get_statistics(),
            "messages": [msg.to_dict() for msg in target_msgs]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"✓ 导出完成：{output_path}")

    def export_markdown(self, output_path: str) -> None:
        """导出为 Markdown 格式（供 Claude 直接读取）"""
        target_msgs = self.filter_target_messages()
        stats = self.get_statistics()

        lines = [
            f"# {self.target_name} 的聊天记录",
            "",
            "## 统计信息",
            "",
            f"- **消息总数**：{stats['total_messages']} 条",
            f"- **时间跨度**：{stats['time_range']['earliest'][:10]} 至 {stats['time_range']['latest'][:10]}（{stats['time_range']['days_span']} 天）",
            f"- **平均消息长度**：{stats['message_stats']['avg_length']} 字",
            f"- **平均回复速度**：{stats['reply_stats']['avg_reply_seconds']} 秒",
            "",
            "### 时间权重分布",
            ""
        ]

        for period, count in stats['weight_distribution'].items():
            lines.append(f"- {period}：{count} 条")

        lines.extend([
            "",
            "---",
            "",
            "## 聊天记录",
            ""
        ])

        # 按时间分组
        current_date = None
        for msg in target_msgs:
            msg_date = msg.timestamp.date()

            # 日期分隔
            if msg_date != current_date:
                lines.append(f"### {msg_date}")
                lines.append("")
                current_date = msg_date

            # 消息内容（标注权重）
            weight_label = f"[权重 {int(msg.weight * 100)}%]"
            time_str = msg.timestamp.strftime("%H:%M:%S")
            lines.append(f"**{time_str}** {weight_label}")
            lines.append(f"> {msg.content}")
            lines.append("")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print(f"✓ Markdown 导出完成：{output_path}")

    def print_summary(self) -> None:
        """打印摘要信息"""
        stats = self.get_statistics()

        print("\n" + "="*60)
        print(f"聊天记录分析摘要 - {self.target_name}")
        print("="*60)
        print(f"消息总数：{stats['total_messages']} 条")
        print(f"时间跨度：{stats['time_range']['days_span']} 天")
        print(f"平均消息长度：{stats['message_stats']['avg_length']} 字")
        print(f"平均回复速度：{stats['reply_stats']['avg_reply_seconds']} 秒")
        print("\n时间权重分布：")
        for period, count in stats['weight_distribution'].items():
            print(f"  {period}：{count} 条")
        print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="微信聊天记录解析器")
    parser.add_argument("--input", required=True, help="输入文件路径（微信 txt 格式）")
    parser.add_argument("--target-name", required=True, help="要分析的对象名字")
    parser.add_argument("--user-name", default="我", help="用户自己的名字（默认：我）")
    parser.add_argument("--output", help="输出 JSON 文件路径")
    parser.add_argument("--output-md", help="输出 Markdown 文件路径")
    parser.add_argument("--output-dir", help="输出目录（自动生成文件名）")

    args = parser.parse_args()

    # 初始化解析器
    chat_parser = ChatParser(target_name=args.target_name, user_name=args.user_name)

    # 解析文件
    print(f"正在解析：{args.input}")
    chat_parser.parse_file(args.input)

    # 计算权重
    chat_parser.calculate_weights()

    # 打印摘要
    chat_parser.print_summary()

    # 导出
    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        json_path = output_dir / f"{args.target_name}_parsed.json"
        md_path = output_dir / f"{args.target_name}_chat.md"

        chat_parser.export_json(str(json_path))
        chat_parser.export_markdown(str(md_path))

    if args.output:
        chat_parser.export_json(args.output)

    if args.output_md:
        chat_parser.export_markdown(args.output_md)


if __name__ == "__main__":
    main()
