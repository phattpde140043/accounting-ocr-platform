from sqlalchemy.ext.asyncio import AsyncSession

from app.core.model_mixins import new_id
from app.domains.accounting.models import AccountingClientCompany
from app.domains.accounting.repositories import AccountingClientCompanyRepository
from app.domains.accounting.schemas import CreateClientCompanyIn
from app.domains.platform.audit_service import AuditEventCreate, AuditLogService


class AccountingClientCompanyService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = AccountingClientCompanyRepository(session)
        self.audit_log = AuditLogService(session)

    async def list_client_companies(self, organization_id: str) -> list[dict]:
        companies = await self.repository.list_for_org(organization_id)
        return [self._serialize(company) for company in companies]

    async def create_client_company(
        self,
        *,
        organization_id: str,
        actor_user_id: str,
        payload: CreateClientCompanyIn,
    ) -> dict:
        company = AccountingClientCompany(
            id=new_id("client"),
            organization_id=organization_id,
            name=payload.name,
            tax_code=payload.tax_code,
        )
        await self.repository.add(company)
        await self.audit_log.record(
            AuditEventCreate(
                organization_id=organization_id,
                actor_user_id=actor_user_id,
                action="accounting.client_company_created",
                resource_type="client_company",
                resource_id=company.id,
                metadata={"tax_code": payload.tax_code},
            )
        )
        await self.session.commit()
        return self._serialize(company)

    def _serialize(self, company: AccountingClientCompany) -> dict:
        return {
            "id": company.id,
            "organization_id": company.organization_id,
            "name": company.name,
            "tax_code": company.tax_code,
            "created_at": company.created_at.isoformat() if company.created_at else "",
        }

