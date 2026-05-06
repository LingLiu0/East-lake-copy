#!/usr/bin/env python3
"""
Obsidian AI 工作流 - 统一入口（精简版）

一个脚本搞定所有功能：
- 成果导入 (文件/网页)
- AI 对话/问答
- 知识管理/演化
- 系统诊断

使用: python obsidian.py <command> [args]
"""
import argparse
import json
import os
import re
import subprocess
import sys
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

VERSION = "2.0"

# ============================================================
# 核心配置
# ============================================================

VAULT = Path(os.getcwd())
INBOX = VAULT / "_inbox"
ARCHIVE = VAULT / "_archive"
ACHIEVEMENTS = VAULT / "achievements"

# 创建必要目录
for d in [INBOX, ARCHIVE, ACHIEVEMENTS]:
    d.mkdir(parents=True, exist_ok=True)


# ============================================================
# 工具函数
# ============================================================

def compute_hash(content: bytes) -> str:
    return hashlib.md5(content).hexdigest()[:12]


def run_py(script: str, args: list = None):
    """运行 Python 脚本"""
    cmd = [sys.executable, str(VAULT / "scripts" / script)]
    if args:
        cmd.extend(args)
    return subprocess.run(cmd, cwd=str(VAULT)).returncode


def print_header(title: str):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}\n")


def print_status(items: list, empty_msg: str = "无"):
    if not items:
        print(f"  {empty_msg}")
        return
    for i, item in enumerate(items, 1):
        print(f"  {i}. {item}")


# ============================================================
# 成果管理
# ============================================================

def cmd_achieve(args):
    """成果管理命令"""
    if args.action == "in" or args.action == "inbox":
        # 查看投递箱
        print_header("📥 投递箱状态")

        # 文件
        files = [f for f in INBOX.rglob("*") if f.is_file() and not f.name.startswith('.')]
        print(f"\n  待处理文件: {len(files)}")
        for f in files[:5]:
            print(f"    - {f.name}")
        if len(files) > 5:
            print(f"    ... 还有 {len(files)-5} 个")

        # 网页
        web_inbox = INBOX / "web"
        if web_inbox.exists():
            web_files = list(web_inbox.glob("*.json"))
            print(f"\n  待处理网页: {len(web_files)}")
            for f in web_files[:3]:
                data = json.loads(f.read_text())
                print(f"    - {data.get('title', 'untitled')[:40]}")
            if len(web_files) > 3:
                print(f"    ... 还有 {len(web_files)-3} 个")

        print("\n  处理命令: obsidian.py achieve process")

    elif args.action == "process" or args.action == "run":
        # 处理投递箱
        print_header("🔄 处理投递箱")

        # 处理文件
        files = [f for f in INBOX.rglob("*") if f.is_file() and not f.name.startswith('.')]
        processed = 0

        for f in files:
            result = process_file(f)
            if result["success"]:
                processed += 1
                print(f"  ✅ {result['title']}")

        print(f"\n  处理完成: {processed}/{len(files)} 个文件")

        # 处理网页
        web_inbox = INBOX / "web"
        if web_inbox.exists():
            web_files = list(web_inbox.glob("*.json"))
            print(f"\n  网页收集: {len(web_files)} 个待处理")
            print("  运行: obsidian.py web process")

    elif args.action == "status":
        # 状态
        files = [f for f in INBOX.rglob("*") if f.is_file() and not f.name.startswith('.')]
        achievements = list(ACHIEVEMENTS.rglob("*.md")) if ACHIEVEMENTS.exists() else []

        print_header("📊 系统状态")
        print(f"  投递箱: {len(files)} 个文件")
        print(f"  成果库: {len(achievements)} 篇笔记")

        # 最近处理
        state_file = VAULT / ".obsidian" / "achievement-state.json"
        if state_file.exists():
            state = json.loads(state_file.read_text())
            count = len(state.get("processed", {}))
            print(f"  已处理: {count} 篇")


def process_file(file_path: Path) -> dict:
    """处理单个文件"""
    try:
        # 提取元数据
        title = file_path.stem.replace('-', ' ').replace('_', ' ').title()[:60]
        date = datetime.now().strftime('%Y-%m-%d')

        # 检测分类
        category = detect_category(file_path)

        # 创建笔记
        content = f"""---
title: {title}
tags: [{datetime.now().strftime('%Y-%m')}]
created: {date}
updated: {date}
source: {file_path.name}
category: achievements/{category}
status: processed
---

# {title}

> [!info] 成果信息
> - 来源: {file_path.name}
> - 处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 附件

📎 [{file_path.name}](.attachments/{file_name})

---

## 后续操作

- [ ] 补充内容
- [ ] 添加链接
- [ ] 分享团队
"""

        # 保存笔记
        target_dir = ACHIEVEMENTS / category
        target_dir.mkdir(parents=True, exist_ok=True)

        target_file = target_dir / f"{date}-{file_path.stem[:40]}.md"
        target_file.write_text(content, encoding='utf-8')

        # 保存附件
        attach_dir = target_dir / ".attachments"
        attach_dir.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copy2(file_path, attach_dir / file_path.name)

        # 归档原文件
        archive_dir = ARCHIVE
        archive_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(file_path), str(archive_dir / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{file_path.name}"))

        return {"success": True, "title": title, "category": category}

    except Exception as e:
        return {"success": False, "error": str(e)}


def detect_category(file_path: Path) -> str:
    """检测分类"""
    name = file_path.name.lower()
    rules = {
        "weekly": ["周报", "weekly", "总结"],
        "research": ["研究", "research", "报告", "分析"],
        "design": ["设计", "design", "ui", "ux"],
        "code": ["代码", "code", "实现"],
    }
    for cat, keywords in rules.items():
        if any(k in name for k in keywords):
            return cat
    return "misc"


# ============================================================
# 网页收集
# ============================================================

def cmd_web(args):
    """网页收集命令"""
    if args.action == "add":
        # 添加网页
        if not args.url:
            print("错误: 请提供 URL")
            return

        url = args.url
        title = args.title or extract_title(url) or url.split('/')[-1][:50]

        web_inbox = INBOX / "web"
        web_inbox.mkdir(parents=True, exist_ok=True)

        task = {
            "url": url,
            "title": title,
            "tags": args.tags.split(',') if args.tags else [],
            "added_at": datetime.now().isoformat(),
        }

        url_hash = compute_hash(url.encode())
        (web_inbox / f"{url_hash}.json").write_text(json.dumps(task, indent=2))

        print(f"  ✅ 已添加: {title}")
        print("  运行: obsidian.py web process")

    elif args.action == "process":
        # 处理网页
        print_header("🌐 处理网页")

        web_inbox = INBOX / "web"
        if not web_inbox.exists():
            print("  收集箱为空")
            return

        processed = 0
        for task_file in web_inbox.glob("*.json"):
            task = json.loads(task_file.read_text())
            result = collect_web(task["url"], task.get("title"))
            if result["success"]:
                processed += 1
                task_file.unlink()  # 删除任务
                print(f"  ✅ {result['title']}")

        print(f"\n  完成: {processed} 个网页")

    else:
        # 查看
        print_header("🌐 网页收集箱")
        web_inbox = INBOX / "web"
        if not web_inbox.exists():
            print("  收集箱为空")
            return

        files = list(web_inbox.glob("*.json"))
        print(f"  待处理: {len(files)} 个")
        for f in files[:5]:
            data = json.loads(f.read_text())
            print(f"    - {data.get('title', 'untitled')[:40]}")


def extract_title(url: str) -> Optional[str]:
    """快速获取标题"""
    try:
        import requests
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        soup = __import__('bs4').BeautifulSoup(resp.text, 'html.parser')
        return soup.title.string.strip()[:60] if soup.title else None
    except:
        return None


def collect_web(url: str, title: str = None) -> dict:
    """收集网页"""
    try:
        import requests
        from bs4 import BeautifulSoup

        resp = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, 'html.parser')

        # 获取标题
        if not title:
            title = soup.title.string.strip()[:60] if soup.title else url

        # 提取内容
        for tag in soup(['script', 'style', 'nav', 'footer']):
            tag.decompose()

        content = soup.get_text(separator='\n', strip=True)
        lines = [l for l in content.split('\n') if len(l) > 20]
        content = '\n\n'.join(lines[:15])[:2000]

        # 保存笔记
        date = datetime.now().strftime('%Y-%m-%d')
        target = ACHIEVEMENTS / "research"
        target.mkdir(parents=True, exist_ok=True)

        safe_title = re.sub(r'[^\w\s-]', '', title).replace(' ', '-')[:40]
        md_file = target / f"{date}-{safe_title}.md"

        note = f"""---
title: {title}
tags: [web-collector, {datetime.now().strftime('%Y-%m')}]
created: {date}
source: {url}
category: achievements/research
status: collected
---

# {title}

> [!info] 网页剪藏
> - 来源: {url}
> - 日期: {date}

## 原文链接

[{title}]({url})

## 内容摘要

{content}

---

## 后续操作

- [ ] 阅读完整内容
- [ ] 提取要点
- [ ] 添加思考
"""

        md_file.write_text(note, encoding='utf-8')
        return {"success": True, "title": title}

    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# 知识管理
# ============================================================

def cmd_ai(args):
    """AI 命令"""
    if args.action == "ask":
        if not args.query:
            print("错误: 请提供问题")
            return
        run_py("obsidian_chat.py", [args.query])

    elif args.action == "chat":
        run_py("obsidian_chat.py", ["--interactive"])

    elif args.action == "stats":
        run_py("obsidian_qa.py", ["--summary"])

    elif args.action == "gaps":
        run_py("obsidian_qa.py", ["--gaps"])

    elif args.action == "evolve":
        run_py("auto_evolve.py", ["--once"])


# ============================================================
# 系统命令
# ============================================================

def cmd_system(args):
    """系统命令"""
    if args.action == "status":
        print_header("📊 系统状态")

        # 文件统计
        files = [f for f in INBOX.rglob("*") if f.is_file()]
        web_files = list((INBOX / "web").glob("*.json")) if (INBOX / "web").exists() else []
        md_files = list(ACHIEVEMENTS.rglob("*.md")) if ACHIEVEMENTS.exists() else []

        print(f"  投递箱: {len(files)} 个文件")
        print(f"  网页收集: {len(web_files)} 个")
        print(f"  成果笔记: {len(md_files)} 篇")

    elif args.action == "diagnose":
        run_py("diagnose.py")

    elif args.action == "install":
        print("📦 安装依赖...")
        packages = ["requests", "beautifulsoup4", "anthropic", "PyPDF2", "python-docx"]
        for p in packages:
            subprocess.run([sys.executable, "-m", "pip", "install", p, "-q"], capture_output=True)
        print("  ✅ 完成")


# ============================================================
# 主程序
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description=f"Obsidian AI 工作流 v{VERSION} - 统一入口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
命令:

  成果管理:
    achieve in          查看投递箱
    achieve process     处理文件
    achieve status      状态

  网页收集:
    web add <URL>       添加网页
    web process         处理网页
    web                 查看收集箱

  AI 对话:
    ask <问题>          提问
    chat                交互对话

  知识管理:
    ai stats            统计
    ai gaps             知识缺口
    ai evolve           演化

  系统:
    status              系统状态
    install             安装依赖

示例:
  python obsidian.py achieve process
  python obsidian.py web add "https://..."
  python obsidian.py ask "什么是RAG?"
  python obsidian.py ai stats
        """
    )

    parser.add_argument("command", nargs="?", help="主命令")
    parser.add_argument("action", nargs="?", help="子命令")
    parser.add_argument("args", nargs="?", help="参数")
    parser.add_argument("--tags", "-t", help="标签")
    parser.add_argument("--title", help="标题")

    args = parser.parse_args()

    # 无参数显示帮助
    if not args.command:
        parser.print_help()
        print(f"\n版本: {VERSION}")
        return

    # 路由命令
    if args.command == "achieve" or args.command == "a":
        cmd_achieve(args)

    elif args.command == "web" or args.command == "w":
        cmd_web(args)

    elif args.command == "ask":
        cmd_ai(argparse.Namespace(action="ask", query=args.action or args.args))

    elif args.command == "chat":
        cmd_ai(argparse.Namespace(action="chat"))

    elif args.command == "ai":
        cmd_ai(argparse.Namespace(action=args.action or "stats"))

    elif args.command == "status":
        cmd_system(argparse.Namespace(action="status"))

    elif args.command == "install":
        cmd_system(argparse.Namespace(action="install"))

    elif args.command == "diagnose":
        cmd_system(argparse.Namespace(action="diagnose"))

    else:
        print(f"未知命令: {args.command}")
        print("运行 python obsidian.py 查看帮助")


if __name__ == "__main__":
    main()