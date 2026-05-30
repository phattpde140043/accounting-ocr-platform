from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_request_context, require_roles
from app.core.database import get_db_session
from app.domains.platform.admin_service import AdminUserService
from app.domains.platform.models import Organization
from app.domains.platform.schemas import (
    AuditEventOut,
    CreateUserIn,
    MeOut,
    OrganizationOut,
    UserOut,
)
from app.domains.shared.schemas import ListResponse, StatusResponse, build_offset_page_info

router = APIRouter(tags=["platform"])


@router.get("/me", response_model=MeOut)
async def get_me(
    context: Annotated[RequestContext, Depends(get_request_context)]
) -> MeOut:
    return MeOut(
        user_id=context.user_id,
        organization_id=context.organization_id,
        role=context.role,
        permissions=list(context.permissions),
    )


@router.get("/organizations", response_model=ListResponse[OrganizationOut])
async def list_organizations(
    context: Annotated[RequestContext, Depends(get_request_context)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    organization = await session.get(Organization, context.organization_id)
    if organization is None:
        return {"items": []}
    return {
        "items": [
            {
                "id": organization.id,
                "name": organization.name,
                "created_at": (
                    organization.created_at.isoformat()
                    if organization.created_at
                    else ""
                ),
            }
        ]
    }


@router.get("/admin/users", response_model=ListResponse[UserOut])
async def list_users(
    context: Annotated[RequestContext, Depends(require_roles("admin"))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    service = AdminUserService(session)
    items = await service.list_users(
        context.organization_id, limit=limit, offset=offset
    )
    return {
        "items": items,
        "page_info": build_offset_page_info(
            item_count=len(items), limit=limit, offset=offset
        ),
    }


@router.post("/admin/users", response_model=UserOut)
async def create_user(
    payload: CreateUserIn,
    context: Annotated[RequestContext, Depends(require_roles("admin"))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    service = AdminUserService(session)
    return await service.create_user(
        organization_id=context.organization_id,
        actor_user_id=context.user_id,
        payload=payload,
    )


@router.post("/admin/users/{user_id}/reset-password", response_model=StatusResponse)
async def reset_user_password(
    user_id: str,
    context: Annotated[RequestContext, Depends(require_roles("admin"))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    service = AdminUserService(session)
    await service.request_password_reset(
        organization_id=context.organization_id,
        actor_user_id=context.user_id,
        user_id=user_id,
    )
    return {"status": "reset_requested"}


@router.get("/admin/audit-events", response_model=ListResponse[AuditEventOut])
async def list_audit_events(
    context: Annotated[RequestContext, Depends(require_roles("admin"))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    service = AdminUserService(session)
    items = await service.list_audit_events(
        context.organization_id, limit=limit, offset=offset
    )
    return {
        "items": items,
        "page_info": build_offset_page_info(
            item_count=len(items), limit=limit, offset=offset
        ),
    }
