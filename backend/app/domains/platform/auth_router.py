from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db_session
from app.core.session import issue_access_token
from app.domains.platform.auth_membership_service import AuthMembershipService
from app.domains.platform.auth_schemas import (
    GoogleCallbackIn,
    GoogleCallbackOut,
    GoogleLoginOut,
    GoogleProfileOut,
    SessionTokenOut,
)
from app.domains.platform.google_sso import (
    GoogleTokenVerifier,
    get_google_token_verifier,
)
from app.domains.platform.login_audit_service import LoginAuditService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/google/login", response_model=GoogleLoginOut)
async def get_google_login_metadata() -> GoogleLoginOut:
    return GoogleLoginOut(
        provider="google",
        client_id=settings.google_client_id,
        scope=settings.google_oauth_scope,
        response_type="id_token",
        next_step="Send the Google ID token to POST /api/v1/auth/google/callback.",
    )


@router.post("/google/callback", response_model=GoogleCallbackOut)
async def handle_google_callback(
    payload: GoogleCallbackIn,
    request: Request,
    verifier: Annotated[GoogleTokenVerifier, Depends(get_google_token_verifier)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> GoogleCallbackOut:
    login_audit = LoginAuditService(session)
    try:
        profile = await verifier.verify_id_token(payload.id_token)
        principal = await AuthMembershipService(session).principal_from_google_profile(profile)
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, dict) else {}
        login_audit.record_rejection(reason=detail.get("code", "authentication_failed"))
        raise

    await login_audit.record_success(
        organization_id=principal.organization_id,
        user_id=principal.user_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    token_payload = issue_access_token(principal)
    return GoogleCallbackOut(
        profile=GoogleProfileOut(
            provider="google",
            subject=profile.subject,
            email=profile.email,
            name=profile.name,
            avatar_url=profile.avatar_url,
        ),
        session=SessionTokenOut(**token_payload),
        next_step="Use the returned bearer token in the Authorization header.",
    )
