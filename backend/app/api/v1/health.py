"""
Health Check API Router
"""

from fastapi import APIRouter
from sqlalchemy import text

from app.config.settings import settings
from app.database.session import engine
from app.schemas.envelope import ApiResponse
from app.providers.factory import get_cloud_provider

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=ApiResponse[dict])
def health_check():
    """Overall platform health check."""
    return ApiResponse.ok({
        "status": "healthy",
        "app": settings.APP_NAME,
        "demo_mode": settings.DEMO_MODE,
    })


@router.get("/db", response_model=ApiResponse[dict])
def database_health():
    """Database connectivity and query test."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return ApiResponse.ok({"database": "connected", "engine": engine.dialect.name})
    except Exception as e:
        return ApiResponse.fail(code="DATABASE_UNAVAILABLE", message=f"Database check failed: {str(e)}")


@router.get("/aws", response_model=ApiResponse[dict])
def cloud_health():
    """Cloud provider readiness test without leaking secrets."""
    provider = get_cloud_provider()
    test_result = provider.test_connection()
    return ApiResponse.ok({
        "provider": provider.get_provider_name(),
        "is_ready": test_result["is_connected"],
        "account_masked": test_result["account_id_masked"],
    })
