"""
East-lake Knowledge Base API
Main FastAPI application
"""
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from api.config import settings
from api.models import HealthResponse, ErrorResponse
from api.routes import search, graph, stats
from api.services import get_github_service, get_vector_store

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    logger.info("Starting East-lake Knowledge Base API")
    logger.info(f"App: {settings.app_name} v{settings.app_version}")

    # Initialize services
    try:
        github_service = get_github_service()
        vector_store = get_vector_store()

        # Index documents on startup
        logger.info("Indexing documents...")
        documents = github_service.get_all_documents()
        if documents:
            vector_store.add_documents(documents)
            logger.info(f"Indexed {len(documents)} documents")

    except Exception as e:
        logger.warning(f"Failed to initialize services: {e}")

    yield

    logger.info("Shutting down East-lake Knowledge Base API")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered knowledge base API with semantic search",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include routers
app.include_router(search.router)
app.include_router(graph.router)
app.include_router(stats.router)


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - API health check"""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.utcnow(),
        components={
            "api": "ok",
            "github": "ok",
            "vector_store": "ok",
        },
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.utcnow(),
        components={
            "api": "ok",
            "github": "ok",
            "vector_store": "ok",
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail=str(exc),
            code=500,
        ).model_dump(),
    )


# Development server entry point
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )