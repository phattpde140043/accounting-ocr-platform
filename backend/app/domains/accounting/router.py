from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.context import RequestContext, get_request_context, require_roles
from app.core.database import get_db_session
from app.core.storage import LocalStorageProvider
from app.domains.accounting.client_company_service import AccountingClientCompanyService
from app.domains.accounting.document_service import AccountingDocumentService
from app.domains.accounting.export_service import AccountingExportService
from app.domains.accounting.lifecycle import AccountingDocumentStatus
from app.domains.accounting.ocr_service import AccountingOcrService
from app.domains.accounting.region_ocr_service import RegionOcrService
from app.domains.accounting.schemas import (
    AccountingDocumentOut,
    CreateExportBatchIn,
    ClientCompanyOut,
    CreateAccountingDocumentIn,
    CreateClientCompanyIn,
    OcrJobExecutionOut,
    OcrJobRequestOut,
    OcrResultOut,
    ExportBatchOut,
    RegionOcrIn,
    RegionOcrOut,
    UpdateOcrFieldIn,
)
from app.domains.shared.schemas import ListResponse, build_offset_page_info

router = APIRouter(prefix="/accounting", tags=["accounting"])


async def read_upload_content(file: UploadFile) -> bytes:
    max_bytes = settings.max_upload_size_bytes
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "code": "file_too_large",
                    "message": "Uploaded file exceeds the configured size limit.",
                },
            )
        chunks.append(chunk)
    return b"".join(chunks)


@router.get("/client-companies", response_model=ListResponse[ClientCompanyOut])
async def list_client_companies(
    context: Annotated[RequestContext, Depends(get_request_context)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    service = AccountingClientCompanyService(session)
    items = await service.list_client_companies(
        context.organization_id, limit=limit, offset=offset
    )
    return {
        "items": items,
        "page_info": build_offset_page_info(
            item_count=len(items), limit=limit, offset=offset
        ),
    }


@router.post("/client-companies", response_model=ClientCompanyOut)
async def create_client_company(
    payload: CreateClientCompanyIn,
    context: Annotated[RequestContext, Depends(require_roles("admin", "employee"))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    service = AccountingClientCompanyService(session)
    return await service.create_client_company(
        organization_id=context.organization_id,
        actor_user_id=context.user_id,
        payload=payload,
    )


@router.get("/documents", response_model=ListResponse[AccountingDocumentOut])
async def list_documents(
    context: Annotated[RequestContext, Depends(get_request_context)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    status: Annotated[str | None, Query()] = None,
    client_company_id: Annotated[str | None, Query()] = None,
    accounting_period: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    service = AccountingDocumentService(session)
    items = await service.list_documents(
        context.organization_id,
        status=status,
        client_company_id=client_company_id,
        accounting_period=accounting_period,
        limit=limit,
        offset=offset,
    )
    return {
        "items": items,
        "page_info": build_offset_page_info(
            item_count=len(items), limit=limit, offset=offset
        ),
    }


@router.post("/documents", response_model=AccountingDocumentOut)
async def create_document(
    payload: CreateAccountingDocumentIn,
    context: Annotated[RequestContext, Depends(require_roles("admin", "employee"))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    service = AccountingDocumentService(session)
    return await service.create_metadata_document(
        organization_id=context.organization_id,
        actor_user_id=context.user_id,
        payload=payload,
    )


@router.post("/documents/upload", response_model=AccountingDocumentOut)
async def upload_document(
    context: Annotated[RequestContext, Depends(require_roles("admin", "employee"))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    client_company_id: Annotated[str, Form()],
    accounting_period: Annotated[str, Form()],
    document_type: Annotated[str, Form()] = "invoice",
    category: Annotated[str, Form()] = "sales",
    file: UploadFile = File(...),
) -> dict:
    content = await read_upload_content(file)
    service = AccountingDocumentService(session)
    return await service.upload_document(
        organization_id=context.organization_id,
        actor_user_id=context.user_id,
        client_company_id=client_company_id,
        document_type=document_type,
        category=category,
        accounting_period=accounting_period,
        file_name=file.filename or "upload.bin",
        mime_type=file.content_type or "application/octet-stream",
        content=content,
        storage=LocalStorageProvider(),
    )


@router.post("/documents/{document_id}/ocr-jobs", response_model=OcrJobRequestOut)
async def request_ocr(
    document_id: str,
    context: Annotated[RequestContext, Depends(require_roles("admin", "employee"))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    service = AccountingOcrService(session)
    return await service.request_ocr(
        organization_id=context.organization_id,
        actor_user_id=context.user_id,
        document_id=document_id,
    )


@router.post("/documents/{document_id}/submit", response_model=AccountingDocumentOut)
async def submit_document(
    document_id: str,
    context: Annotated[RequestContext, Depends(require_roles("admin", "employee"))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    service = AccountingDocumentService(session)
    return await service.transition_document(
        organization_id=context.organization_id,
        actor_user_id=context.user_id,
        document_id=document_id,
        next_status=AccountingDocumentStatus.QUEUED.value,
    )


@router.post(
    "/documents/{document_id}/mark-needs-review",
    response_model=AccountingDocumentOut,
)
async def mark_document_needs_review(
    document_id: str,
    context: Annotated[RequestContext, Depends(require_roles("admin", "employee"))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    service = AccountingDocumentService(session)
    return await service.transition_document(
        organization_id=context.organization_id,
        actor_user_id=context.user_id,
        document_id=document_id,
        next_status=AccountingDocumentStatus.NEEDS_REVIEW.value,
    )


@router.post("/documents/{document_id}/approve", response_model=AccountingDocumentOut)
async def approve_document(
    document_id: str,
    context: Annotated[RequestContext, Depends(require_roles("admin", "employee"))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    service = AccountingDocumentService(session)
    return await service.transition_document(
        organization_id=context.organization_id,
        actor_user_id=context.user_id,
        document_id=document_id,
        next_status=AccountingDocumentStatus.APPROVED.value,
    )


@router.get("/documents/{document_id}/ocr-result", response_model=OcrResultOut)
async def get_ocr_result(
    document_id: str,
    context: Annotated[RequestContext, Depends(get_request_context)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    service = AccountingOcrService(session)
    return await service.get_result_for_document(
        organization_id=context.organization_id,
        document_id=document_id,
    )


@router.post("/ocr-jobs/{ocr_job_id}/execute", response_model=OcrJobExecutionOut)
async def execute_ocr_job(
    ocr_job_id: str,
    context: Annotated[RequestContext, Depends(require_roles("admin", "employee"))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    service = AccountingOcrService(session)
    return await service.execute_ocr_job(
        organization_id=context.organization_id,
        actor_user_id=context.user_id,
        ocr_job_id=ocr_job_id,
    )


@router.patch("/ocr-results/{result_id}/fields/{field_id}")
async def update_ocr_field(
    result_id: str,
    field_id: str,
    payload: UpdateOcrFieldIn,
    context: Annotated[RequestContext, Depends(require_roles("admin", "employee"))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    service = AccountingOcrService(session)
    return await service.update_field(
        organization_id=context.organization_id,
        actor_user_id=context.user_id,
        result_id=result_id,
        field_id=field_id,
        value=payload.value,
        version=payload.version,
    )


@router.post("/ocr-results/{result_id}/approve", response_model=OcrResultOut)
async def approve_ocr_result(
    result_id: str,
    context: Annotated[RequestContext, Depends(require_roles("admin", "employee"))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    service = AccountingOcrService(session)
    return await service.approve_result(
        organization_id=context.organization_id,
        actor_user_id=context.user_id,
        result_id=result_id,
    )


@router.post("/export-batches", response_model=ExportBatchOut)
async def create_export_batch(
    payload: CreateExportBatchIn,
    context: Annotated[RequestContext, Depends(require_roles("admin", "employee"))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    service = AccountingExportService(session)
    return await service.create_export_batch(
        organization_id=context.organization_id,
        actor_user_id=context.user_id,
        payload=payload,
    )


@router.get("/export-batches/{batch_id}/download")
async def download_export_batch(
    batch_id: str,
    context: Annotated[RequestContext, Depends(require_roles("admin", "employee"))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    service = AccountingExportService(session)
    artifact = await service.download_export_batch(
        organization_id=context.organization_id,
        actor_user_id=context.user_id,
        batch_id=batch_id,
    )
    return Response(
        content=artifact.content,
        media_type=artifact.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{artifact.file_name}"'
        },
    )


@router.post("/documents/{document_id}/region-ocr", response_model=RegionOcrOut)
async def process_region_ocr(
    document_id: str,
    payload: RegionOcrIn,
    context: Annotated[RequestContext, Depends(require_roles("admin", "employee"))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    service = RegionOcrService(session)
    return await service.process_regions(
        organization_id=context.organization_id,
        actor_user_id=context.user_id,
        document_id=document_id,
        payload=payload,
    )
