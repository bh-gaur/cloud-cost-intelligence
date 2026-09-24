"""
Main FastAPI Application Entry Point
Initializes middleware, health endpoints, CORS, database schemas, and v1 routers.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi import FastAPI, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.database.base import Base
from app.database.session import engine, SessionLocal, get_db
from app.api.v1 import v1_router
from app.schemas.envelope import ApiResponse
from app.providers.factory import get_cloud_provider

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cloud-cost-intelligence")


from app.database.migration import run_multi_tenancy_migration


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure tables exist and run multi-tenancy migration
    logger.info("Starting up %s (Demo Mode: %s)", settings.APP_NAME, settings.DEMO_MODE)
    if get_db not in app.dependency_overrides:
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as db:
            run_multi_tenancy_migration(db, engine=engine)
            if settings.DEMO_MODE:
                try:
                    from app.models.cost import CostRecord
                    has_records = db.query(CostRecord).first() is not None
                    if not has_records:
                        logger.info("Demo mode enabled & empty database detected. Seeding mock demo data...")
                        from scripts.seed_demo_data import seed
                        seed()
                except Exception as e:
                    logger.warning("Could not auto-seed demo data: %s", e)
    yield
    # Shutdown
    logger.info("Shutting down %s", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise-grade AWS Cloud Cost Intelligence and FinOps Optimization Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Exception Handlers ensuring uniform ApiResponse envelopes
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse.fail(
            code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
        ).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ApiResponse.fail(
            code="VALIDATION_ERROR",
            message="Request parameters failed schema validation.",
            details=exc.errors(),
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server exception: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ApiResponse.fail(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal error occurred.",
        ).model_dump(),
    )


# Health Check Endpoints (Section 52)
@app.get("/health", tags=["Health"])
def health_check():
    """Overall platform health check."""
    return ApiResponse.ok({
        "status": "healthy",
        "app": settings.APP_NAME,
        "demo_mode": settings.DEMO_MODE,
    })


@app.get("/health/db", tags=["Health"])
def database_health(db: Session = Depends(get_db)):
    """Database connectivity and query test."""
    try:
        db.execute(text("SELECT 1"))
        dialect_name = db.bind.dialect.name if db.bind else engine.dialect.name
        return ApiResponse.ok({"database": "connected", "engine": dialect_name})
    except Exception as e:
        return ApiResponse.fail(code="DATABASE_UNAVAILABLE", message=f"Database check failed: {str(e)}")


@app.get("/health/aws", tags=["Health"])
def cloud_health():
    """Cloud provider readiness test without leaking secrets."""
    provider = get_cloud_provider()
    test_result = provider.test_connection()
    return ApiResponse.ok({
        "provider": provider.get_provider_name(),
        "is_ready": test_result["is_connected"],
        "account_masked": test_result["account_id_masked"],
    })


# Mount API Version 1
app.include_router(v1_router)

