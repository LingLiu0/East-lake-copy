#!/usr/bin/env python3
"""
chunker.py - Markdown 文档切片器

为 RAG 引擎把 wiki/ 下的 markdown 文档切成可索引的 chunk。
切片策略：按 H1/H2/H3 标题分块，单块超过 800 字时按段落再切。

每块保留元信息：
- doc_path：所属文档路径（相对 VAULT）
- doc_title：所属文档标题
- section：所在章节标题
- chunk_idx：块在文档中的序号
- text：块文本内容
- word_count：字数
- headings：文档内的所有 H1/H2 标题列表（用于上下文回溯）
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterator, List

VAULT = Path(os.getcwd())
WIKI = VAULT / "wiki"

# 切片参数
MAX_CHUNK_CHARS = 800   # 单块字符数上限（中文按字符算）
MIN_CHUNK_CHARS = 30    # 单块字符数下限
H1_PATTERN = re.compile(r'^#\s+(.+)$', re.MULTILINE)
H2_PATTERN = re.compile(r'^##\s+(.+)$', re.MULTILINE)
H3_PATTERN = re.compile(r'^###\s+(.+)$', re.MULTILINE)
FRONT_MATTER = re.compile(r'^---\n.*?\n---\n', re.DOTALL)
WIKI_LINK = re.compile(r'\[\[(wiki/[^\]]+)\]\]')  # 提取 [[wiki/...]] 双向链接


@dataclass
class Chunk:
    doc_path: str          # 例: "wiki/summaries/政策简报2026-05-07.md"
    doc_title: str         # 例: "政策简报 2026-05-07"
    section: str           # 例: "## 摘要" / "## 关键要点" / ""（front matter 部分）
    chunk_idx: int         # 块在文档内的序号，从 0 开始
    text: str              # 块文本
    word_count: int        # 字数
    headings: List[str]    # 文档的 H1/H2 列表（用于回溯）


def extract_title_and_front_matter(content: str) -> tuple[str, str, str]:
    """
    提取文档的 front matter、title、剩余正文

    Returns:
        (front_matter, title, body)
    """
    fm = ""
    title = ""
    body = content

    m = FRONT_MATTER.match(content)
    if m:
        fm = m.group(0)
        body = content[m.end():]
        title_match = re.search(r'^title:\s*(.+)$', fm, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip().strip('"').strip("'")

    if not title:
        h1 = H1_PATTERN.search(body)
        if h1:
            title = h1.group(1).strip()

    return fm, title, body


def extract_headings(body: str) -> List[str]:
    """提取文档所有 H1/H2 标题（按出现顺序）"""
    headings = []
    for pat in (H1_PATTERN, H2_PATTERN):
        for m in pat.finditer(body):
            headings.append(m.group(1).strip())
    return headings


def split_by_sections(body: str) -> Iterator[tuple[str, str]]:
    """
    按 H2 标题分块（保留 H1 作为前缀）

    Yields:
        (section_title, section_text)
    """
    lines = body.split('\n')
    current_h1 = ""
    current_h2 = ""
    current_buf: List[str] = []

    def flush():
        if current_buf:
            section = current_h2 or current_h1 or ""
            text = '\n'.join(current_buf).strip()
            if text:
                yield (section, text)
            current_buf.clear()

    for line in lines:
        h1 = H1_PATTERN.match(line)
        h2 = H2_PATTERN.match(line)

        if h1:
            yield from flush()
            current_h1 = h1.group(1).strip()
            current_h2 = ""
        elif h2:
            yield from flush()
            current_h2 = h2.group(1).strip()
        else:
            current_buf.append(line)

    yield from flush()


def split_long_section(text: str, max_chars: int = MAX_CHUNK_CHARS) -> List[str]:
    """
    单个 H2 section 超过 max_chars 时按段落切

    Returns:
        切分后的多个文本块
    """
    if len(text) <= max_chars:
        return [text]

    paragraphs = re.split(r'\n\s*\n', text)
    chunks: List[str] = []
    buf = ""

    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if len(p) > max_chars:
            if buf:
                chunks.append(buf.strip())
                buf = ""
            sentences = re.split(r'(?<=[。！？\n])', p)
            sub_buf = ""
            for s in sentences:
                if len(sub_buf) + len(s) > max_chars and sub_buf:
                    chunks.append(sub_buf.strip())
                    sub_buf = s
                else:
                    sub_buf += s
            if sub_buf:
                chunks.append(sub_buf.strip())
        elif len(buf) + len(p) + 2 > max_chars and buf:
            chunks.append(buf.strip())
            buf = p
        else:
            buf = (buf + "\n\n" + p) if buf else p

    if buf.strip():
        chunks.append(buf.strip())

    return chunks


def chunk_document(file_path: Path) -> List[Chunk]:
    """
    切片单个 markdown 文档

    Returns:
        Chunk 列表（按文档内顺序）
    """
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        print(f"⚠️ 读取失败: {file_path}: {e}")
        return []

    fm, title, body = extract_title_and_front_matter(content)
    if not title:
        title = file_path.stem
    headings = extract_headings(body)
    doc_path = str(file_path.relative_to(VAULT))

    chunks: List[Chunk] = []
    chunk_idx = 0

    if fm:
        fm_text = fm.strip()
        if len(fm_text) >= MIN_CHUNK_CHARS:
            chunks.append(Chunk(
                doc_path=doc_path,
                doc_title=title,
                section="(元信息)",
                chunk_idx=chunk_idx,
                text=fm_text,
                word_count=len(fm_text),
                headings=headings,
            ))
            chunk_idx += 1

    for section_title, section_text in split_by_sections(body):
        for piece in split_long_section(section_text):
            if len(piece) < MIN_CHUNK_CHARS:
                continue
            chunks.append(Chunk(
                doc_path=doc_path,
                doc_title=title,
                section=section_title or "(正文)",
                chunk_idx=chunk_idx,
                text=piece,
                word_count=len(piece),
                headings=headings,
            ))
            chunk_idx += 1

    return chunks


def chunk_wiki(verbose: bool = False) -> List[Chunk]:
    """切片 wiki/ 下所有文档"""
    all_chunks: List[Chunk] = []
    files = [f for f in WIKI.rglob("*.md")
             if not f.name.startswith('.') and 'indexes' not in f.parts]

    if verbose:
        print(f"  待切片: {len(files)} 个文档")

    for f in files:
        chunks = chunk_document(f)
        all_chunks.extend(chunks)
        if verbose and chunks:
            print(f"    {f.relative_to(VAULT)}: {len(chunks)} 块")

    return all_chunks


def save_chunks(chunks: List[Chunk], output_path: Path) -> None:
    """把 chunks 存为 JSONL（每行一个 chunk）"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for c in chunks:
            f.write(__import__('json').dumps(asdict(c), ensure_ascii=False) + '\n')


def load_chunks(input_path: Path) -> List[Chunk]:
    """从 JSONL 加载 chunks"""
    chunks = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = __import__('json').loads(line)
            chunks.append(Chunk(**data))
    return chunks


# ============================================================
# CLI
# ============================================================

def main():
    import argparse
    import json
    parser = argparse.ArgumentParser(description="wiki 文档切片器")
    parser.add_argument("--input", default="wiki", help="输入目录（相对 VAULT）")
    parser.add_argument("--output", default=".cache/chunks.jsonl", help="输出 JSONL 路径")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    print("=" * 60)
    print("  📑 wiki 文档切片器")
    print("=" * 60)
    print(f"  输入: {args.input}/")
    print(f"  输出: {args.output}")
    print()

    chunks = chunk_wiki(verbose=args.verbose)

    output_path = VAULT / args.output
    save_chunks(chunks, output_path)

    total_chars = sum(c.word_count for c in chunks)
    avg_chars = total_chars // len(chunks) if chunks else 0
    print()
    print(f"  ✅ 切片完成")
    print(f"     文档数: {len(set(c.doc_path for c in chunks))}")
    print(f"     chunk 总数: {len(chunks)}")
    print(f"     总字符数: {total_chars}")
    print(f"     平均 chunk 字符数: {avg_chars}")
    print(f"     输出: {output_path.relative_to(VAULT)}")


if __name__ == "__main__":
    main()
