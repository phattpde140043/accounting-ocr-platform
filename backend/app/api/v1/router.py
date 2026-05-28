from fastapi import APIRouter

from app.domains.accounting.router import router as accounting_router
from app.domains.dashboard.router import router as dashboard_router
from app.domains.platform.auth_router import router as auth_router
from app.domains.platform.router import router as platform_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(platform_router)
api_router.include_router(accounting_router)
api_router.include_router(dashboard_router)
