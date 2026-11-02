#!/usr/bin/env python3
"""
qa_engine.py - RAG 智能问答引擎

子任务三核心模块。流程：
  query → 意图分类 → 切片索引 → 混合检索（BM25 + 关键词权重）→ LLM 生成 → 答案沉淀

设计要点：
- 不依赖重型 embedding 模型（避免下载失败）
- 默认用 BM25 做基础检索 + 标题/链接加权 + 关键词命中率
- 可选升级：若 vector_store 可用，则叠加向量检索（rerank）
- Prompt 模板从 templates/qa/ 动态加载
- 答案沉淀到 outputs/qa/ 包含来源标注
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# 第三方（运行时检查）
try:
    import jieba
    import jieba.posseg as pseg
    JIEBA_OK = True
except ImportError:
    JIEBA_OK = False

try:
    from rank_bm25 import BM25Okapi
    BM25_OK = True
except ImportError:
    BM25_OK = False

# 路径
VAULT = Path(os.getcwd())
SCRIPTS = VAULT / "scripts"
WIKI = VAULT / "wiki"
OUTPUTS = VAULT / "outputs"
TEMPLATES = VAULT / "templates"
CACHE = VAULT / ".cache"
CACHE.mkdir(parents=True, exist_ok=True)
QA_DIR = OUTPUTS / "qa"
QA_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(SCRIPTS))
from chunker import Chunk, chunk_wiki, load_chunks, save_chunks  # noqa: E402


# ============================================================
# 数据类
# ============================================================

@dataclass
class RetrievalHit:
    """单条检索命中"""
    chunk: Chunk
    score: float
    bm25_score: float = 0.0
    title_boost: float = 0.0
    link_boost: float = 0.0
    keyword_hits: List[str] = field(default_factory=list)

    def explain(self) -> str:
        return (f"score={self.score:.3f} "
                f"(bm25={self.bm25_score:.3f}, "
                f"title={self.title_boost:.2f}, "
                f"link={self.link_boost:.2f}, "
                f"hits={','.join(self.keyword_hits[:3])})")


@dataclass
class QAResult:
    """问答结果"""
    query: str
    intent: str
    entities: List[str]
    confidence: float
    hits: List[RetrievalHit]
    answer: str
    sources: List[str]
    used_template: str
    elapsed_ms: int
    quality_scores: Optional[Dict[str, float]] = None
    error: Optional[str] = None


# ============================================================
# 工具
# ============================================================

def tokenize(text: str) -> List[str]:
    """中文 + 英文混合分词"""
    if not JIEBA_OK:
        return re.findall(r'[\w]+', text.lower())

    tokens = []
    for word, flag in pseg.cut(text):
        word = word.strip()
        if not word:
            continue
        if flag.startswith(('n', 'v', 'a', 'eng', 'i')):
            tokens.append(word.lower())
        elif len(word) == 1 and '\u4e00' <= word <= '\u9fff':
            tokens.append(word)
    return tokens


def extract_keywords(query: str, max_keywords: int = 8) -> List[str]:
    """从查询中提取关键词（用于检索权重）"""
    if not JIEBA_OK:
        return [w for w in re.findall(r'[\w]+', query) if len(w) >= 2][:max_keywords]

    keywords = []
    for word, flag in pseg.cut(query):
        w = word.strip()
        if not w:
            continue
        if flag.startswith(('n', 'vn', 'eng')) and len(w) >= 2:
            keywords.append(w)
    seen = set()
    result = []
    for k in keywords:
        if k not in seen:
            seen.add(k)
            result.append(k)
    return result[:max_keywords]


def load_template(kind: str, name: str) -> Tuple[str, Dict]:
    """
    加载模板文件，提取 system prompt 和 front matter
    """
    template_path = TEMPLATES / kind / f"{name}.md"
    if not template_path.exists():
        raise FileNotFoundError(f"模板不存在: {template_path}")

    content = template_path.read_text(encoding='utf-8')
    fm: Dict = {}
    body = content

    m = re.match(r'^---\n(.*?)\n---\n(.*)$', content, re.DOTALL)
    if m:
        fm_text = m.group(1)
        body = m.group(2)
        for line in fm_text.split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                fm[k.strip()] = v.strip()

    h1 = re.search(r'^#\s+System Prompt\s*\n(.*?)(?=^---\s*$|\Z)',
                   body, re.MULTILINE | re.DOTALL)
    if h1:
        system_prompt = h1.group(1).strip()
    else:
        system_prompt = body.strip()

    return system_prompt, fm


# ============================================================
# BM25 索引
# ============================================================

class BM25Index:
    """基于 BM25 的 chunk 索引"""

    def __init__(self, chunks: List[Chunk]):
        self.chunks = chunks
        self.tokenized_corpus = []
        self.bm25 = None

        if not BM25_OK:
            print("⚠️ rank_bm25 未安装，BM25 检索不可用")
            return

        if not JIEBA_OK:
            print("⚠️ jieba 未安装，回退到英文分词")

        print(f"  🔨 构建 BM25 索引 ({len(chunks)} chunks)...")
        t0 = time.time()
        for c in chunks:
            text = f"{c.doc_title} {c.section} {c.text}"
            self.tokenized_corpus.append(tokenize(text))

        self.bm25 = BM25Okapi(self.tokenized_corpus)
        print(f"  ✅ BM25 索引构建完成 ({time.time() - t0:.2f}s)")

    def search(self, query: str, keywords: List[str],
               top_k: int = 10) -> List[RetrievalHit]:
        if self.bm25 is None:
            return []

        query_tokens = tokenize(query)
        bm25_scores = self.bm25.get_scores(query_tokens)

        keyword_hits_map: Dict[int, List[str]] = {}
        for idx, chunk in enumerate(self.chunks):
            text_lower = (chunk.doc_title + chunk.section + chunk.text).lower()
            hit_words = [k for k in keywords if k.lower() in text_lower]
            if hit_words:
                keyword_hits_map[idx] = hit_words

        hits: List[RetrievalHit] = []
        for idx, score in enumerate(bm25_scores):
            if score <= 0:
                continue
            chunk = self.chunks[idx]

            title_lower = chunk.doc_title.lower()
            title_boost = sum(0.5 for k in keywords if k.lower() in title_lower)

            link_count = len(re.findall(r'\[\[wiki/', chunk.text))
            link_boost = min(link_count * 0.1, 0.5)

            kw_boost = 0.0
            kw_hits = keyword_hits_map.get(idx, [])
            kw_boost = min(len(kw_hits) * 0.3, 1.0)

            total_score = score + title_boost + link_boost + kw_boost

            hits.append(RetrievalHit(
                chunk=chunk,
                score=total_score,
                bm25_score=score,
                title_boost=title_boost,
                link_boost=link_boost,
                keyword_hits=kw_hits,
            ))

        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:top_k]


# ============================================================
# 意图分类
# ============================================================

INTENT_KEYWORDS = {
    "policy_query": ["政策", "意见", "通知", "规划", "方案", "行动", "印发", "出台",
                     "发布", "聚焦", "举措", "实施意见", "行动计划", "支持文件", "规范",
                     "标准", "规定", "条例"],
    "concept_explain": ["什么是", "定义", "解释", "含义", "概念", "指什么", "是何含义",
                        "什么叫", "是何物", "怎么理解", "如何理解", "是什么意思"],
    "relation_analysis": ["关系", "区别", "对比", "比较", "影响", "区别于",
                          "相对于", "和", "与", "vs", "和...差异"],
    "synthesis": ["分析", "研判", "趋势", "前景", "综述", "整体", "总结", "研报"],
}

# 概念解释类"强信号"词 - 命中即判定为 concept_explain（避免弱词误判）
STRONG_CONCEPT_KEYWORDS = ["什么是", "定义", "解释", "什么叫", "怎么理解", "如何理解", "是什么意思"]


def classify_intent_rule_based(query: str) -> Dict:
    """规则化意图分类（不调 LLM，零延迟）"""
    query_lower = query.lower()
    scores = {intent: 0 for intent in INTENT_KEYWORDS}
    scores["synthesis"] = 0
    scores["fallback"] = 0

    for intent, kws in INTENT_KEYWORDS.items():
        for kw in kws:
            if kw in query or kw.lower() in query_lower:
                scores[intent] += 1

    if len(query.strip()) < 4:
        return {"intent": "fallback", "entities": [], "confidence": 0.30}

    SCENARIO_KEYWORDS = (
        "政策", "意见", "通知", "规划", "方案", "数字", "5G", "AI", "算力",
        "湖北", "移动", "政企", "ICT", "项目", "战略", "业务", "客户",
        "技术", "市场", "产品", "运营", "管理", "团队", "概念", "新质",
        "产业", "智能", "模型", "应用", "平台", "网络", "算力", "数据",
    )
    has_scenario_kw = any(kw in query for kw in SCENARIO_KEYWORDS)

    if scores["concept_explain"] > 0 and any(kw in query for kw in STRONG_CONCEPT_KEYWORDS):
        intent = "concept_explain"
        confidence = min(0.6 + scores["concept_explain"] * 0.1, 0.95)
    elif scores["policy_query"] >= scores["relation_analysis"] and scores["policy_query"] > 0:
        intent = "policy_query"
        confidence = min(0.5 + scores["policy_query"] * 0.1, 0.90)
    elif scores["synthesis"] > 0 and scores["relation_analysis"] == 0:
        # "趋势/分析/研判" 等合成关键词且无对比关系词 → 合成
        intent = "synthesis"
        confidence = min(0.6 + scores["synthesis"] * 0.1, 0.90)
    elif scores["relation_analysis"] > 0:
        intent = "relation_analysis"
        confidence = min(0.5 + scores["relation_analysis"] * 0.1, 0.90)
    elif not has_scenario_kw and scores["synthesis"] == 0:
        intent = "fallback"
        confidence = 0.40
    else:
        intent = "synthesis"
        confidence = 0.50

    entities = extract_keywords(query)
    return {
        "intent": intent,
        "entities": entities,
        "confidence": confidence,
    }


def classify_intent_with_llm(query: str, client) -> Dict:
    """用 LLM 分类意图（精度更高但更慢）"""
    try:
        system_prompt, _ = load_template("qa", "intent_classify")
        prompt = f"用户问题：{query}\n\n请输出 JSON 分类结果。"
        result_text = client(system_prompt + "\n\n" + prompt, max_tokens=200)

        if not result_text:
            return classify_intent_rule_based(query)

        m = re.search(r'\{.*\}', result_text, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        print(f"  ⚠️ LLM 分类失败: {e}")

    return classify_intent_rule_based(query)


# ============================================================
# 答案生成
# ============================================================

def build_context(hits: List[RetrievalHit], max_chars: int = 4000) -> str:
    """把 top-k hits 拼成 context 文本"""
    parts = []
    total = 0
    for i, h in enumerate(hits, 1):
        chunk = h.chunk
        text = f"## [{i}] {chunk.doc_title}\n路径: {chunk.doc_path}\n片段: {chunk.text[:500]}\n"
        if total + len(text) > max_chars:
            break
        parts.append(text)
        total += len(text)
    return "\n".join(parts)


def select_template(intent: str) -> str:
    """根据 intent 选模板名"""
    return {
        "policy_query": "policy_query",
        "concept_explain": "concept_explain",
        "relation_analysis": "relation_analysis",
        "synthesis": "synthesis",
    }.get(intent, "fallback")


def generate_answer(query: str, intent: str, entities: List[str],
                    hits: List[RetrievalHit], client) -> str:
    """调 LLM 生成答案"""
    template_name = select_template(intent)
    system_prompt, _ = load_template("qa", template_name)

    context = build_context(hits)
    intent_meta = {"entities": entities}

    if not hits and intent != "fallback":
        template_name = "fallback"
        system_prompt, _ = load_template("qa", template_name)
        context = ""

    user_msg = f"""用户问题：{query}

实体识别：{', '.join(entities) if entities else '无'}

检索片段（可能为空）：
{context if context else '（未检索到相关内容）'}"""

    answer = client(system_prompt + "\n\n" + user_msg, max_tokens=1500)

    if not answer:
        return "❌ 答案生成失败（API 调用返回空）"

    return answer


def extract_sources_from_answer(answer: str) -> List[str]:
    """从答案中提取 [[wiki/...]] 链接作为来源"""
    sources = re.findall(r'\[\[(wiki/[^\]]+)\]\]', answer)
    seen = set()
    result = []
    for s in sources:
        if s not in seen:
            seen.add(s)
            result.append(s)
    return result


def evaluate_quality(query: str, answer: str, hits: List[RetrievalHit],
                     client) -> Optional[Dict]:
    """评估答案质量（可选，二阶段）"""
    if not hits or not answer or answer.startswith("❌"):
        return None

    try:
        system_prompt, _ = load_template("qa", "quality_eval")
        context_summary = "\n".join(
            f"- {h.chunk.doc_title} ({h.chunk.doc_path})"
            for h in hits[:5]
        )
        user_msg = f"""用户问题：{query}

生成的答案：
{answer}

用到的检索片段：
{context_summary}

请输出 JSON 评分。"""

        result = client(system_prompt + "\n\n" + user_msg, max_tokens=300)
        if not result:
            return None
        m = re.search(r'\{.*\}', result, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        print(f"  ⚠️ 质量评估失败: {e}")
    return None


# ============================================================
# 主问答入口
# ============================================================

def get_default_client():
    """获取 LLM 客户端（优先用 api_client）"""
    try:
        from api_client import chat
        return chat
    except ImportError:
        return None


def ensure_index(force_rebuild: bool = False) -> List[Chunk]:
    """确保 chunk 索引存在（缓存到 .cache/chunks.jsonl）"""
    cache_path = CACHE / "chunks.jsonl"
    needs_rebuild = force_rebuild or not cache_path.exists()

    if not needs_rebuild:
        cache_mtime = cache_path.stat().st_mtime
        if WIKI.exists():
            wiki_mtime = max(
                (f.stat().st_mtime for f in WIKI.rglob("*.md") if f.is_file()),
                default=0,
            )
            if wiki_mtime > cache_mtime:
                needs_rebuild = True

    if needs_rebuild:
        chunks = chunk_wiki(verbose=False)
        save_chunks(chunks, cache_path)
        return chunks

    return load_chunks(cache_path)


def ask(query: str, use_llm_intent: bool = False,
        evaluate: bool = False, client=None) -> QAResult:
    """主问答入口

    Args:
        query: 用户问题
        use_llm_intent: 是否用 LLM 分类意图（更准但更慢）
        evaluate: 是否做二阶段质量评估
        client: LLM 客户端（默认用 scripts/api_client.chat）

    Returns:
        QAResult 对象
    """
    t0 = time.time()
    client = client or get_default_client()
    if client is None:
        return QAResult(
            query=query, intent="fallback", entities=[], confidence=0,
            hits=[], answer="❌ 未配置 LLM 客户端（检查 API_KEY 等环境变量）",
            sources=[], used_template="fallback", elapsed_ms=0,
            error="no_client",
        )

    if use_llm_intent:
        intent_info = classify_intent_with_llm(query, client)
    else:
        intent_info = classify_intent_rule_based(query)
    intent = intent_info["intent"]
    entities = intent_info["entities"]
    intent_conf = intent_info["confidence"]

    hits: List[RetrievalHit] = []
    if intent != "fallback":
        chunks = ensure_index(force_rebuild=False)
        if chunks and BM25_OK:
            index = BM25Index(chunks)
            keywords = entities or extract_keywords(query)
            hits = index.search(query, keywords=keywords, top_k=8)

    answer = generate_answer(query, intent, entities, hits, client)
    sources = extract_sources_from_answer(answer)

    quality = None
    if evaluate and hits:
        quality = evaluate_quality(query, answer, hits, client)

    elapsed = int((time.time() - t0) * 1000)

    return QAResult(
        query=query,
        intent=intent,
        entities=entities,
        confidence=intent_conf,
        hits=hits,
        answer=answer,
        sources=sources,
        used_template=select_template(intent),
        elapsed_ms=elapsed,
        quality_scores=quality.get("scores") if quality else None,
    )


def save_qa_to_wiki(result: QAResult) -> Path:
    """把问答沉淀到 outputs/qa/"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_query = re.sub(r'[\\/:*?"<>|]', '_', result.query)[:20]
    qa_file = QA_DIR / f"{timestamp}-{safe_query}.md"

    hits_section = "\n".join(
        f"- [[{h.chunk.doc_path}]] (score={h.score:.2f}, {h.explain()})"
        for h in result.hits[:5]
    )

    sources_section = "\n".join(f"- [[{s}]]" for s in result.sources) or "- 无"

    quality_section = ""
    if result.quality_scores:
        scores_str = ", ".join(f"{k}={v:.2f}" for k, v in result.quality_scores.items())
        quality_section = f"\n## 质量评分\n\n{scores_str}\n"

    content = f"""---
title: {result.query}
date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
type: qa
intent: {result.intent}
entities: [{', '.join(result.entities)}]
elapsed_ms: {result.elapsed_ms}
---

# {result.query}

## 意图识别

- **类型**: {result.intent}
- **实体**: {', '.join(result.entities) if result.entities else '无'}
- **置信度**: {result.confidence:.2f}
- **使用模板**: {result.used_template}

## 检索片段（top-5）

{hits_section if hits_section else '（无）'}

## AI 回答

{result.answer}

## 来源

{sources_section}
{quality_section}
---

*由 qa_engine.py 自动生成*
"""

    qa_file.write_text(content, encoding='utf-8')
    return qa_file


# ============================================================
# CLI
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="RAG 智能问答引擎")
    parser.add_argument("query", nargs="*", help="问题（不传则进入交互模式）")
    parser.add_argument("--llm-intent", action="store_true", help="用 LLM 分类意图")
    parser.add_argument("--evaluate", action="store_true", help="启用质量评估")
    parser.add_argument("--rebuild-index", action="store_true", help="强制重建 chunk 索引")
    parser.add_argument("--save", action="store_true", help="保存问答到 outputs/qa/")
    parser.add_argument("--show-hits", action="store_true", help="显示检索命中详情")
    args = parser.parse_args()

    print("=" * 70)
    print("  🧠 RAG 智能问答引擎 — 子任务三")
    print("=" * 70)
    print()

    if args.rebuild_index:
        print("🔨 强制重建 chunk 索引...")
        chunks = ensure_index(force_rebuild=True)
        print(f"  共 {len(chunks)} chunks")
        print()

    if not args.query:
        print("输入问题（Ctrl+C 退出）：")
        try:
            while True:
                q = input("\n> ").strip()
                if not q:
                    continue
                result = ask(q, use_llm_intent=args.llm_intent,
                             evaluate=args.evaluate)
                print()
                print(f"  🎯 意图: {result.intent} (置信度 {result.confidence:.2f})")
                print(f"  📊 检索: {len(result.hits)} 命中")
                if args.show_hits and result.hits:
                    for i, h in enumerate(result.hits[:3], 1):
                        print(f"     {i}. {h.chunk.doc_title} [{h.chunk.section}] — {h.explain()}")
                print()
                print(f"  💡 回答 ({result.elapsed_ms}ms):\n")
                print(result.answer)
                print()
                if result.quality_scores:
                    scores = ", ".join(f"{k}={v:.2f}" for k, v in result.quality_scores.items())
                    print(f"  📈 质量: {scores}")
                if args.save:
                    qa_file = save_qa_to_wiki(result)
                    print(f"\n  💾 已保存: {qa_file.relative_to(VAULT)}")
        except KeyboardInterrupt:
            print("\n👋 退出")
        return

    query = " ".join(args.query)
    result = ask(query, use_llm_intent=args.llm_intent,
                 evaluate=args.evaluate)

    print(f"问题: {result.query}")
    print(f"意图: {result.intent} (置信度 {result.confidence:.2f})")
    print(f"实体: {', '.join(result.entities) if result.entities else '无'}")
    print(f"模板: {result.used_template}")
    print(f"耗时: {result.elapsed_ms}ms")
    print(f"检索: {len(result.hits)} 命中")
    print()

    if args.show_hits and result.hits:
        print("检索命中：")
        for i, h in enumerate(result.hits[:5], 1):
            print(f"  {i}. {h.chunk.doc_title} [{h.chunk.section}]")
            print(f"     {h.explain()}")
        print()

    print("=" * 70)
    print("回答：")
    print("=" * 70)
    print(result.answer)

    if result.quality_scores:
        scores = ", ".join(f"{k}={v:.2f}" for k, v in result.quality_scores.items())
        print(f"\n质量评分: {scores}")

    if args.save:
        qa_file = save_qa_to_wiki(result)
        print(f"\n💾 已保存: {qa_file.relative_to(VAULT)}")


if __name__ == "__main__":
    main()
