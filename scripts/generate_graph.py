#!/usr/bin/env python3
"""
知识图谱生成器
生成 Mermaid 格式的知识网络图
"""
from pathlib import Path
import re
from datetime import datetime

VAULT = Path(".")
WIKI = VAULT / "wiki"
GRAPH_FILE = WIKI / "indexes" / "knowledge-graph.md"


def generate_graph():
    """生成知识图谱"""
    concepts_dir = WIKI / "concepts"
    summaries_dir = WIKI / "summaries"

    if not concepts_dir.exists():
        print("❌ concepts/ 目录不存在")
        return

    concept_files = list(concepts_dir.glob("*.md"))
    summary_files = list(summaries_dir.glob("*.md")) if summaries_dir.exists() else []

    if not concept_files:
        print("❌ 没有概念文件")
        return

    # 收集所有概念
    nodes = set()
    for cf in concept_files:
        nodes.add(cf.stem)

    # 收集所有关系（从 summaries 和 concepts）
    edges = []

    # 从 summaries 提取关系
    for sf in summary_files:
        try:
            content = sf.read_text(encoding='utf-8', errors='ignore')
            links = re.findall(r'\[\[wiki/concepts/([^\]]+)\]\]', content.replace(',', ''))
            for link in links:
                link = link.strip()
                if link in nodes:
                    edges.append((sf.stem, link))
        except:
            pass

    # 从 concepts 提取关系
    for cf in concept_files:
        concept = cf.stem
        try:
            content = cf.read_text(encoding='utf-8', errors='ignore')
            links = re.findall(r'\[\[wiki/concepts/([^\]]+)\]\]', content.replace(',', ''))
            for link in links:
                link = link.strip()
                if link in nodes and link != concept:
                    edges.append((concept, link))
        except:
            pass

    # 去重
    edges = list(set(edges))

    # 生成 Mermaid 图谱
    mermaid = """# 知识图谱

> 自动生成的知识网络

```mermaid
flowchart LR
"""

    for node in nodes:
        safe_id = node.replace(' ', '-')
        mermaid += f"    {safe_id}[\"{node}\"]\n"

    mermaid += "\n"

    for src, dst in edges:
        src_id = src.replace(' ', '-')
        dst_id = dst.replace(' ', '-')
        mermaid += f"    {src_id} --> {dst_id}\n"

    mermaid += "```\n\n"

    # 统计信息
    mermaid += "---\n\n"
    mermaid += f"## 统计\n\n"
    mermaid += f"- 概念数量: {len(nodes)}\n"
    mermaid += f"- 关联数量: {len(edges)}\n"
    mermaid += f"- 更新于: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

    # 保存
    GRAPH_FILE.parent.mkdir(parents=True, exist_ok=True)
    GRAPH_FILE.write_text(mermaid, encoding='utf-8')

    print(f"✅ 知识图谱已生成: {GRAPH_FILE}")
    print(f"   - 概念: {len(nodes)}")
    print(f"   - 关联: {len(edges)}")


if __name__ == "__main__":
    generate_graph()