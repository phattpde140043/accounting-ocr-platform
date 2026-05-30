import pytest
from fastapi import HTTPException

from app.core.auth_types import AuthPrincipal
from app.core.config import settings
from app.core.context import DemoHeaderAuthProvider, get_auth_provider
from app.core.session import decode_access_token, issue_access_token
from app.domains.platform.google_sso import (
    DemoGoogleTokenVerifier,
    GoogleAuthTokenVerifier,
    get_google_token_verifier,
)
from app.domains.platform.login_audit_service import LoginAuditService


@pytest.mark.asyncio
async def test_production_auth_rejects_missing_bearer_token(monkeypatch) -> None:
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "auth_mode", "google")

    with pytest.raises(HTTPException) as exc_info:
        await get_auth_provider(
            credentials=None,
            organization_id="org_injected",
            header_user_id="user_injected",
            role="admin",
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["code"] == "missing_access_token"


@pytest.mark.asyncio
async def test_local_demo_auth_allows_explicit_demo_headers(monkeypatch) -> None:
    monkeypatch.setattr(settings, "environment", "local")
    monkeypatch.setattr(settings, "auth_mode", "demo")

    provider = await get_auth_provider(
        credentials=None,
        organization_id="org_demo",
        header_user_id="user_admin",
        role="admin",
    )

    assert isinstance(provider, DemoHeaderAuthProvider)
    assert (await provider.authenticate()).organization_id == "org_demo"


def test_demo_google_verifier_is_not_allowed_in_production(monkeypatch) -> None:
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "auth_mode", "google")
    monkeypatch.setattr(settings, "google_token_verifier_mode", "demo")

    with pytest.raises(RuntimeError, match="only in local demo mode"):
        get_google_token_verifier()


def test_local_demo_mode_uses_demo_google_verifier(monkeypatch) -> None:
    monkeypatch.setattr(settings, "environment", "local")
    monkeypatch.setattr(settings, "auth_mode", "demo")
    monkeypatch.setattr(settings, "google_token_verifier_mode", "demo")

    assert isinstance(get_google_token_verifier(), DemoGoogleTokenVerifier)


@pytest.mark.asyncio
async def test_google_verifier_requires_verified_email(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.domains.platform.google_sso.google_id_token.verify_oauth2_token",
        lambda *_args: {
            "sub": "google_subject",
            "email": "accounting@example.com",
            "email_verified": False,
        },
    )

    with pytest.raises(HTTPException) as exc_info:
        await GoogleAuthTokenVerifier().verify_id_token("signed-google-id-token")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["code"] == "invalid_google_profile"


def test_issued_jwt_contains_backend_principal_claims() -> None:
    principal = AuthPrincipal(
        user_id="user_1",
        organization_id="org_1",
        role="employee",
        permissions=("accounting:write",),
    )

    token_payload = issue_access_token(principal)

    assert decode_access_token(token_payload["access_token"]) == principal


@pytest.mark.asyncio
async def test_successful_login_audit_contains_no_token() -> None:
    class FakeSession:
        def __init__(self) -> None:
            self.records = []
            self.committed = False

        def add(self, record) -> None:
            self.records.append(record)

        async def commit(self) -> None:
            self.committed = True

    session = FakeSession()

    await LoginAuditService(session).record_success(
        organization_id="org_1",
        user_id="user_1",
        ip_address="127.0.0.1",
        user_agent="pytest",
    )

    assert session.committed is True
    assert len(session.records) == 1
    assert session.records[0].result == "success"
    assert not hasattr(session.records[0], "id_token")
    assert not hasattr(session.records[0], "access_token")
