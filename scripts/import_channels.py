"""Import channel usernames from a text file into the database.

Usage:
    python scripts/import_channels.py --file /path/to/README.md

The script scans the given file for Telegram channel links or @usernames,
deduplicates them, and inserts each into the `channels` table if it does not
already exist. The original text line is used to推测分类，并记录来源。
"""

from __future__ import annotations

import argparse
import asyncio
import os
import re
from typing import Dict, Set

from database import db
from extractor import extractor


CHANNEL_PATTERN = re.compile(r"(?:https?://)?t\.me/([a-zA-Z0-9_]{5,32})")
AT_PATTERN = re.compile(r"@([a-zA-Z0-9_]{5,32})")


async def insert_channels(channels: Dict[str, str], source: str, dry_run: bool) -> None:
    added = 0
    skipped = 0

    for username, context in sorted(channels.items()):
        username = username.lower()

        existing = await db.get_channel_by_username(username)
        if existing:
            print(f"⏭️ 频道已存在，跳过: @{username}")
            skipped += 1
            continue

        category = extractor.categorize_channel(context or "") or "uncategorized"

        if dry_run:
            print(f"[DRY-RUN] 将插入频道: @{username} (分类: {category})")
            added += 1
            continue

        await db.add_channel(
            username=username,
            title=None,
            channel_id=None,
            discovered_from=source,
            category=category
        )
        added += 1
        print(f"✅ 已插入频道: @{username} (分类: {category})")

    print("""
======== 汇总 ========
新增频道: {added}
已存在: {skipped}
=====================
""".format(added=added, skipped=skipped))


def extract_channels_from_text(text: str) -> Dict[str, str]:
    channels: Dict[str, str] = {}

    for line in text.splitlines():
        matches: Set[str] = set()
        matches.update(CHANNEL_PATTERN.findall(line))
        matches.update(AT_PATTERN.findall(line))

        for username in matches:
            username = username.lower()
            channels.setdefault(username, line.strip())

    return channels


async def main() -> None:
    parser = argparse.ArgumentParser(description="从文本文件导入频道用户名")
    parser.add_argument(
        "--file",
        default="uploaddata.md",
        help="包含频道信息的文本文件路径 (默认: uploaddata.md)"
    )
    parser.add_argument("--dry-run", action="store_true", help="仅显示结果，不写入数据库")
    args = parser.parse_args()

    file_path = os.path.expanduser(args.file)
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"找不到文件: {file_path}")

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    channels = extract_channels_from_text(content)
    if not channels:
        print("⚠️ 在文件中没有找到任何频道链接或 @username")
        return

    print(f"📄 文件: {file_path}")
    print(f"🔍 共发现 {len(channels)} 个唯一频道用户名")

    source = f"import:{os.path.basename(file_path)}"
    await insert_channels(channels, source, args.dry_run)


if __name__ == "__main__":
    asyncio.run(main())

