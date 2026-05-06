"""
Pydantic Models for API
"""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CategoryEnum(str, Enum):
    """Document category"""
    POLICY = "政策解读"
    TECH = "技术分析"
    PROJECT = "专项课题"
    VISIT = "领导拜访"
    INDUSTRY = "行业研究"
    OTHER = "其他"


class StatusEnum(str, Enum):
    """Document status"""
    DRAFT = "draft"
    REVIEW = "review"
    STABLE = "stable"


# Request Models
class SearchRequest(BaseModel):
    """Semantic search request"""
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)
    category: CategoryEnum | None = None
    tags: list[str] | None = None


class GraphRequest(BaseModel):
    """Knowledge graph query request"""
    node: str = Field(..., min_length=1)
    depth: int = Field(default=1, ge=1, le=3)


# Response Models
class DocumentRef(BaseModel):
    """Document reference"""
    path: str
    title: str
    url: str


class SearchResult(BaseModel):
    """Search result item"""
    document: DocumentRef
    chunk: str
    score: float
    highlights: list[str] | None = None


class SearchResponse(BaseModel):
    """Search response"""
    query: str
    results: list[SearchResult]
    total: int
    took_ms: float


class GraphNode(BaseModel):
    """Knowledge graph node"""
    id: str
    label: str
    type: str
    category: str | None = None


class GraphEdge(BaseModel):
    """Knowledge graph edge"""
    source: str
    target: str
    label: str | None = None


class GraphResponse(BaseModel):
    """Knowledge graph response"""
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class StatsResponse(BaseModel):
    """Statistics response"""
    total_documents: int
    total_concepts: int
    total_links: int
    categories: dict[str, int]
    tags: dict[str, int]
    recent_updates: list[dict[str, Any]]


class HealthResponse(BaseModel):
    """API health check"""
    status: str
    version: str
    timestamp: datetime
    components: dict[str, str]


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: str | None = None
    code: int = 400