"""Import all SQLAlchemy models so Alembic can discover metadata."""

from app.domains.accounting.models import (  # noqa: F401
    AccountingClientCompany,
    AccountingDocument,
    AccountingExportBatch,
    AccountingExportItem,
    AccountingOcrField,
    AccountingOcrJob,
    AccountingOcrResult,
)
from app.domains.platform.models import (  # noqa: F401
    AuditEvent,
    LoginEvent,
    Membership,
    Organization,
    Permission,
    Role,
    RolePermission,
    User,
)
from app.domains.shared.models import BackgroundJob, FileAsset  # noqa: F401
