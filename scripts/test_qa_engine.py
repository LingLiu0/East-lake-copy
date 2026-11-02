#!/usr/bin/env python3
"""
test_qa_engine.py - RAG 引擎冒烟测试

无 LLM 调用也能跑：只测 chunker + BM25 索引 + 意图分类（规则化）。
要测 LLM 生成部分需配 API_KEY。
"""
import os
import sys
from pathlib import Path

VAULT = Path(os.getcwd())
SCRIPTS = VAULT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def test_chunker():
    print("\n" + "=" * 60)
    print("  TEST 1: chunker.py 切片器")
    print("=" * 60)
    from chunker import chunk_wiki, save_chunks

    chunks = chunk_wiki(verbose=True)
    save_chunks(chunks, VAULT / ".cache" / "chunks_test.jsonl")

    assert len(chunks) > 0, "未生成任何 chunk"
    print(f"\n  ✅ 通过：生成 {len(chunks)} chunks")
    print(f"     示例 chunk:")
    sample = chunks[0]
    print(f"     - doc_path: {sample.doc_path}")
    print(f"     - doc_title: {sample.doc_title}")
    print(f"     - section: {sample.section}")
    print(f"     - text 前 80 字: {sample.text[:80]}...")
    return chunks


def test_intent_classifier():
    print("\n" + "=" * 60)
    print("  TEST 2: 意图分类器（规则化）")
    print("=" * 60)
    from qa_engine import classify_intent_rule_based

    test_cases = [
        ("湖北 5G 政策有哪些？", "policy_query"),
        ("什么是新质生产力？", "concept_explain"),
        ("5G 和 5G-A 区别在哪？", "relation_analysis"),
        ("分析一下 2026 数字经济趋势", "synthesis"),
        ("今天天气如何", "fallback"),
        ("1+1 等于几？", "fallback"),
        ("湖北 5G 和 4G 区别", "relation_analysis"),
    ]

    passed = 0
    for query, expected_intent in test_cases:
        result = classify_intent_rule_based(query)
        actual = result["intent"]
        status = "✅" if actual == expected_intent else "⚠️"
        if actual == expected_intent:
            passed += 1
        print(f"  {status} \"{query}\"")
        print(f"     期望: {expected_intent} | 实际: {actual} (conf={result['confidence']:.2f})")
        print(f"     实体: {result['entities']}")

    print(f"\n  通过率: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_bm25_index(chunks):
    print("\n" + "=" * 60)
    print("  TEST 3: BM25 索引 + 检索")
    print("=" * 60)

    try:
        from qa_engine import BM25Index, extract_keywords
    except ImportError as e:
        print(f"  ⚠️ 跳过：{e}（依赖未安装）")
        return False

    if not chunks:
        print("  ⚠️ 跳过：无 chunks")
        return False

    index = BM25Index(chunks)
    keywords = extract_keywords("湖北 数字经济 政策")
    print(f"\n  查询: '湖北 数字经济 政策'")
    print(f"  关键词: {keywords}")
    print()

    hits = index.search("湖北 数字经济 政策", keywords=keywords, top_k=5)
    print(f"  命中 {len(hits)} 条:")
    for i, h in enumerate(hits[:5], 1):
        print(f"    {i}. {h.chunk.doc_title} [{h.chunk.section}]")
        print(f"       {h.explain()}")

    assert len(hits) > 0, "BM25 未返回任何命中"
    print(f"\n  ✅ 通过：BM25 检索正常")
    return True


def test_template_loader():
    print("\n" + "=" * 60)
    print("  TEST 4: 模板加载器")
    print("=" * 60)
    from qa_engine import load_template

    template_files = [
        ("qa", "policy_query"),
        ("qa", "concept_explain"),
        ("qa", "relation_analysis"),
        ("qa", "synthesis"),
        ("qa", "fallback"),
        ("qa", "intent_classify"),
        ("qa", "quality_eval"),
        ("evolution", "concept_complete"),
        ("evolution", "concept_link"),
        ("evolution", "contradiction_check"),
        ("evolution", "qa_to_concept"),
    ]

    passed = 0
    for kind, name in template_files:
        try:
            system_prompt, fm = load_template(kind, name)
            assert len(system_prompt) > 50, f"模板 {kind}/{name} system_prompt 过短"
            assert "name" in fm, f"模板 {kind}/{name} 缺 front matter"
            print(f"  ✅ {kind}/{name}: {len(system_prompt)} 字符, fm keys = {list(fm.keys())}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {kind}/{name}: {e}")

    print(f"\n  通过率: {passed}/{len(template_files)}")
    return passed == len(template_files)


def test_confidence():
    print("\n" + "=" * 60)
    print("  TEST 5: 概念置信度评估")
    print("=" * 60)
    sys.path.insert(0, str(SCRIPTS))
    from auto_evolve import compute_concept_confidence

    WIKI = VAULT / "wiki" / "concepts"
    if not WIKI.exists():
        print("  ⚠️ 跳过：无概念库")
        return False

    concepts = list(WIKI.glob("*.md"))[:5]
    print(f"  抽样 {len(concepts)} 个概念：")
    for cf in concepts:
        conf, scores = compute_concept_confidence(cf)
        print(f"    {cf.stem}: confidence={conf:.3f}")
        for k, v in scores.items():
            print(f"      - {k}: {v:.3f}")

    print(f"\n  ✅ 通过：置信度评估函数可调用")
    return True


def main():
    print("=" * 60)
    print("  🧪 RAG 智能问答引擎 - 冒烟测试")
    print("=" * 60)

    results = {}

    try:
        chunks = test_chunker()
        results["chunker"] = True
    except Exception as e:
        print(f"  ❌ chunker 失败: {e}")
        results["chunker"] = False
        chunks = []

    try:
        results["intent"] = test_intent_classifier()
    except Exception as e:
        print(f"  ❌ 意图分类器失败: {e}")
        results["intent"] = False

    try:
        results["bm25"] = test_bm25_index(chunks)
    except Exception as e:
        print(f"  ❌ BM25 失败: {e}")
        results["bm25"] = False

    try:
        results["templates"] = test_template_loader()
    except Exception as e:
        print(f"  ❌ 模板加载失败: {e}")
        results["templates"] = False

    try:
        results["confidence"] = test_confidence()
    except Exception as e:
        print(f"  ❌ 置信度失败: {e}")
        results["confidence"] = False

    print("\n" + "=" * 60)
    print("  📊 测试总结")
    print("=" * 60)
    for name, ok in results.items():
        status = "✅" if ok else "❌"
        print(f"  {status} {name}")

    if all(results.values()):
        print("\n  🎉 全部通过！")
    else:
        print("\n  ⚠️ 部分测试未通过，请检查")
    print()

    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
