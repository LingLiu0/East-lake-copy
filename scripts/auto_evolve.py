#!/usr/bin/env python3
"""
Obsidian 知识库自动演化脚本
在后台运行，监听文件变化，自动执行知识库演化任务

使用方法:
    python auto_evolve.py --daemon      # 后台守护进程模式
    python auto_evolve.py --watch       # 监听模式
    python auto_evolve.py --on-change   # 文件变化时触发
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# 简单的文件监听（跨平台）
try:
    import watchdog
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False
    print("注意: 安装 watchdog 以启用文件监听功能: pip install watchdog")


class KnowledgeEvolver:
    """知识库自动演化器"""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.state_file = self.vault_path / ".obsidian" / "evolve_state.json"
        self.state = self._load_state()

    def _load_state(self) -> dict:
        """加载状态"""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except:
                pass
        return {
            "last_hash": "",
            "last_evolution": None,
            "evolution_count": 0,
        }

    def _save_state(self):
        """保存状态"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self.state, indent=2))

    def _compute_hash(self) -> str:
        """计算知识库内容哈希"""
        hasher = hashlib.md5()

        for md_file in self.vault_path.rglob("*.md"):
            if ".git" in str(md_file) or ".obsidian" in str(md_file):
                continue
            content = md_file.read_text(encoding='utf-8', errors='ignore')
            hasher.update(content.encode())

        return hasher.hexdigest()

    def analyze_and_evolve(self, force: bool = False) -> dict:
        """分析并演化知识库"""
        current_hash = self._compute_hash()

        # 检查是否有变化
        if not force and current_hash == self.state["last_hash"]:
            return {"status": "no_change", "message": "知识库无变化"}

        print(f"\n🔄 检测到知识库变化，开始分析...")

        # 执行分析
        analysis = self._analyze_knowledge_base()

        # 执行演化
        evolutions = self._execute_evolution(analysis)

        # 更新状态
        self.state["last_hash"] = current_hash
        self.state["last_evolution"] = datetime.now().isoformat()
        self.state["evolution_count"] += 1
        self._save_state()

        return {
            "status": "evolved",
            "analysis": analysis,
            "evolutions": evolutions,
            "timestamp": datetime.now().isoformat(),
        }

    def _analyze_knowledge_base(self) -> dict:
        """分析知识库结构"""
        analysis = {
            "total_docs": 0,
            "total_links": 0,
            "concepts": [],
            "orphans": [],
            "broken_links": [],
            "link_suggestions": [],
            "tag_clusters": {},
        }

        all_files = {}
        all_links = set()

        # 收集所有文件
        for md_file in self.vault_path.rglob("*.md"):
            if ".git" in str(md_file) or ".obsidian" in str(md_file):
                continue

            stem = md_file.stem
            content = md_file.read_text(encoding='utf-8', errors='ignore')

            all_files[stem] = {
                "path": str(md_file.relative_to(self.vault_path)),
                "content": content,
                "tags": self._extract_tags(content),
            }

            analysis["total_docs"] += 1

        # 收集所有链接
        for stem, data in all_files.items():
            links = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', data["content"])
            for link in links:
                all_links.add((stem, link))

                # 检查断开的链接
                if link not in all_files:
                    analysis["broken_links"].append({
                        "from": stem,
                        "to": link,
                    })

            # 记录标签聚类
            for tag in data["tags"]:
                if tag not in analysis["tag_clusters"]:
                    analysis["tag_clusters"][tag] = []
                analysis["tag_clusters"][tag].append(stem)

        analysis["total_links"] = len(all_links)

        # 找出孤立文档（concepts 和 decisions 目录中没有被链接的）
        linked_stems = {s for s, t in all_links} | {t for s, t in all_links}

        for stem, data in all_files.items():
            path = data["path"]
            if "/concepts/" in path or "/decisions/" in path:
                if stem not in linked_stems:
                    analysis["orphans"].append(stem)

        # 生成链接建议
        # 基于标签相似性
        for tag, stems in analysis["tag_clusters"].items():
            if len(stems) >= 2:
                analysis["link_suggestions"].append({
                    "type": "tag_cluster",
                    "tag": tag,
                    "documents": stems,
                })

        return analysis

    def _extract_tags(self, content: str) -> list[str]:
        """提取标签"""
        match = re.search(r'^tags:\s*\[([^\]]+)\]', content, re.MULTILINE)
        if match:
            tags_str = match.group(1)
            return [t.strip().strip('"\' ') for t in tags_str.split(',')]
        return []

    def _execute_evolution(self, analysis: dict) -> list[dict]:
        """执行知识库演化"""
        evolutions = []

        # 1. 更新索引文件
        index_evolve = self._evolve_index(analysis)
        if index_evolve:
            evolutions.append(index_evolve)

        # 2. 创建缺失的反向链接
        backlink_evolve = self._evolve_backlinks(analysis)
        if backlink_evolve:
            evolutions.append(backlink_evolve)

        # 3. 建议新文档
        new_doc_evolve = self._suggest_new_documents(analysis)
        if new_doc_evolve:
            evolutions.append(new_doc_evolve)

        return evolutions

    def _evolve_index(self, analysis: dict) -> dict:
        """演化索引文件"""
        # 更新 concept/index.md
        index_path = self.vault_path / "concepts" / "index.md"

        if not index_path.exists():
            return {"type": "skip", "reason": "索引文件不存在"}

        # 获取所有概念
        concepts = [s for s, d in analysis.items() if "/concepts/" in d.get("path", "")]

        content = f"""---
title: 概念索引
tags: [index, concepts]
updated: {datetime.now().strftime('%Y-%m-%d')}
---

# 概念索引

> 由自动演化系统生成

共 {len(concepts)} 个概念。

## 全部概念

"""
        for stem, data in analysis.items():
            if "/concepts/" in data.get("path", ""):
                title = stem.replace("-", " ").title()
                content += f"- [[{stem}|{title}]]\n"

        index_path.write_text(content, encoding='utf-8')

        return {"type": "index_updated", "documents": ["concepts/index.md"]}

    def _evolve_backlinks(self, analysis: dict) -> dict:
        """添加反向链接"""
        # 在每个文档末尾添加"相关链接"部分
        updated = []

        all_files = {}
        all_links = set()

        # 重新收集
        for md_file in self.vault_path.rglob("*.md"):
            if ".git" in str(md_file) or ".obsidian" in str(md_file):
                continue
            stem = md_file.stem
            all_files[stem] = md_file

            content = md_file.read_text(encoding='utf-8', errors='ignore')
            links = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', content)
            for link in links:
                all_links.add((stem, link))

        # 为每个文档添加反向链接
        for stem, md_file in all_files.items():
            # 找出引用此文档的文档
            backlinks = [s for s, t in all_links if t == stem]

            if not backlinks:
                continue

            content = md_file.read_text(encoding='utf-8', errors='ignore')

            # 检查是否已有反向链接部分
            if "## 相关链接" not in content and len(backlinks) > 0:
                backlinks_md = "\n".join(f"- [[{s}]]" for s in backlinks[:5])
                new_content = content + f"""

## 相关链接

{backlinks_md}

---
*自动演化: 添加反向链接*
"""

                md_file.write_text(new_content, encoding='utf-8')
                updated.append(str(md_file.relative_to(self.vault_path)))

        return {"type": "backlinks_added", "documents": updated} if updated else {"type": "skip", "reason": "无需更新"}

    def _suggest_new_documents(self, analysis: dict) -> dict:
        """建议新文档"""
        suggestions = []

        # 检查高引用但不存在的概念
        link_counts = {}
        for from_stem, to_stem in analysis.get("broken_links", []):
            link_counts[to_stem] = link_counts.get(to_stem, 0) + 1

        for target, count in link_counts.items():
            if count >= 2:
                suggestions.append({
                    "type": "create_concept",
                    "name": target,
                    "reason": f"被 {count} 个文档引用但不存在",
                })

        if suggestions:
            # 创建建议文件
            suggest_path = self.vault_path / "docs" / "evolution-suggestions.md"
            suggest_path.parent.mkdir(parents=True, exist_ok=True)

            content = f"""---
title: 知识库演化建议
tags: [evolution, suggestion]
generated: {datetime.now().strftime('%Y-%m-%d')}
---

# 知识库演化建议

> 自动生成

## 建议创建的新概念

"""
            for s in suggestions:
                content += f"### {s['name']}\n\n- 原因: {s['reason']}\n- 建议模板: [[concept-template]]\n\n"

            content += f"\n---\n*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"

            suggest_path.write_text(content, encoding='utf-8')

            return {"type": "suggestions_created", "suggestions": suggestions}

        return {"type": "skip", "reason": "无建议"}


class ObsidianEventHandler(FileSystemEventHandler):
    """Obsidian 文件事件处理器"""

    def __init__(self, evolver: KnowledgeEvolver, debounce: int = 5):
        self.evolver = evolver
        self.debounce = debounce
        self.last_event = 0
        self.pending = False

    def on_modified(self, event):
        if event.is_directory:
            return

        if not event.src_path.endswith(".md"):
            return

        # 防抖
        now = time.time()
        if now - self.last_event < self.debounce:
            self.pending = True
            return

        self.last_event = now

        # 触发演化
        print(f"\n📝 检测到文件变化: {Path(event.src_path).name}")
        result = self.evolver.analyze_and_evolve()

        if result["status"] == "evolved":
            print(f"✅ 演化完成: {len(result.get('evolutions', []))} 项更新")


def run_daemon(vault_path: str, interval: int = 300):
    """守护进程模式：定期检查并演化"""
    evolver = KnowledgeEvolver(vault_path)

    print(f"🔄 启动知识库演化守护进程 (间隔: {interval}秒)")
    print(f"📁 知识库: {vault_path}\n")

    try:
        while True:
            result = evolver.analyze_and_evolve()

            if result["status"] == "evolved":
                print(f"✅ {result['timestamp']}: 演化完成")
                for e in result.get("evolutions", []):
                    print(f"   - {e['type']}: {len(e.get('documents', []))} 文档")

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\n👋 守护进程已停止")


def run_watch(vault_path: str):
    """监听模式：实时响应文件变化"""
    if not HAS_WATCHDOG:
        print("错误: 需要安装 watchdog 库")
        print("运行: pip install watchdog")
        sys.exit(1)

    evolver = KnowledgeEvolver(vault_path)
    event_handler = ObsidianEventHandler(evolver)

    observer = Observer()
    observer.schedule(event_handler, vault_path, recursive=True)
    observer.start()

    print(f"👀 启动文件监听模式")
    print(f"📁 知识库: {vault_path}")
    print(f"🛑 按 Ctrl+C 停止\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()
        print("\n👋 监听已停止")


def run_once(vault_path: str):
    """单次运行模式"""
    evolver = KnowledgeEvolver(vault_path)
    result = evolver.analyze_and_evolve(force=True)

    print(f"\n{'='*50}")
    print(f"知识库演化结果")
    print(f"{'='*50}\n")

    print(f"状态: {result['status']}")
    print(f"时间: {result.get('timestamp', 'N/A')}\n")

    analysis = result.get("analysis", {})
    print("📊 分析结果:")
    print(f"   总文档: {analysis.get('total_docs', 0)}")
    print(f"   总链接: {analysis.get('total_links', 0)}")
    print(f"   孤立文档: {len(analysis.get('orphans', []))}")
    print(f"   断开链接: {len(analysis.get('broken_links', []))}")
    print(f"   链接建议: {len(analysis.get('link_suggestions', []))}")

    print("\n🔄 演化执行:")
    for e in result.get("evolutions", []):
        print(f"   - {e['type']}")
        if e.get('documents'):
            for doc in e['documents'][:3]:
                print(f"     • {doc}")
        if e.get('suggestions'):
            for s in e['suggestions'][:3]:
                print(f"     • {s['name']}: {s['reason']}")


def main():
    parser = argparse.ArgumentParser(
        description="Obsidian 知识库自动演化工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --daemon           # 后台守护进程 (每5分钟检查一次)
  %(prog)s --watch            # 实时监听文件变化
  %(prog)s --on-change        # 单次执行
  %(prog)s --once             # 立即执行一次分析
        """
    )

    parser.add_argument("path", nargs="?", default=".", help="Obsidian 仓库路径")
    parser.add_argument("--daemon", "-d", action="store_true", help="守护进程模式")
    parser.add_argument("--watch", "-w", action="store_true", help="监听模式")
    parser.add_argument("--once", "-o", action="store_true", help="单次执行")
    parser.add_argument("--interval", "-i", type=int, default=300, help="守护进程间隔(秒)")

    args = parser.parse_args()

    vault_path = str(Path(args.path).resolve())

    if args.daemon:
        run_daemon(vault_path, args.interval)
    elif args.watch:
        run_watch(vault_path)
    elif args.once:
        run_once(vault_path)
    else:
        # 默认单次执行
        run_once(vault_path)


if __name__ == "__main__":
    main()