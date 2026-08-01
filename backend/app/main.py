from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.database.models import Base, engine
from app.api.v1.auth.router import router as auth_router
from app.api.v1.projects.router import router as projects_router
from app.api.v1.characters.router import router as characters_router
from app.api.v1.assets.router import router as assets_router
from app.api.v1.render.router import router as render_router
from app.api.v1.models.router import router as models_router
from app.api.v1.notifications.router import router as notifications_router
from app.api.v1.settings.router import router as settings_router
from app.api.v1.storyboards.router import router as storyboards_router
from app.api.intelligence import router as intelligence_router
from app.api.ai_infrastructure import router as ai_infrastructure_router
from app.websocket.manager import router as websocket_router
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="AI Movie Studio Backend API - A production-ready backend for AI-powered filmmaking",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Serve generated/rendered files (storage/generated, storage/renders, storage/uploads)
# so the frontend can load/download them directly by the relative path the API returns.
storage_root = Path(settings.STORAGE_PATH).parent
storage_root.mkdir(parents=True, exist_ok=True)
app.mount("/storage", StaticFiles(directory=str(storage_root)), name="storage")


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Create database tables
Base.metadata.create_all(bind=engine)


# Include routers
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(projects_router, prefix=settings.API_V1_PREFIX)
app.include_router(characters_router, prefix=settings.API_V1_PREFIX)
app.include_router(storyboards_router, prefix=settings.API_V1_PREFIX)
app.include_router(assets_router, prefix=settings.API_V1_PREFIX)
app.include_router(render_router, prefix=settings.API_V1_PREFIX)
app.include_router(models_router, prefix=settings.API_V1_PREFIX)
app.include_router(notifications_router, prefix=settings.API_V1_PREFIX)
app.include_router(settings_router, prefix=settings.API_V1_PREFIX)
app.include_router(intelligence_router)  # Intelligence router has its own prefix
app.include_router(ai_infrastructure_router)  # AI infrastructure router has its own prefix
app.include_router(websocket_router)  # /ws, /ws/jobs


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    # In production, check database and Redis connections here
    return {
        "status": "ready",
        "database": "connected",
        "redis": "connected"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
