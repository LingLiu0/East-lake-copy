#!/usr/bin/env python3
"""
Obsidian 成果管理器后台自动处理器

功能：
- 监听文件系统变化，自动处理新文件
- 支持 macOS/Linux/Windows
- 可配置为开机自启

安装方法：
    # macOS
    brew services start python@3.11
    launchctl plutil -w ~/Library/LaunchAgents/com.obsidian.achievement.plist

    # Linux (systemd)
    sudo cp achievement-daemon.service /etc/systemd/system/
    sudo systemctl enable achievement-daemon.service
    sudo systemctl start achievement-daemon.service
"""
import argparse
import os
import sys
import time
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import watchdog
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False


class AchievementAutoProcessor:
    """后台自动处理器"""

    def __init__(self, vault_path: str = None):
        self.vault_path = Path(vault_path or os.getcwd())
        self.inbox = self.vault_path / "_inbox"
        self.processed_marker = self.vault_path / ".obsidian" / "processed.json"

        self._load_processed()

    def _load_processed(self):
        """加载已处理文件列表"""
        if self.processed_marker.exists():
            try:
                self.processed = json.loads(self.processed_marker.read_text())
            except:
                self.processed = {}
        else:
            self.processed = {}

    def _save_processed(self):
        """保存已处理文件列表"""
        self.processed_marker.parent.mkdir(parents=True, exist_ok=True)
        self.processed_marker.write_text(json.dumps(self.processed, indent=2))

    def _get_hash(self, file_path: Path) -> str:
        """计算文件哈希"""
        hasher = hashlib.md5()
        hasher.update(file_path.read_bytes())
        return hasher.hexdigest()

    def is_processed(self, file_path: Path) -> bool:
        """检查文件是否已处理"""
        file_hash = self._get_hash(file_path)
        return file_hash in self.processed

    def mark_processed(self, file_path: Path):
        """标记文件已处理"""
        file_hash = self._get_hash(file_path)
        self.processed[file_hash] = {
            "name": file_path.name,
            "size": file_path.stat().st_size,
            "at": datetime.now().isoformat()
        }
        self._save_processed()

    def process_single(self, file_path: Path) -> bool:
        """处理单个文件"""
        if not file_path.exists() or file_path.is_dir():
            return False

        # 检查扩展名
        allowed_ext = ['.pdf', '.docx', '.doc', '.md', '.txt', '.png', '.jpg', '.jpeg', '.gif']
        if file_path.suffix.lower() not in allowed_ext:
            return False

        # 跳过隐藏文件
        if file_path.name.startswith('.'):
            return False

        # 检查是否已处理
        if self.is_processed(file_path):
            print(f"⏭️  跳过（已处理）: {file_path.name}")
            return True

        print(f"\n📥 处理: {file_path.name}")

        try:
            # 提取元数据
            metadata = self._extract_metadata(file_path)

            # 生成笔记内容
            content = self._generate_note(file_path, metadata)

            # 确定目标位置
            category = self._detect_category(file_path)
            target_dir = self.vault_path / "achievements" / category
            target_dir.mkdir(parents=True, exist_ok=True)

            target_file = target_dir / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{file_path.stem}.md"
            target_file.write_text(content, encoding='utf-8')

            # 复制原文件到附件
            attach_dir = target_dir / ".attachments"
            attach_dir.mkdir(parents=True, exist_ok=True)
            attach_file = attach_dir / file_path.name
            if not attach_file.exists():
                import shutil
                shutil.copy2(file_path, attach_file)

            # 标记已处理
            self.mark_processed(file_path)

            print(f"   ✅ 已创建: {target_file.relative_to(self.vault_path)}")

            # 尝试移动原文件到归档
            archive_dir = self.vault_path / "_archive"
            archive_dir.mkdir(parents=True, exist_ok=True)
            import shutil
            archive_file = archive_dir / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{file_path.name}"
            shutil.move(str(file_path), str(archive_file))

            return True

        except Exception as e:
            print(f"   ❌ 错误: {e}")
            return False

    def _detect_category(self, file_path: Path) -> str:
        """检测分类"""
        name_lower = file_path.name.lower()

        if any(k in name_lower for k in ['周报', 'weekly', '总结']):
            return "weekly"
        elif any(k in name_lower for k in ['研究', 'research', '报告', '分析']):
            return "research"
        elif any(k in name_lower for k in ['设计', 'design', 'ui', 'ux']):
            return "design"
        elif any(k in name_lower for k in ['代码', 'code', '实现']):
            return "code"
        else:
            return "documents"

    def _extract_metadata(self, file_path: Path) -> dict:
        """提取元数据"""
        stem = file_path.stem

        # 清理标题
        title = stem
        title = title.replace('-', ' ').replace('_', ' ')
        title = ' '.join(word.capitalize() for word in title.split())

        return {
            "title": title[:80],
            "date": datetime.now().strftime('%Y-%m-%d'),
            "author": "团队成员",
            "source": file_path.name,
            "tags": [datetime.now().strftime('%Y-%m')],
        }

    def _generate_note(self, file_path: Path, metadata: dict) -> str:
        """生成笔记内容"""
        content = f"""---
title: {metadata['title']}
tags: [{', '.join(metadata['tags'])}]
created: {metadata['date']}
updated: {metadata['date']}
author: {metadata['author']}
source: {metadata['source']}
category: achievements/{self._detect_category(file_path)}
status: auto-processed
---

# {metadata['title']}

> [!info] 自动生成的成果笔记
> - 来源文件: {metadata['source']}
> - 处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> - 请补充更多详细信息

## 附件

📎 [{file_path.name}](.attachments/{file_path.name})

---

## 📝 后续操作

- [ ] 补充内容详情
- [ ] 添加相关概念链接
- [ ] 分享给团队
"""

        return content

    def scan_inbox(self):
        """扫描投递箱并处理所有文件"""
        if not self.inbox.exists():
            print(f"📭 投递箱不存在: {self.inbox}")
            return 0

        processed = 0

        for file_path in self.inbox.rglob("*"):
            if file_path.is_file():
                if self.process_single(file_path):
                    processed += 1

        return processed


class FileChangeHandler(FileSystemEventHandler):
    """文件变化处理器"""

    def __init__(self, processor: AchievementAutoProcessor):
        self.processor = processor

    def on_created(self, event):
        """文件创建事件"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # 等待文件写入完成
        time.sleep(1)

        # 检查是否是投递箱中的文件
        if "achievements" in str(file_path):
            return

        print(f"\n🔔 检测到新文件: {file_path.name}")

        # 处理文件
        self.processor.process_single(file_path)


def run_daemon(vault_path: str, interval: int = 60):
    """后台运行"""
    processor = AchievementAutoProcessor(vault_path)

    print("=" * 50)
    print("🚀 Obsidian 成果自动处理器")
    print("=" * 50)
    print(f"📂 Vault: {vault_path}")
    print(f"📥 投递箱: {processor.inbox}")
    print(f"⏱️  完整扫描间隔: {interval}秒")
    print("🛑 按 Ctrl+C 停止")
    print("=" * 50)

    # 先处理一次
    print("\n📋 初始扫描...")
    count = processor.scan_inbox()
    print(f"✅ 处理了 {count} 个文件\n")

    if not HAS_WATCHDOG:
        print("⚠️  未安装 watchdog，使用定时扫描模式\n")
        try:
            while True:
                time.sleep(interval)
                count = processor.scan_inbox()
                if count > 0:
                    print(f"\n📥 自动处理了 {count} 个文件")
        except KeyboardInterrupt:
            print("\n👋 停止")
        return

    # 使用 watchdog 监听
    observer = Observer()
    event_handler = FileChangeHandler(processor)

    # 监听整个 vault，但排除一些目录
    observer.schedule(event_handler, vault_path, recursive=True)
    observer.start()

    print("👀 监听中...\n")

    try:
        # 定时完整扫描（作为备份）
        while True:
            time.sleep(interval)
            count = processor.scan_inbox()
            if count > 0:
                print(f"\n📥 定时扫描处理了 {count} 个文件")

    except KeyboardInterrupt:
        observer.stop()
        print("\n\n👋 已停止")


def main():
    parser = argparse.ArgumentParser(description="Obsidian 成果自动处理器")
    parser.add_argument("--path", "-p", default=".", help="Obsidian 路径")
    parser.add_argument("--once", "-o", action="store_true", help="只运行一次")
    parser.add_argument("--interval", "-i", type=int, default=60, help="扫描间隔（秒）")

    args = parser.parse_args()

    vault_path = str(Path(args.path).resolve())

    if args.once:
        # 只运行一次
        processor = AchievementAutoProcessor(vault_path)
        count = processor.scan_inbox()
        print(f"\n✅ 处理完成: {count} 个文件")
    else:
        # 后台运行
        run_daemon(vault_path, args.interval)


if __name__ == "__main__":
    main()