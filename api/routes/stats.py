"""
Stats Routes - Knowledge base statistics endpoints
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi.security import APIKeyHeader

from api.models import StatsResponse
from api.services import get_github_service
from api.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stats", tags=["stats"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
api_key_header = APIKeyHeader(name=settings.api_key_header, auto_error=False)


async def verify_api_key(api_key: Annotated[str | None, Depends(api_key_header)]):
    """Verify API key"""
    if settings.admin_api_key and api_key != settings.admin_api_key:
        if settings.debug or not settings.admin_api_key:
            return True
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True


@router.get("/", response_model=StatsResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def get_stats(
    _auth: Annotated[bool, Depends(verify_api_key)],
):
    """
    Get knowledge base statistics

    Returns document counts, category distribution, tag distribution, and recent updates.
    """
    try:
        github_service = get_github_service()
        stats = github_service.get_statistics()

        return StatsResponse(
            total_documents=stats.get("total_documents", 0),
            total_concepts=stats.get("total_concepts", 0),
            total_links=stats.get("total_links", 0),
            categories=stats.get("categories", {}),
            tags=stats.get("tags", {}),
            recent_updates=[],  # Would need GitHub API for this
        )

    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/categories")
async def get_categories(
    _auth: Annotated[bool, Depends(verify_api_key)],
):
    """Get category distribution"""
    try:
        github_service = get_github_service()
        stats = github_service.get_statistics()
        return {"categories": stats.get("categories", {})}
    except Exception as e:
        logger.error(f"Failed to get categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tags")
async def get_tags(
    limit: int = 20,
    _auth: Annotated[bool, Depends(verify_api_key)],
):
    """Get tag distribution"""
    try:
        github_service = get_github_service()
        stats = github_service.get_statistics()
        tags = stats.get("tags", {})
        sorted_tags = dict(sorted(tags.items(), key=lambda x: x[1], reverse=True)[:limit])
        return {"tags": sorted_tags, "total": len(tags)}
    except Exception as e:
        logger.error(f"Failed to get tags: {e}")
        raise HTTPException(status_code=500, detail=str(e))