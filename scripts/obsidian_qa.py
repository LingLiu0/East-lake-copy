#!/usr/bin/env python3
"""
Obsidian AI 问答助手
基于本地知识库回答问题，自动关联已有概念

使用方法:
    python obsidian_qa.py "你的问题"
    python obsidian_qa.py --interactive
    python obsidian_qa.py --evolve "分析知识库并提出演化建议"
"""
import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Optional: 使用 Anthropic API
USE_ANTHROPIC = os.getenv("ANTHROPIC_API_KEY") is not None

if USE_ANTHROPIC:
    import anthropic


class ObsidianQA:
    """Obsidian 本地知识库 AI 问答助手"""

    def __init__(self, vault_path: str = None):
        self.vault_path = Path(vault_path or os.getcwd())
        self.index = self._build_index()

    def _build_index(self) -> dict[str, Any]:
        """构建知识库索引"""
        index = {
            "documents": [],
            "links": [],  # (source, target) pairs
            "tags": {},
            "concepts": [],
        }

        # 遍历所有 md 文件
        for md_file in self.vault_path.rglob("*.md"):
            # 跳过隐藏目录
            if any(part.startswith('.') for part in md_file.parts):
                continue

            content = md_file.read_text(encoding='utf-8')
            relative_path = md_file.relative_to(self.vault_path)

            # 提取 front matter
            title = self._extract_title(content, md_file.stem)
            tags = self._extract_tags(content)
            category = self._extract_category(relative_path)

            # 提取双向链接
            links = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', content)

            doc_info = {
                "path": str(relative_path),
                "title": title,
                "content": content,
                "tags": tags,
                "category": category,
                "links": links,
                "stem": md_file.stem,
            }

            index["documents"].append(doc_info)

            # 记录链接关系
            for link in links:
                index["links"].append((md_file.stem, link))

            # 记录标签
            for tag in tags:
                if tag not in index["tags"]:
                    index["tags"][tag] = []
                index["tags"][tag].append(doc_info)

            # 记录概念（concepts 目录下的文档）
            if "concepts" in str(relative_path):
                index["concepts"].append(doc_info)

        return index

    def _extract_title(self, content: str, default: str) -> str:
        """从 front matter 提取标题"""
        match = re.search(r'^title:\s*(.+)$', content, re.MULTILINE)
        return match.group(1).strip() if match else default

    def _extract_tags(self, content: str) -> list[str]:
        """从 front matter 提取标签"""
        match = re.search(r'^tags:\s*\[([^\]]+)\]', content, re.MULTILINE)
        if match:
            tags_str = match.group(1)
            return [t.strip().strip('"\' ') for t in tags_str.split(',')]
        return []

    def _extract_category(self, path: Path) -> str:
        """提取文档类别"""
        parts = path.parts
        if len(parts) > 1:
            return parts[0]
        return "root"

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """基于关键词搜索相关文档"""
        query_lower = query.lower()
        results = []

        for doc in self.index["documents"]:
            score = 0
            content_lower = doc["content"].lower()

            # 标题匹配
            if query_lower in doc["title"].lower():
                score += 10

            # 标签匹配
            for tag in doc["tags"]:
                if query_lower in tag.lower():
                    score += 5

            # 内容匹配
            score += content_lower.count(query_lower)

            # 链接匹配（文档被其他文档引用）
            linked_count = sum(1 for s, t in self.index["links"] if t == doc["stem"])
            score += linked_count * 2

            if score > 0:
                results.append({
                    **doc,
                    "score": score,
                    "preview": self._get_preview(doc["content"], query),
                })

        return sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]

    def _get_preview(self, content: str, query: str, context: int = 100) -> str:
        """获取包含查询词的上下文预览"""
        content_lower = content.lower()
        query_lower = query.lower()

        pos = content_lower.find(query_lower)
        if pos == -1:
            # 如果没找到精确匹配，取内容开头
            return content[:context * 2] + "..."

        start = max(0, pos - context)
        end = min(len(content), pos + len(query) + context)

        preview = content[start:end]
        if start > 0:
            preview = "..." + preview
        if end < len(content):
            preview = preview + "..."

        return preview

    def get_related_concepts(self, doc_path: str) -> list[str]:
        """获取与文档相关的概念"""
        stem = Path(doc_path).stem
        related = set()

        # 通过链接关系找
        for source, target in self.index["links"]:
            if source == stem:
                related.add(target)
            if target == stem:
                related.add(source)

        # 通过共同标签找
        doc = next((d for d in self.index["documents"] if d["stem"] == stem), None)
        if doc:
            for tag in doc["tags"]:
                for related_doc in self.index["tags"].get(tag, []):
                    if related_doc["stem"] != stem:
                        related.add(related_doc["stem"])

        return list(related)[:10]

    def get_backlinks(self, doc_path: str) -> list[str]:
        """获取反向链接（引用此文档的文档）"""
        stem = Path(doc_path).stem
        backlinks = []

        for source, target in self.index["links"]:
            if target == stem:
                # 找到引用此文档的文档
                for doc in self.index["documents"]:
                    if doc["stem"] == source:
                        backlinks.append({
                            "path": doc["path"],
                            "title": doc["title"],
                        })
                        break

        return backlinks

    def analyze_gaps(self) -> dict:
        """分析知识缺口"""
        gaps = {
            "orphaned": [],  # 没有被链接的文档
            "without_tags": [],  # 没有标签的文档
            "without_category": [],  # 没有类别的文档
            "isolated_concepts": [],  # 孤立的概念
        }

        linked_stems = set(s for s, t in self.index["links"])
        linked_stems.update(t for s, t in self.index["links"])

        for doc in self.index["documents"]:
            # 检查孤立文档
            if doc["stem"] not in linked_stems and doc["category"] in ["concepts", "decisions"]:
                gaps["orphaned"].append(doc)

            # 检查无标签
            if not doc["tags"]:
                gaps["without_tags"].append(doc)

            # 检查无类别（不在子目录）
            if "/" not in doc["path"] or doc["category"] == "root":
                gaps["without_category"].append(doc)

        return gaps

    def suggest_new_content(self) -> list[dict]:
        """基于现有知识结构，建议新增内容"""
        suggestions = []

        # 1. 找出高链接概念但没有详细文档的
        link_counts = {}
        for source, target in self.index["links"]:
            link_counts[target] = link_counts.get(target, 0) + 1

        high_link_targets = {k for k, v in link_counts.items() if v >= 3}

        for target in high_link_targets:
            exists = any(d["stem"] == target for d in self.index["documents"])
            if not exists:
                suggestions.append({
                    "type": "new_concept",
                    "reason": f"被 {link_counts[target]} 个文档引用但不存在",
                    "suggested_name": target,
                })

        # 2. 找出可以合并的相似概念
        # 基于标签聚类
        tag_groups = {}
        for doc in self.index["documents"]:
            for tag in doc["tags"]:
                if tag not in tag_groups:
                    tag_groups[tag] = []
                tag_groups[tag].append(doc["title"])

        for tag, titles in tag_groups.items():
            if len(titles) >= 3:
                suggestions.append({
                    "type": "index_page",
                    "reason": f"标签 '{tag}' 下有 {len(titles)} 个相关文档",
                    "suggested_name": f"索引: {tag}",
                })

        return suggestions

    def generate_summary(self) -> str:
        """生成知识库摘要"""
        total = len(self.index["documents"])
        concepts = len(self.index["concepts"])
        total_links = len(self.index["links"])
        total_tags = len(self.index["tags"])

        # 热门标签
        hot_tags = sorted(
            self.index["tags"].items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:10]

        categories = {}
        for doc in self.index["documents"]:
            cat = doc["category"]
            categories[cat] = categories.get(cat, 0) + 1

        return f"""# 知识库摘要

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 统计

| 指标 | 数值 |
|------|------|
| 总文档数 | {total} |
| 概念数 | {concepts} |
| 总链接数 | {total_links} |
| 总标签数 | {total_tags} |

## 类别分布

{chr(10).join(f'- {cat}: {count}' for cat, count in sorted(categories.items()))}

## 热门标签

{chr(10).join(f'- {tag}: {len(docs)} 个文档' for tag, docs in hot_tags)}

## 链接关系图

```mermaid
graph LR
"""

    # 添加节点
    for doc in self.index["documents"][:30]:  # 限制数量
        self.generate_summary += f'    {doc["stem"]}["{doc["title"][:20]}"]\n'

    # 添加链接
    for source, target in self.index["links"][:50]:  # 限制数量
        self.generate_summary += f'    {source} --> {target}\n'

    self.generate_summary += "```"
    return self.generate_summary


def ask_with_ai(query: str, context: str) -> str:
    """使用 AI 生成答案"""
    if not USE_ANTHROPIC:
        return None

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    prompt = f"""你是一个知识库助手。请基于以下上下文信息回答用户的问题。

上下文信息：
{context}

用户问题：{query}

请用中文回答。如果上下文中没有足够信息，请明确说明"根据知识库，现有信息不足以回答这个问题"。

回答格式：
1. 直接回答问题
2. 列出相关的知识库文档（用中文标题）
3. 如有需要，列出建议的后续问题
"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text


def main():
    parser = argparse.ArgumentParser(
        description="Obsidian AI 问答助手",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s "什么是 RAG 技术"
  %(prog)s --interactive
  %(prog)s --evolve "分析知识库"
  %(prog)s --gaps
  %(prog)s --summary
        """
    )

    parser.add_argument("query", nargs="?", help="要查询的问题")
    parser.add_argument("--interactive", "-i", action="store_true", help="交互式问答模式")
    parser.add_argument("--evolve", "-e", metavar="分析指令", help="分析知识库并提出演化建议")
    parser.add_argument("--gaps", "-g", action="store_true", help="分析知识缺口")
    parser.add_argument("--summary", "-s", action="store_true", help="生成知识库摘要")
    parser.add_argument("--path", "-p", default=".", help="Obsidian 仓库路径")
    parser.add_argument("--top-k", "-k", type=int, default=5, help="返回相关文档数量")

    args = parser.parse_args()

    # 初始化
    qa = ObsidianQA(args.path)

    if args.summary:
        print(qa.generate_summary())
        return

    if args.gaps:
        gaps = qa.analyze_gaps()
        print("\n=== 知识缺口分析 ===\n")

        print(f"📌 孤立文档（未被链接）: {len(gaps['orphaned'])}")
        for doc in gaps["orphaned"][:5]:
            print(f"   - {doc['title']} ({doc['path']})")

        print(f"\n🏷️ 无标签文档: {len(gaps['without_tags'])}")
        for doc in gaps["without_tags"][:5]:
            print(f"   - {doc['title']}")

        print(f"\n📂 未分类文档: {len(gaps['without_category'])}")

        return

    if args.evolve:
        # 演化分析
        suggestions = qa.suggest_new_content()
        gaps = qa.analyze_gaps()

        print("\n=== 知识库演化建议 ===\n")

        print("## 📝 建议新增内容\n")
        for i, s in enumerate(suggestions[:10], 1):
            print(f"{i}. [{s['type']}] {s['suggested_name']}")
            print(f"   原因: {s['reason']}\n")

        print("## ⚠️ 需要关注的缺口\n")
        if gaps["orphaned"]:
            print("孤立文档:")
            for doc in gaps["orphaned"][:5]:
                print(f"  - {doc['title']}")

        # 尝试用 AI 分析
        if USE_ANTHROPIC:
            print("\n## 🤖 AI 深度分析\n")
            context = f"""知识库包含 {len(qa.index['documents'])} 个文档，
{len(qa.index['links'])} 个链接，{len(qa.index['tags'])} 个标签。

建议新增：{suggestions[:5]}
知识缺口：孤立文档 {len(gaps['orphaned'])} 个

现有文档标题：
{chr(10).join(d['title'] for d in qa.index['documents'][:20])}"""

            answer = ask_with_ai(args.evolve, context)
            if answer:
                print(answer)
        return

    # 问答模式
    if args.interactive:
        print("=== Obsidian AI 问答助手 ===")
        print("输入问题进行查询，输入 'quit' 退出\n")

        while True:
            query = input("❓ 问题: ").strip()
            if not query or query.lower() in ["quit", "q", "exit"]:
                break

            results = qa.search(query, args.top_k)

            if not results:
                print("未找到相关内容\n")
                continue

            print(f"\n找到 {len(results)} 个相关文档:\n")

            for i, doc in enumerate(results, 1):
                print(f"--- [{i}] {doc['title']} (得分: {doc['score']})")
                print(f"    路径: {doc['path']}")
                print(f"    标签: {', '.join(doc['tags']) if doc['tags'] else '无'}")
                print(f"    预览: {doc['preview'][:150]}...")

                # 显示相关概念
                related = qa.get_related_concepts(doc["path"])
                if related:
                    print(f"    相关: {', '.join(related[:5])}")

                print()

            # 使用 AI 生成答案
            if USE_ANTHROPIC:
                print("🤖 AI 回答:\n")
                context = "\n\n".join(
                    f"文档{i+1}: {d['title']}\n{d['preview'][:500]}"
                    for i, d in enumerate(results[:3])
                )
                answer = ask_with_ai(query, context)
                if answer:
                    print(answer)
                print()

    elif args.query:
        results = qa.search(args.query, args.top_k)

        print(f"\n🔍 查询: {args.query}")
        print(f"📊 找到 {len(results)} 个相关文档:\n")

        for i, doc in enumerate(results, 1):
            print(f"[{i}] {doc['title']}")
            print(f"    路径: {doc['path']}")
            print(f"    得分: {doc['score']}")
            print(f"    预览: {doc['preview'][:120]}...\n")

        # AI 回答
        if USE_ANTHROPIC and results:
            print("=" * 50)
            print("🤖 AI 回答:\n")
            context = "\n\n".join(
                f"文档{i+1}: {d['title']}\n{d['preview'][:500]}"
                for i, d in enumerate(results[:3])
            )
            answer = ask_with_ai(args.query, context)
            if answer:
                print(answer)
        elif not USE_ANTHROPIC:
            print("💡 设置 ANTHROPIC_API_KEY 环境变量可启用 AI 回答功能")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()