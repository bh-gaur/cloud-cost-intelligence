"""
FinOps AI Copilot & Optimization Advisor API Router
Provides real-time cloud waste analysis, anomaly explanations, and interactive FinOps chat.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.envelope import ApiResponse
from app.schemas.copilot import (
    FinOpsInsightsResponse,
    CopilotPromptRequest,
    CopilotChatResponse,
)
from app.services.copilot_service import FinOpsCopilotService
from app.auth.tenant_context import TenantContext, get_tenant_context

router = APIRouter(prefix="/copilot", tags=["FinOps AI Copilot"])


@router.get("/insights", response_model=ApiResponse[FinOpsInsightsResponse])
def get_copilot_insights(
    account_id: str = Query("all", description="AWS Account ID or 'all'"),
    db: Session = Depends(get_db),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    """Generates an executive FinOps intelligence brief, efficiency score, and prioritized savings pipeline."""
    service = FinOpsCopilotService(db, organization_id=tenant_ctx.organization_id)
    insights = service.generate_insights(account_id=account_id)
    return ApiResponse.ok(insights)


@router.post("/chat", response_model=ApiResponse[CopilotChatResponse])
def chat_with_copilot(
    request: CopilotPromptRequest,
    db: Session = Depends(get_db),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    """Processes natural language FinOps queries with contextual telemetry reasoning and remediation code."""
    service = FinOpsCopilotService(db, organization_id=tenant_ctx.organization_id)
    response = service.process_chat(query=request.query, account_id=request.account_id)
    return ApiResponse.ok(response)

