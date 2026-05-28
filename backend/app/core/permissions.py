from enum import StrEnum


class Permission(StrEnum):
    ADMIN_ALL = "*"
    ACCOUNTING_READ = "accounting:read"
    ACCOUNTING_WRITE = "accounting:write"
    DASHBOARD_READ = "dashboard:read"
    AI_MANAGE = "ai:manage"
    USER_MANAGE = "user:manage"
    AUDIT_READ = "audit:read"


ROLE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    "admin": (Permission.ADMIN_ALL.value,),
    "employee": (
        Permission.ACCOUNTING_READ.value,
        Permission.ACCOUNTING_WRITE.value,
        Permission.DASHBOARD_READ.value,
    ),
}


def has_permission(principal_permissions: tuple[str, ...], required: tuple[str, ...]) -> bool:
    if Permission.ADMIN_ALL.value in principal_permissions:
        return True
    return all(permission in principal_permissions for permission in required)
