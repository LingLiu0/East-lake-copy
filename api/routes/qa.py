"""
QA Routes - RAG 智能问答端点（子任务三）

暴露 HTTP 接口让 RAG 引擎（scripts/qa_engine.py）可被外部服务调用。

端点：
- POST /qa/                单次问答
- GET  /qa/health          健康检查（确认 qa_engine 可用）
- POST /qa/evaluate        用评估集打分（如果存在 evaluation/qa_eval.jsonl）
"""
import logging
import os
import time
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi.security import APIKeyHeader

from api.models import QARequest, QAResponse, SourceItem
from api.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/qa", tags=["qa"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
api_key_header = APIKeyHeader(name=settings.api_key_header, auto_error=False)


async def verify_api_key(api_key: Annotated[str | None, Depends(api_key_header)]):
    """验证 API key（与 search 路由一致）"""
    if settings.admin_api_key and api_key != settings.admin_api_key:
        if settings.debug or not settings.admin_api_key:
            return True
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True


# ============================================================
# qa_engine 单例导入（避免重复加载 BM25 索引）
# ============================================================

_qa_engine_module = None
_engine_load_error = None


def get_qa_engine():
    """惰性加载 qa_engine，避免在 import 时就建立 BM25 索引"""
    global _qa_engine_module, _engine_load_error
    if _qa_engine_module is not None:
        return _qa_engine_module
    try:
        # 把 repo 根加到 sys.path，让 scripts 可被 import
        import sys
        REPO_ROOT = Path(__file__).resolve().parent.parent.parent
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
        from scripts import qa_engine  # noqa
        _qa_engine_module = qa_engine
        return _qa_engine_module
    except Exception as e:
        _engine_load_error = str(e)
        logger.error(f"加载 qa_engine 失败: {e}")
        return None


# ============================================================
# 端点
# ============================================================

@router.post("/", response_model=QAResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def qa(
    request: QARequest,
    _auth: Annotated[bool, Depends(verify_api_key)],
):
    """
    RAG 智能问答

    - **query**: 用户问题
    - **use_llm_intent**: 是否用 LLM 做意图分类（精度更高但更慢）
    - **evaluate**: 是否做二阶段质量评估
    - **top_k**: 检索 top-k 文档片段（1-20）
    - **save**: 是否保存到 outputs/qa/
    """
    start = time.time()
    qa_engine = get_qa_engine()
    if qa_engine is None:
        raise HTTPException(
            status_code=503,
            detail=f"RAG 引擎不可用: {_engine_load_error or '未知错误'}",
        )

    # 拿 LLM 客户端（如果可用）
    client = None
    if os.getenv("API_KEY") or os.getenv("ANTHROPIC_API_KEY"):
        try:
            from api.services import get_chat_client  # type: ignore
            client = get_chat_client()
        except Exception:
            try:
                # fallback: 走 scripts/api_client
                from scripts.api_client import chat as _client
                client = _client
            except Exception as e:
                logger.warning(f"未配置 LLM 客户端: {e}")

    try:
        result = qa_engine.ask(
            request.query,
            use_llm_intent=request.use_llm_intent,
            evaluate=request.evaluate,
            client=client,
        )
    except Exception as e:
        logger.error(f"qa_engine.ask 异常: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"问答失败: {e}")

    # 转成 response
    sources = [
        SourceItem(
            path=h.chunk.doc_path,
            title=h.chunk.doc_title,
            section=h.chunk.section,
            score=round(h.score, 3),
        )
        for h in result.hits[:request.top_k]
    ]

    saved_path = None
    if request.save and not result.error and not result.answer.startswith("❌"):
        try:
            qa_file = qa_engine.save_qa_to_wiki(result)
            saved_path = str(qa_file.relative_to(Path(__file__).resolve().parent.parent.parent))
        except Exception as e:
            logger.warning(f"保存问答失败: {e}")

    return QAResponse(
        query=result.query,
        intent=result.intent,
        entities=result.entities,
        confidence=result.confidence,
        answer=result.answer,
        sources=sources,
        used_template=result.used_template,
        elapsed_ms=result.elapsed_ms,
        quality_scores=result.quality_scores,
        saved_path=saved_path,
        error=result.error,
    )


@router.get("/health")
async def health_check():
    """RAG 引擎健康检查"""
    qa_engine = get_qa_engine()
    if qa_engine is None:
        return {
            "status": "unavailable",
            "error": _engine_load_error,
        }

    # 检查 chunk 索引
    try:
        chunks = qa_engine.ensure_index(force_rebuild=False)
        return {
            "status": "healthy",
            "indexed_chunks": len(chunks),
            "templates_loaded": True,
            "llm_available": bool(os.getenv("API_KEY") or os.getenv("ANTHROPIC_API_KEY")),
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
        }


@router.post("/evaluate")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def evaluate(
    eval_set_path: str = Query(default="evaluation/qa_eval.jsonl"),
    _auth: Annotated[bool, Depends(verify_api_key)],
):
    """
    在 evaluation/qa_eval.jsonl 上跑批量评估

    JSONL 格式（每行）:
    {
      "query": "什么是新质生产力？",
      "expected_intent": "concept_explain",
      "expected_keywords": ["新质", "生产力"]
    }

    返回每条用例的 intent 分类是否正确、检索命中率、整体指标。
    """
    qa_engine = get_qa_engine()
    if qa_engine is None:
        raise HTTPException(status_code=503, detail="qa_engine 不可用")

    REPO_ROOT = Path(__file__).resolve().parent.parent.parent
    eval_path = REPO_ROOT / eval_set_path
    if not eval_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"评估集不存在: {eval_set_path}（示例格式见 evaluation/qa_eval.jsonl.example）",
        )

    import json
    cases = []
    with open(eval_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))

    if not cases:
        raise HTTPException(status_code=400, detail="评估集为空")

    chunks = qa_engine.ensure_index(force_rebuild=False)
    if not chunks:
        raise HTTPException(status_code=500, detail="chunk 索引为空")

    # 跑评估
    from qa_engine import BM25Index, extract_keywords
    index = BM25Index(chunks)

    results = []
    intent_correct = 0
    retrieval_hit = 0
    for case in cases:
        query = case["query"]
        expected_intent = case.get("expected_intent")
        expected_keywords = case.get("expected_keywords", [])

        # 意图分类
        info = qa_engine.classify_intent_rule_based(query)
        intent_ok = (expected_intent is None) or (info["intent"] == expected_intent)
        if intent_ok:
            intent_correct += 1

        # 检索
        hits = index.search(query, keywords=info["entities"] or extract_keywords(query), top_k=5)
        # 命中判定：top-5 任一 chunk 含 expected_keywords 中任一词
        kw_hit = False
        for h in hits[:5]:
            text = (h.chunk.doc_title + h.chunk.section + h.chunk.text).lower()
            if any(kw.lower() in text for kw in expected_keywords):
                kw_hit = True
                break
        if kw_hit:
            retrieval_hit += 1

        results.append({
            "query": query,
            "expected_intent": expected_intent,
            "actual_intent": info["intent"],
            "intent_correct": intent_ok,
            "retrieval_hit": kw_hit,
            "top_score": round(hits[0].score, 3) if hits else 0,
        })

    metrics = {
        "total": len(cases),
        "intent_accuracy": round(intent_correct / len(cases), 3) if cases else 0,
        "retrieval_hit_at_5": round(retrieval_hit / len(cases), 3) if cases else 0,
    }

    return {
        "metrics": metrics,
        "results": results,
    }
