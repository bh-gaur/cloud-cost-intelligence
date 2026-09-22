"""
Standard API Response Envelope
Ensures consistent JSON responses across all v1 endpoints.
"""

from datetime import datetime, timezone
from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiError(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class ApiMeta(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version: str = "v1"
    demo_mode: bool = True
    page: Optional[int] = None
    page_size: Optional[int] = None
    total_count: Optional[int] = None
    total_pages: Optional[int] = None


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    error: Optional[ApiError] = None
    meta: ApiMeta = Field(default_factory=ApiMeta)

    @classmethod
    def ok(cls, data: T, meta: Optional[ApiMeta] = None) -> "ApiResponse[T]":
        return cls(
            success=True,
            data=data,
            error=None,
            meta=meta or ApiMeta(),
        )

    @classmethod
    def fail(
        cls,
        code: str,
        message: str,
        details: Optional[Any] = None,
        meta: Optional[ApiMeta] = None,
    ) -> "ApiResponse[None]":
        return cls(
            success=False,
            data=None,
            error=ApiError(code=code, message=message, details=details),
            meta=meta or ApiMeta(),
        )

