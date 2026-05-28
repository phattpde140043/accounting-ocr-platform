from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_request_context, require_roles
from app.core.database import get_db_session
from app.domains.dashboard.service import DashboardAggregationService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def get_summary(
    context: Annotated[RequestContext, Depends(get_request_context)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    service = DashboardAggregationService(session)
    return await service.get_summary(
        organization_id=context.organization_id,
        role=context.role,
    )


@router.get("/admin")
async def get_admin_dashboard(
    context: Annotated[RequestContext, Depends(require_roles("admin"))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    service = DashboardAggregationService(session)
    return await service.get_role_dashboard(
        organization_id=context.organization_id,
        role=context.role,
        focus="tenant operations, audit, users and workload",
    )


@router.get("/employee")
async def get_employee_dashboard(
    context: Annotated[RequestContext, Depends(require_roles("admin", "employee"))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    service = DashboardAggregationService(session)
    return await service.get_role_dashboard(
        organization_id=context.organization_id,
        role=context.role,
        focus="assigned accounting documents, OCR queue and review workload",
    )

