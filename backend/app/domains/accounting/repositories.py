from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.repository import BaseRepository
from app.domains.accounting.models import (
    AccountingClientCompany,
    AccountingDocument,
    AccountingExportBatch,
    AccountingExportItem,
    AccountingOcrJob,
    AccountingOcrField,
    AccountingOcrResult,
)


class AccountingClientCompanyRepository(BaseRepository[AccountingClientCompany]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AccountingClientCompany)

    async def get_by_tax_code(
        self, organization_id: str, tax_code: str
    ) -> AccountingClientCompany | None:
        return await self.session.scalar(
            select(AccountingClientCompany).where(
                AccountingClientCompany.organization_id == organization_id,
                AccountingClientCompany.tax_code == tax_code,
            )
        )


class AccountingDocumentRepository(BaseRepository[AccountingDocument]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AccountingDocument)

    async def list_for_org(
        self,
        organization_id: str,
        *,
        status: str | None = None,
        client_company_id: str | None = None,
        accounting_period: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AccountingDocument]:
        statement = (
            select(AccountingDocument)
            .where(AccountingDocument.organization_id == organization_id)
            .order_by(AccountingDocument.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if status:
            statement = statement.where(AccountingDocument.status == status)
        if client_company_id:
            statement = statement.where(
                AccountingDocument.client_company_id == client_company_id
            )
        if accounting_period:
            statement = statement.where(
                AccountingDocument.accounting_period == accounting_period
            )
        result = await self.session.scalars(statement)
        return list(result.all())

    async def get_by_invoice_identity(
        self,
        *,
        organization_id: str,
        seller_tax_code: str,
        invoice_number: str,
        invoice_symbol: str,
        invoice_date: str,
        total_amount: str,
    ) -> AccountingDocument | None:
        return await self.session.scalar(
            select(AccountingDocument).where(
                AccountingDocument.organization_id == organization_id,
                AccountingDocument.seller_tax_code == seller_tax_code,
                AccountingDocument.invoice_number == invoice_number,
                AccountingDocument.invoice_symbol == invoice_symbol,
                AccountingDocument.invoice_date == invoice_date,
                AccountingDocument.total_amount == total_amount,
            )
        )


class AccountingOcrJobRepository(BaseRepository[AccountingOcrJob]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AccountingOcrJob)


class AccountingOcrResultRepository(BaseRepository[AccountingOcrResult]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AccountingOcrResult)

    async def get_latest_for_document(
        self, organization_id: str, document_id: str
    ) -> AccountingOcrResult | None:
        return await self.session.scalar(
            select(AccountingOcrResult)
            .where(
                AccountingOcrResult.organization_id == organization_id,
                AccountingOcrResult.document_id == document_id,
            )
            .order_by(AccountingOcrResult.created_at.desc())
            .limit(1)
        )


class AccountingOcrFieldRepository(BaseRepository[AccountingOcrField]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AccountingOcrField)

    async def list_for_result(
        self, organization_id: str, result_id: str
    ) -> list[AccountingOcrField]:
        result = await self.session.scalars(
            select(AccountingOcrField)
            .where(
                AccountingOcrField.organization_id == organization_id,
                AccountingOcrField.result_id == result_id,
            )
            .order_by(AccountingOcrField.field_key.asc())
        )
        return list(result.all())


class AccountingExportBatchRepository(BaseRepository[AccountingExportBatch]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AccountingExportBatch)


class AccountingExportItemRepository(BaseRepository[AccountingExportItem]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AccountingExportItem)

    async def list_for_batch(
        self, organization_id: str, batch_id: str
    ) -> list[AccountingExportItem]:
        result = await self.session.scalars(
            select(AccountingExportItem).where(
                AccountingExportItem.organization_id == organization_id,
                AccountingExportItem.batch_id == batch_id,
            )
        )
        return list(result.all())
