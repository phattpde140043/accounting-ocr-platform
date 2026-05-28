from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.accounting.models import AccountingClientCompany, AccountingDocument
from app.domains.platform.models import (
    Membership,
    Organization,
    Permission,
    Role,
    RolePermission,
    User,
)


ORG_ID = "org_demo"
ADMIN_ID = "user_admin"
EMPLOYEE_ID = "user_employee"


async def add_if_missing(session: AsyncSession, model: type, record_id: str, **values):
    existing = await session.get(model, record_id)
    if existing is not None:
        return existing

    record = model(id=record_id, **values)
    session.add(record)
    return record


async def seed_demo_data(session: AsyncSession) -> None:
    await add_if_missing(
        session,
        Organization,
        ORG_ID,
        name="Accounting OCR Demo Organization",
        slug="accounting-ocr-demo",
        status="active",
    )

    await add_if_missing(
        session,
        User,
        ADMIN_ID,
        email="admin@example.com",
        name="Demo Admin",
        google_subject="google_admin_demo",
        is_active=True,
    )
    await add_if_missing(
        session,
        User,
        EMPLOYEE_ID,
        email="employee@example.com",
        name="Demo Employee",
        google_subject="google_employee_demo",
        is_active=True,
    )
    roles = [
        ("role_admin", "admin", "Admin"),
        ("role_employee", "employee", "Employee"),
    ]
    for role_id, key, name in roles:
        await add_if_missing(
            session,
            Role,
            role_id,
            organization_id=ORG_ID,
            key=key,
            name=name,
            description=f"Demo {name} role",
        )

    permissions = [
        ("perm_all", "*", "Full administrative access"),
        ("perm_accounting_write", "accounting:write", "Manage accounting intake"),
        ("perm_dashboard_read", "dashboard:read", "Read dashboards"),
        ("perm_ai_manage", "ai:manage", "Manage OCR providers and prompts"),
    ]
    for permission_id, key, description in permissions:
        await add_if_missing(
            session,
            Permission,
            permission_id,
            key=key,
            description=description,
        )

    role_permissions = [
        ("role_perm_admin_all", "role_admin", "perm_all"),
        ("role_perm_employee_accounting", "role_employee", "perm_accounting_write"),
        ("role_perm_employee_dashboard", "role_employee", "perm_dashboard_read"),
    ]
    for record_id, role_id, permission_id in role_permissions:
        await add_if_missing(
            session,
            RolePermission,
            record_id,
            role_id=role_id,
            permission_id=permission_id,
        )

    memberships = [
        ("membership_admin", ADMIN_ID, "role_admin"),
        ("membership_employee", EMPLOYEE_ID, "role_employee"),
    ]
    for record_id, user_id, role_id in memberships:
        await add_if_missing(
            session,
            Membership,
            record_id,
            organization_id=ORG_ID,
            user_id=user_id,
            role_id=role_id,
            status="active",
        )

    await add_if_missing(
        session,
        AccountingClientCompany,
        "client_acme",
        organization_id=ORG_ID,
        name="Cong ty TNHH Acme Viet Nam",
        tax_code="0312345678",
        address="Ho Chi Minh City",
    )
    await add_if_missing(
        session,
        AccountingDocument,
        "doc_invoice_demo",
        organization_id=ORG_ID,
        client_company_id="client_acme",
        document_type="invoice",
        category="sales",
        accounting_period="2026-05",
        file_name="invoice-demo.pdf",
        mime_type="application/pdf",
        status="uploaded",
        ocr_status="not_started",
        created_by_user_id=EMPLOYEE_ID,
    )

    await session.commit()
