"""
FinOps AI Copilot & Cost Advisor Schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CopilotPromptRequest(BaseModel):
    query: str = Field(..., description="Natural language question or command for the FinOps Copilot")
    account_id: Optional[str] = Field(None, description="Optional AWS Account ID filter")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Client page context")


class SavingsOpportunity(BaseModel):
    id: str
    title: str
    category: str
    service: str
    estimated_monthly_savings: float
    effort: str = Field("Low", description="Low, Medium, or High")
    risk: str = Field("Zero", description="Zero, Low, Medium, or High")
    remediation_command: Optional[str] = None
    description: str


class AnomalyDiagnosis(BaseModel):
    service: str
    detected_surge_pct: float
    estimated_impact: float
    root_cause_hypothesis: str
    recommended_action: str


class FinOpsInsightsResponse(BaseModel):
    health_score: int = Field(..., description="Overall FinOps Health & Efficiency Score (0-100)")
    total_monthly_spend: float
    potential_monthly_savings: float
    savings_percentage: float
    executive_summary: str
    top_opportunities: List[SavingsOpportunity]
    anomalies: List[AnomalyDiagnosis]
    quick_wins: List[str]
    tagging_compliance_pct: float


class CopilotChatResponse(BaseModel):
    reply: str
    suggested_actions: List[str] = Field(default_factory=list)
    relevant_opportunities: List[SavingsOpportunity] = Field(default_factory=list)
    remediation_snippet: Optional[str] = None

