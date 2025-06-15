from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import structlog
from typing import Dict
from pathlib import Path

from app.core.config import settings
from app.core.database import init_db, close_db
from app.api import auth, rag
from app.core.logging import setup_logging

# Setup logging
setup_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    await logger.ainfo("app_startup", version=settings.app_version)
    await init_db()
    
    yield
    
    # Shutdown
    await close_db()
    await logger.ainfo("app_shutdown")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(rag.router)

# Mount static files if directory exists
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root():
    """Serve the web interface"""
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version
    }


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    request_id = request.headers.get("X-Request-ID", "")
    
    with structlog.contextvars.bound_contextvars(
        request_id=request_id,
        path=request.url.path,
        method=request.method
    ):
        await logger.ainfo("request_started")
        response = await call_next(request)
        await logger.ainfo("request_completed", status_code=response.status_code)
        
    return response


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_config=None  # Use structlog instead
    )