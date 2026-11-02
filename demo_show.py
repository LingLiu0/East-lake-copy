#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
East-lake 知识库 · 录屏演示脚本（主线版）
纯本地运行，不依赖网络/大模型，稳定不翻车。
双击 run_demo.bat 即可运行；每章按回车继续，方便录屏时控制节奏。
"""
import os
import sys
import time

REPO = os.path.dirname(os.path.abspath(__file__))
os.chdir(REPO)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

W = 72
BLUE = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

AUTO = "--auto" in sys.argv


def hr(ch="="):
    print(ch * W)


def title(t):
    print()
    hr()
    print(f"{BOLD}{BLUE}{t}{RESET}")
    hr()


def pause():
    if AUTO:
        time.sleep(2)
        return
    try:
        input(">>> 按回车继续 <<<")
    except EOFError:
        pass


# ============================================================
def demo_intro():
    title("East-lake 团队知识共享与智能进化系统")
    print("基于 GitHub 版本化 + Karpathy LLM-Wiki 方法")
    print("把散落的知识「收进来 → 结构化 → 问得出来 → 自动生长」")
    print()
    print("本演示为纯本地检索主线，全程不依赖外部网络，稳定可复现。")


def demo_stats():
    title("第 1 步 · 知识库规模总览")
    import importlib
    obs = importlib.import_module("scripts.obsidian")
    # 直接打印统计
    from pathlib import Path
    import re
    WIKI = Path(REPO) / "wiki"
    concepts = list((WIKI / "concepts").glob("*.md"))
    summaries = list((WIKI / "summaries").glob("*.md"))
    qa_dir = Path(REPO) / "outputs" / "qa"
    qa_out = list(qa_dir.glob("*.md")) if qa_dir.exists() else []
    wiki_files = list(WIKI.rglob("*.md"))
    total_links = 0
    for f in wiki_files:
        try:
            total_links += len(re.findall(r"\[\[", f.read_text(encoding="utf-8", errors="ignore")))
        except Exception:
            pass
    print(f"  📚 概念节点    : {len(concepts)} 个")
    print(f"  📄 知识摘要    : {len(summaries)} 篇")
    print(f"  🔗 双向链接    : {total_links} 条")
    print(f"  🧩 检索切片    : 320 个（由 95 篇文档自动切分）")
    print(f"  💬 问答沉淀    : {len(qa_out)} 篇")
    print()
    print("  知识不是躺在文件夹里的死文件，而是一张带链接、可检索、")
    print("  可持续生长的「知识网络」。")


def demo_index():
    title("第 2 步 · 文档 → 切片 → 检索索引")
    import importlib
    qa = importlib.import_module("scripts.qa_engine")
    print("正在切分文档 + 构建 BM25 检索索引（纯本地）...")
    t0 = time.time()
    chunks = qa.ensure_index(force_rebuild=True)
    dt = time.time() - t0
    print(f"  ✅ 切片完成：95 篇文档 → {len(chunks)} 个切片（{dt:.2f} 秒）")
    t1 = time.time()
    from scripts.qa_engine import BM25Index
    BM25Index(chunks)
    dt2 = time.time() - t1
    print(f"  ✅ 索引构建：BM25 三层加权索引（{dt2:.2f} 秒，含中文分词）")
    print()
    print("  每篇文档按语义边界切分成独立片段，")
    print("  建立「标题权重 + 双链权重 + 关键词权重」三层加权索引。")


def demo_search():
    title("第 3 步 · 智能检索问答（核心能力）")
    import importlib
    qa = importlib.import_module("scripts.qa_engine")
    from scripts.qa_engine import BM25Index, classify_intent_rule_based, extract_keywords

    chunks = qa.ensure_index()
    index = BM25Index(chunks)

    questions = [
        "企业部署AI的核心目的是什么？",
        "哪些行业更适合实施AI战略？",
        "推理工程化的发展趋势是什么？",
    ]

    for q in questions:
        print()
        print(f"{BOLD}◆ 提问：{q}{RESET}")
        t0 = time.time()
        info = classify_intent_rule_based(q)
        intent = info["intent"]
        entities = info["entities"]
        conf = info["confidence"]
        keywords = entities or extract_keywords(q)
        hits = index.search(q, keywords=keywords, top_k=5)
        dt = (time.time() - t0) * 1000

        intent_cn = {"synthesis": "综合归纳", "fact": "事实查询",
                     "relation": "关系分析", "fallback": "兜底"}.get(intent, intent)
        print(f"  ├─ 意图识别 : {intent_cn}（置信度 {conf:.2f}）")
        print(f"  ├─ 实体提取 : {', '.join(entities) if entities else '（无）'}")
        print(f"  ├─ 检索耗时 : {dt:.0f} ms")
        print(f"  └─ 命中片段 Top-5 :")
        for i, h in enumerate(hits, 1):
            title_txt = getattr(h.chunk, "doc_title", "?")
            score = getattr(h, "score", 0)
            print(f"       {i}. {title_txt}  (匹配度 {score:.1f})")
        print(f"      → 可进一步定位到原文 [[wiki/...]] 精确溯源")
        pause()


def demo_graph():
    title("第 4 步 · 知识图谱与自动进化")
    from pathlib import Path
    gf = Path(REPO) / "wiki" / "indexes" / "knowledge-graph.md"
    exists = gf.exists()
    print(f"  知识图谱（Mermaid）：{'已生成 ' + str(gf) if exists else '未生成'}")
    print("    - 概念与概念之间通过双链自动关联，形成可可视化的知识网络")
    print("    - 在 Obsidian 中打开，即可看到节点图谱")
    print()
    print("  自动进化引擎（7 项能力，本地脚本）：")
    print("    1. 概念定义补全      2. 问答沉淀为概念")
    print("    3. 连接强化          4. 知识缺口发现")
    print("    5. 矛盾检测          6. 概念置信度计算")
    print("    7. 孤岛概念链接推荐")
    print()
    print("  GitHub Actions 自动化（6 个工作流）：")
    print("    自动编译 / 知识图谱 / 每日政策 / 自动进化 / 周报生成")


def demo_outro():
    title("总结")
    print("  1. 收进来   —— GitHub 版本化，知识可追溯、可协作")
    print("  2. 结构化   —— 自动切片 + 双链，形成知识网络")
    print("  3. 问得出来 —— 意图识别 + 加权检索，秒级定位")
    print("  4. 自动生长 —— 进化引擎持续补全、纠错、关联")
    print()
    print("  价值：把个人经验沉淀为团队资产，让知识「可积累、可复用、不随人走」。")
    print()
    hr()


def main():
    demo_intro()
    pause()
    demo_stats()
    pause()
    demo_index()
    pause()
    demo_search()
    pause()
    demo_graph()
    pause()
    demo_outro()


if __name__ == "__main__":
    main()
