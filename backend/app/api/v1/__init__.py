"""
API v1 Router Aggregator
"""

from fastapi import APIRouter
from app.api.v1.organizations import router as orgs_router
from app.api.v1.auth import router as auth_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.costs import router as costs_router
from app.api.v1.services import router as services_router
from app.api.v1.accounts import router as accounts_router
from app.api.v1.regions import router as regions_router
from app.api.v1.reports import router as reports_router
from app.api.v1.optimization import router as opt_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.aws import router as aws_router
from app.api.v1.integrations import router as integrations_router
from app.api.v1.admin import router as admin_router
from app.api.v1.members import router as members_router
from app.api.v1.health import router as health_router
from app.api.v1.tagging import router as tagging_router

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(health_router)
v1_router.include_router(orgs_router)
v1_router.include_router(members_router)
v1_router.include_router(auth_router)
v1_router.include_router(dashboard_router)
v1_router.include_router(costs_router)
v1_router.include_router(services_router)
v1_router.include_router(accounts_router)
v1_router.include_router(regions_router)
v1_router.include_router(reports_router)
v1_router.include_router(opt_router)
v1_router.include_router(alerts_router)
v1_router.include_router(notifications_router)
v1_router.include_router(integrations_router)
v1_router.include_router(aws_router)
v1_router.include_router(tagging_router)
v1_router.include_router(admin_router)
