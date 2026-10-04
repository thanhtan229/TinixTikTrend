from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.core.logging import logger, log_event
from app.core.exceptions import AppException
from app.api.health import router as health_router
from app.api.products import router as products_router
from app.api.trends import router as trends_router
from app.api.dashboard import router as dashboard_router
from app.api.crawler import router as crawler_router
from app.db.init_db import init_db
from app.scheduler.jobs import start_scheduler, shutdown_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    log_event("app_startup", f"Starting {settings.app_name} in {settings.app_env} mode (Region: {settings.tiktok_region})")
    yield
    shutdown_scheduler()
    log_event("app_shutdown", f"Shutting down {settings.app_name}")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="TikTok Shop Affiliate Trend Hunter API - Local Decision Support Engine",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if isinstance(settings.cors_origins, list) else [settings.cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver"])


@app.middleware("http")
async def local_write_origin(request: Request, call_next):
    origin = request.headers.get("origin")
    if request.method not in ("GET", "HEAD", "OPTIONS") and origin and origin not in settings.cors_origins:
        return JSONResponse(status_code=403, content={"detail": "Only the local application can trigger operations."})
    return await call_next(request)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": exc.__class__.__name__, "message": exc.message, "detail": exc.detail},
    )


# Include API Routers
app.include_router(health_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(trends_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(crawler_router, prefix="/api")


@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "docs_url": "/docs",
        "health_url": "/api/health",
    }
