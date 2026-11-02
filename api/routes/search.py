"""
Search Routes - Semantic search endpoint
"""
import time
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi.security import APIKeyHeader

from api.models import SearchRequest, SearchResponse, SearchResult, DocumentRef
from api.services import get_github_service, get_vector_store
from api.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
api_key_header = APIKeyHeader(name=settings.api_key_header, auto_error=False)


async def verify_api_key(api_key: Annotated[str | None, Depends(api_key_header)]):
    """Verify API key"""
    if settings.admin_api_key and api_key != settings.admin_api_key:
        # For now, allow requests without key in development
        if settings.debug or not settings.admin_api_key:
            return True
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True


@router.post("/", response_model=SearchResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def search(
    request: SearchRequest,
    _auth: Annotated[bool, Depends(verify_api_key)],
):
    """
    Perform semantic search on the knowledge base

    - **query**: Search query text
    - **top_k**: Number of results to return (default: 5)
    - **category**: Filter by category (optional)
    - **tags**: Filter by tags (optional)
    """
    start_time = time.time()

    try:
        # Get search results from vector store
        vector_store = get_vector_store()
        results = vector_store.search(request.query, request.top_k)

        # If no results from vector store, use GitHub search as fallback
        if not results:
            github_service = get_github_service()
            documents = github_service.get_all_documents()

            # Simple keyword search as fallback
            query_lower = request.query.lower()
            for doc in documents:
                if query_lower in doc["content"].lower():
                    results.append({
                        **doc,
                        "score": 0.5,
                        "distance": 1.0,
                    })
                    if len(results) >= request.top_k:
                        break

        # Build response
        search_results = []
        for result in results:
            # Build GitHub URL
            url = f"https://github.com/{settings.github_owner}/{settings.github_repo}/blob/main/{result['path']}"

            search_results.append(SearchResult(
                document=DocumentRef(
                    path=result["path"],
                    title=result.get("title", result["path"]),
                    url=url,
                ),
                chunk=result.get("content", result.get("path", "")),
                score=result.get("score", 0),
            ))

        took_ms = (time.time() - start_time) * 1000

        return SearchResponse(
            query=request.query,
            results=search_results,
            total=len(search_results),
            took_ms=took_ms,
        )

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/health")
async def health_check():
    """Check search service health"""
    try:
        vector_store = get_vector_store()
        doc_count = len(vector_store.metadata) if vector_store.metadata else 0

        return {
            "status": "healthy",
            "indexed_documents": doc_count,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }