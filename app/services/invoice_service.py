from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.invoice import Invoice, InvoiceItem
from app.schemas.invoice import (
    InvoiceCreateRequest,
    InvoiceItemInput,
    InvoiceStatistics,
    InvoiceUpdateRequest,
)


# --- Helpers ---


def compute_payment_due(created_at: date, payment_terms: int) -> date:
    return created_at + timedelta(days=payment_terms)


def derive_totals(
    items: list[InvoiceItemInput], tax_rate: Decimal
) -> tuple[list[dict], Decimal, Decimal, Decimal]:
    """Returns (item_rows, subtotal, tax_amount, total)."""
    item_rows = [
        {
            "name": i.name,
            "quantity": i.quantity,
            "price": i.price,
            "total": (i.quantity * i.price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        }
        for i in items
    ]
    subtotal = sum(row["total"] for row in item_rows)
    subtotal = Decimal(str(subtotal)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    tax_amount = (subtotal * tax_rate / Decimal("100")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    total = subtotal + tax_amount
    return item_rows, subtotal, tax_amount, total


async def _next_sequential_id(db: AsyncSession) -> str:
    """Generate sequential invoice IDs like INV-0001, INV-0002, etc."""
    result = await db.execute(
        select(Invoice.id)
        .where(Invoice.id.like("INV-%"))
        .order_by(Invoice.id.desc())
        .limit(1)
    )
    last_id = result.scalar_one_or_none()
    if last_id is None:
        return "INV-0001"
    # Extract the number part and increment
    num = int(last_id.split("-")[1]) + 1
    return f"INV-{num:04d}"


def _check_not_paid(invoice: Invoice) -> None:
    """Raise 400 if invoice is paid — prevents editing/deleting paid invoices."""
    if invoice.status == "paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify a paid invoice",
        )


# --- CRUD ---


async def create_invoice(
    db: AsyncSession, data: InvoiceCreateRequest, owner_id: UUID
) -> Invoice:
    invoice_id = await _next_sequential_id(db)
    payment_due = compute_payment_due(data.created_at, data.payment_terms)
    item_rows, subtotal, tax_amount, total = derive_totals(data.items, data.tax_rate)

    invoice = Invoice(
        id=invoice_id,
        owner_id=owner_id,
        created_at=data.created_at,
        payment_due=payment_due,
        description=data.description,
        payment_terms=data.payment_terms,
        client_name=data.client_name,
        client_email=data.client_email,
        status=data.submit_mode,
        sender_street=data.sender_address.street,
        sender_city=data.sender_address.city,
        sender_post_code=data.sender_address.post_code,
        sender_country=data.sender_address.country,
        client_street=data.client_address.street,
        client_city=data.client_address.city,
        client_post_code=data.client_address.post_code,
        client_country=data.client_address.country,
        subtotal=subtotal,
        tax_rate=data.tax_rate,
        tax_amount=tax_amount,
        total=total,
    )

    for row in item_rows:
        invoice.items.append(
            InvoiceItem(
                name=row["name"],
                quantity=row["quantity"],
                price=row["price"],
                total=row["total"],
            )
        )

    db.add(invoice)
    await db.commit()
    await db.refresh(invoice, attribute_names=["items"])
    return invoice


async def list_invoices(
    db: AsyncSession, owner_id: UUID, status_filter: Optional[str] = None
) -> list[Invoice]:
    query = (
        select(Invoice)
        .where(Invoice.owner_id == owner_id)
        .options(selectinload(Invoice.items))
        .order_by(Invoice.id.desc())
    )
    if status_filter:
        statuses = [s.strip() for s in status_filter.split(",")]
        query = query.where(Invoice.status.in_(statuses))
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, invoice_id: str, owner_id: UUID) -> Invoice:
    result = await db.execute(
        select(Invoice)
        .where(Invoice.id == invoice_id, Invoice.owner_id == owner_id)
        .options(selectinload(Invoice.items))
    )
    invoice = result.scalar_one_or_none()
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return invoice


async def update_invoice(
    db: AsyncSession, invoice_id: str, data: InvoiceUpdateRequest, owner_id: UUID
) -> Invoice:
    invoice = await get_by_id(db, invoice_id, owner_id)
    _check_not_paid(invoice)

    if data.created_at is not None:
        invoice.created_at = data.created_at
    if data.description is not None:
        invoice.description = data.description
    if data.payment_terms is not None:
        invoice.payment_terms = data.payment_terms
    if data.client_name is not None:
        invoice.client_name = data.client_name
    if data.client_email is not None:
        invoice.client_email = data.client_email

    if data.sender_address is not None:
        invoice.sender_street = data.sender_address.street
        invoice.sender_city = data.sender_address.city
        invoice.sender_post_code = data.sender_address.post_code
        invoice.sender_country = data.sender_address.country

    if data.client_address is not None:
        invoice.client_street = data.client_address.street
        invoice.client_city = data.client_address.city
        invoice.client_post_code = data.client_address.post_code
        invoice.client_country = data.client_address.country

    if data.tax_rate is not None:
        invoice.tax_rate = data.tax_rate

    # Recalculate payment due
    invoice.payment_due = compute_payment_due(invoice.created_at, invoice.payment_terms)

    # Update items if provided
    if data.items is not None:
        for item in invoice.items:
            await db.delete(item)
        invoice.items.clear()

        item_rows, subtotal, tax_amount, total = derive_totals(
            data.items, Decimal(str(invoice.tax_rate))
        )
        invoice.subtotal = subtotal
        invoice.tax_amount = tax_amount
        invoice.total = total
        for row in item_rows:
            invoice.items.append(
                InvoiceItem(
                    name=row["name"],
                    quantity=row["quantity"],
                    price=row["price"],
                    total=row["total"],
                )
            )
    elif data.tax_rate is not None:
        # Tax rate changed but items didn't — recalculate from existing subtotal
        invoice.tax_amount = (
            invoice.subtotal * Decimal(str(invoice.tax_rate)) / Decimal("100")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        invoice.total = invoice.subtotal + invoice.tax_amount

    # Draft → Pending promotion
    if invoice.status == "draft":
        invoice.status = "pending"

    await db.commit()
    await db.refresh(invoice, attribute_names=["items"])
    return invoice


async def delete_invoice(db: AsyncSession, invoice_id: str, owner_id: UUID) -> None:
    invoice = await get_by_id(db, invoice_id, owner_id)
    _check_not_paid(invoice)
    await db.delete(invoice)
    await db.commit()


async def mark_as_paid(db: AsyncSession, invoice_id: str, owner_id: UUID) -> Invoice:
    invoice = await get_by_id(db, invoice_id, owner_id)
    invoice.status = "paid"
    await db.commit()
    await db.refresh(invoice, attribute_names=["items"])
    return invoice


# --- Duplicate ---


async def duplicate_invoice(db: AsyncSession, invoice_id: str, owner_id: UUID) -> Invoice:
    """Create a new draft invoice by copying all data from an existing one."""
    source = await get_by_id(db, invoice_id, owner_id)
    new_id = await _next_sequential_id(db)
    today = date.today()

    new_invoice = Invoice(
        id=new_id,
        owner_id=owner_id,
        created_at=today,
        payment_due=compute_payment_due(today, source.payment_terms),
        description=source.description,
        payment_terms=source.payment_terms,
        client_name=source.client_name,
        client_email=source.client_email,
        status="draft",
        sender_street=source.sender_street,
        sender_city=source.sender_city,
        sender_post_code=source.sender_post_code,
        sender_country=source.sender_country,
        client_street=source.client_street,
        client_city=source.client_city,
        client_post_code=source.client_post_code,
        client_country=source.client_country,
        subtotal=source.subtotal,
        tax_rate=source.tax_rate,
        tax_amount=source.tax_amount,
        total=source.total,
    )

    for item in source.items:
        new_invoice.items.append(
            InvoiceItem(
                name=item.name,
                quantity=item.quantity,
                price=item.price,
                total=item.total,
            )
        )

    db.add(new_invoice)
    await db.commit()
    await db.refresh(new_invoice, attribute_names=["items"])
    return new_invoice


# --- Statistics ---


async def get_statistics(db: AsyncSession, owner_id: UUID) -> InvoiceStatistics:
    today = date.today()

    # Total revenue (all paid invoices)
    result = await db.execute(
        select(func.coalesce(func.sum(Invoice.total), 0)).where(
            Invoice.owner_id == owner_id, Invoice.status == "paid"
        )
    )
    total_revenue = result.scalar_one()

    # Pending amount
    result = await db.execute(
        select(func.coalesce(func.sum(Invoice.total), 0)).where(
            Invoice.owner_id == owner_id, Invoice.status == "pending"
        )
    )
    pending_amount = result.scalar_one()

    # Paid this month
    result = await db.execute(
        select(func.coalesce(func.sum(Invoice.total), 0)).where(
            Invoice.owner_id == owner_id,
            Invoice.status == "paid",
            extract("year", Invoice.payment_due) == today.year,
            extract("month", Invoice.payment_due) == today.month,
        )
    )
    paid_this_month = result.scalar_one()

    # Overdue count
    result = await db.execute(
        select(func.count()).where(
            Invoice.owner_id == owner_id,
            Invoice.status != "paid",
            Invoice.payment_due < today,
        )
    )
    overdue_count = result.scalar_one()

    # Total invoices
    result = await db.execute(
        select(func.count()).where(Invoice.owner_id == owner_id)
    )
    total_invoices = result.scalar_one()

    return InvoiceStatistics(
        total_revenue=Decimal(str(total_revenue)),
        pending_amount=Decimal(str(pending_amount)),
        paid_this_month=Decimal(str(paid_this_month)),
        overdue_count=overdue_count,
        total_invoices=total_invoices,
    )
