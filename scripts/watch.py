#!/usr/bin/env python3
"""
文件监控脚本 - 监听 raw/ 目录，自动触发编译

使用方法：
    python3 scripts/watch.py              # 一次性检查（适合手动运行）
    python3 scripts/watch.py --continuous # 持续监听（适合本地开发）
"""

import argparse
import hashlib
import os
import sys
import time
import json
import subprocess
from datetime import datetime
from pathlib import Path

# 配置
VAULT = Path(os.getcwd())
RAW = VAULT / "raw"
STATE_FILE = VAULT / ".claude" / "watch_state.json"


def load_state() -> dict:
    """加载上次状态"""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except:
            pass
    return {"files": {}, "last_compile": None}


def save_state(state: dict):
    """保存状态"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def compute_file_hash(file_path: Path) -> str:
    """计算文件哈希"""
    return hashlib.md5(file_path.read_bytes()).hexdigest()


def get_all_raw_files() -> dict:
    """获取所有 raw 文件及其哈希"""
    files = {}
    for ext in ['.md', '.txt', '.pdf', '.docx', '.ppt', '.pptx', '.html', '.htm']:
        for f in RAW.rglob(f"*{ext}"):
            if f.is_file():
                files[str(f.relative_to(VAULT))] = compute_file_hash(f)
    return files


def check_new_files() -> list[Path]:
    """检查是否有新文件或修改的文件"""
    state = load_state()
    current_files = get_all_raw_files()
    new_or_modified = []

    # 检查新增或修改的文件
    for file_path, file_hash in current_files.items():
        if file_path not in state["files"] or state["files"][file_path] != file_hash:
            full_path = VAULT / file_path
            new_or_modified.append(full_path)
            print(f"📄 检测到新/修改文件: {file_path}")

    return new_or_modified


def trigger_compile(new_files: list[Path]):
    """触发编译"""
    print("\n🚀 开始编译知识库...")
    print(f"📥 新文件数量: {len(new_files)}")

    # 运行编译
    result = subprocess.run(
        [sys.executable, "scripts/obsidian.py", "ai", "compile"],
        cwd=VAULT,
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("✅ 编译成功")
        # 更新状态
        state = load_state()
        state["files"] = get_all_raw_files()
        state["last_compile"] = datetime.now().isoformat()
        save_state(state)

        # 更新索引
        subprocess.run(
            [sys.executable, "scripts/obsidian.py", "ai", "index"],
            cwd=VAULT,
            capture_output=True,
            text=True
        )
    else:
        print(f"❌ 编译失败: {result.stderr}")


def run_once():
    """一次性检查"""
    new_files = check_new_files()
    if new_files:
        trigger_compile(new_files)
    else:
        print("✅ 没有新文件需要编译")


def run_continuous(interval: int = 10):
    """持续监听模式"""
    print(f"🔍 持续监听 raw/ 目录，间隔 {interval} 秒...")
    print("按 Ctrl+C 退出\n")

    try:
        while True:
            new_files = check_new_files()
            if new_files:
                trigger_compile(new_files)
                print()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n👋 监听已停止")


def main():
    parser = argparse.ArgumentParser(description="监听 raw/ 目录，自动编译知识库")
    parser.add_argument("--once", action="store_true", help="一次性检查（默认）")
    parser.add_argument("--continuous", action="store_true", help="持续监听模式")
    parser.add_argument("--interval", type=int, default=10, help="监听间隔（秒）")

    args = parser.parse_args()

    # 默认行为：一次性检查
    if args.continuous:
        run_continuous(args.interval)
    else:
        run_once()


if __name__ == "__main__":
    main()