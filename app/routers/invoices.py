from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.invoice import (
    InvoiceCreateRequest,
    InvoiceResponse,
    InvoiceStatistics,
    InvoiceUpdateRequest,
)
from app.services import email_service, invoice_service, pdf_service

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("/statistics", response_model=InvoiceStatistics)
async def get_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await invoice_service.get_statistics(db, current_user.id)


@router.get("", response_model=list[InvoiceResponse])
async def list_invoices(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    invoices = await invoice_service.list_invoices(db, current_user.id, status_filter)
    return [InvoiceResponse.from_orm_model(inv) for inv in invoices]


@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    data: InvoiceCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    invoice = await invoice_service.create_invoice(db, data, current_user.id)
    return InvoiceResponse.from_orm_model(invoice)


@router.get("/{id}", response_model=InvoiceResponse)
async def get_invoice(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    invoice = await invoice_service.get_by_id(db, id, current_user.id)
    return InvoiceResponse.from_orm_model(invoice)


@router.put("/{id}", response_model=InvoiceResponse)
async def update_invoice(
    id: str,
    data: InvoiceUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    invoice = await invoice_service.update_invoice(db, id, data, current_user.id)
    return InvoiceResponse.from_orm_model(invoice)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await invoice_service.delete_invoice(db, id, current_user.id)


@router.patch("/{id}/mark-paid", response_model=InvoiceResponse)
async def mark_paid(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    invoice = await invoice_service.mark_as_paid(db, id, current_user.id)
    return InvoiceResponse.from_orm_model(invoice)


@router.post("/{id}/duplicate", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_invoice(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    invoice = await invoice_service.duplicate_invoice(db, id, current_user.id)
    return InvoiceResponse.from_orm_model(invoice)


@router.post("/{id}/send-email")
async def send_invoice_email(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    invoice = await invoice_service.get_by_id(db, id, current_user.id)
    invoice_response = InvoiceResponse.from_orm_model(invoice)
    return email_service.send_invoice_email(invoice_response)


@router.get("/{id}/pdf")
async def download_pdf(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    invoice = await invoice_service.get_by_id(db, id, current_user.id)
    invoice_response = InvoiceResponse.from_orm_model(invoice)
    pdf_bytes = pdf_service.generate_invoice_pdf(invoice_response)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=invoice-{id}.pdf"},
    )
