#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
East-lake 知识库 · 傻瓜提问工具
双击 run_ask.bat 即可用；输入问题回车，即可检索知识库。
纯本地运行，不需要联网、不需要 API，稳定不翻车。
输入 q / quit / 退出 即可结束。
"""
import sys
import os
import time

REPO = os.path.dirname(os.path.abspath(__file__))
os.chdir(REPO)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

from scripts.qa_engine import BM25Index, classify_intent_rule_based, extract_keywords, ensure_index

W = 72
BOLD = ""
CYAN = ""
GREEN = ""
YELLOW = ""
RESET = ""

INTENT_CN = {
    "policy_query": "政策查询",
    "concept_explain": "概念解释",
    "relation_analysis": "关系分析",
    "synthesis": "综合归纳",
    "fallback": "兜底",
}


def hr(ch="="):
    print(ch * W)


def main():
    hr()
    print(f"{BOLD}{CYAN}  East-lake 知识库 · 智能问答{RESET}")
    print("  输入你的问题，回车即可检索知识库。")
    print("  输入 q / quit / 退出  结束程序。")
    hr()

    print("\n正在准备知识库索引（只需一次）...")
    chunks = ensure_index()
    index = BM25Index(chunks)
    print("索引就绪，可以提问了。\n")

    while True:
        try:
            q = input(">> 你的问题：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break
        if not q:
            continue
        if q.lower() in ("q", "quit", "exit") or q in ("退出", "结束"):
            print("再见！")
            break

        print()
        t0 = time.time()
        info = classify_intent_rule_based(q)
        intent = info["intent"]
        entities = info["entities"]
        conf = info["confidence"]
        keywords = entities or extract_keywords(q)
        hits = index.search(q, keywords=keywords, top_k=5)
        dt = (time.time() - t0) * 1000

        print(f"{BOLD}◆ 问题：{q}{RESET}")
        print(f"  ├─ 意图识别：{INTENT_CN.get(intent, intent)}（置信度 {conf:.2f}）")
        print(f"  ├─ 实体提取：{', '.join(entities) if entities else '（无）'}")
        print(f"  ├─ 检索耗时：{dt:.0f} ms")

        if hits:
            print(f"  └─ 命中片段 Top-{len(hits)}：")
            for i, h in enumerate(hits, 1):
                title_txt = getattr(h.chunk, "doc_title", "?")
                path_txt = getattr(h.chunk, "doc_path", "")
                print(f"       {i}. {title_txt}  (匹配度 {h.score:.1f})")
                if path_txt:
                    print(f"          来源: {path_txt}")
            print(f"      → 已定位到原文，可精确溯源。")
        else:
            print(f"  └─ {YELLOW}未命中：知识库中暂无相关内容。{RESET}")
            print(f"      提示：把新资料放进 raw/ 文件夹，再运行 compile 编译后即可检索。")

        print()
        hr("-")


if __name__ == "__main__":
    main()
