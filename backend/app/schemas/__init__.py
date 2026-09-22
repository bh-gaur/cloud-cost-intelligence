"""
Schemas Package
"""

from app.schemas.envelope import ApiResponse, ApiError, ApiMeta
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)
from app.schemas.cost import (
    CostRecordSchema,
    CostFilterParams,
    ServiceBreakdownItem,
    AccountBreakdownItem,
    RegionBreakdownItem,
    TagAnalysisResponse,
)
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    FinOpsKpisResponse,
    CostTrendPoint,
    CostTrendResponse,
)
from app.schemas.report import (
    ReportGenerateRequest,
    ReportResponse,
    ScheduleCreateRequest,
    ScheduleResponse,
)
from app.schemas.optimization import (
    OptimizationRecommendationResponse,
    PotentialSavingsSummary,
)
from app.schemas.alert import (
    AlertRuleCreateRequest,
    AlertRuleResponse,
    AnomalyEventResponse,
    BudgetResponse,
)
from app.schemas.integration import (
    AWSConnectionTestRequest,
    AWSConnectionTestResponse,
    NotificationTestRequest,
    NotificationTestResponse,
)

__all__ = [
    "ApiResponse",
    "ApiError",
    "ApiMeta",
    "UserRegisterRequest",
    "UserLoginRequest",
    "RefreshTokenRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "TokenResponse",
    "UserResponse",
    "CostRecordSchema",
    "CostFilterParams",
    "ServiceBreakdownItem",
    "AccountBreakdownItem",
    "RegionBreakdownItem",
    "TagAnalysisResponse",
    "DashboardSummaryResponse",
    "FinOpsKpisResponse",
    "CostTrendPoint",
    "CostTrendResponse",
    "ReportGenerateRequest",
    "ReportResponse",
    "ScheduleCreateRequest",
    "ScheduleResponse",
    "OptimizationRecommendationResponse",
    "PotentialSavingsSummary",
    "AlertRuleCreateRequest",
    "AlertRuleResponse",
    "AnomalyEventResponse",
    "BudgetResponse",
    "AWSConnectionTestRequest",
    "AWSConnectionTestResponse",
    "NotificationTestRequest",
    "NotificationTestResponse",
]

