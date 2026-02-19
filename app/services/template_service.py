from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.template import InvoiceTemplate, TemplateItem
from app.schemas.invoice import InvoiceTemplateCreate, InvoiceTemplateUpdate


async def create_template(
    db: AsyncSession, data: InvoiceTemplateCreate, owner_id: UUID
) -> InvoiceTemplate:
    template = InvoiceTemplate(
        owner_id=owner_id,
        name=data.name,
        description=data.description,
        payment_terms=data.payment_terms,
        tax_rate=data.tax_rate,
        sender_street=data.sender_address.street if data.sender_address else "",
        sender_city=data.sender_address.city if data.sender_address else "",
        sender_post_code=data.sender_address.post_code if data.sender_address else "",
        sender_country=data.sender_address.country if data.sender_address else "",
    )
    for item in data.items:
        template.items.append(
            TemplateItem(name=item.name, quantity=item.quantity, price=item.price)
        )
    db.add(template)
    await db.commit()
    await db.refresh(template, attribute_names=["items"])
    return template


async def list_templates(db: AsyncSession, owner_id: UUID) -> list[InvoiceTemplate]:
    result = await db.execute(
        select(InvoiceTemplate)
        .where(InvoiceTemplate.owner_id == owner_id)
        .options(selectinload(InvoiceTemplate.items))
        .order_by(InvoiceTemplate.created_at.desc())
    )
    return list(result.scalars().all())


async def get_template(db: AsyncSession, template_id: UUID, owner_id: UUID) -> InvoiceTemplate:
    result = await db.execute(
        select(InvoiceTemplate)
        .where(InvoiceTemplate.id == template_id, InvoiceTemplate.owner_id == owner_id)
        .options(selectinload(InvoiceTemplate.items))
    )
    template = result.scalar_one_or_none()
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return template


async def update_template(
    db: AsyncSession, template_id: UUID, data: InvoiceTemplateUpdate, owner_id: UUID
) -> InvoiceTemplate:
    template = await get_template(db, template_id, owner_id)

    if data.name is not None:
        template.name = data.name
    if data.description is not None:
        template.description = data.description
    if data.payment_terms is not None:
        template.payment_terms = data.payment_terms
    if data.tax_rate is not None:
        template.tax_rate = data.tax_rate
    if data.sender_address is not None:
        template.sender_street = data.sender_address.street
        template.sender_city = data.sender_address.city
        template.sender_post_code = data.sender_address.post_code
        template.sender_country = data.sender_address.country
    if data.items is not None:
        for item in template.items:
            await db.delete(item)
        template.items.clear()
        for item in data.items:
            template.items.append(
                TemplateItem(name=item.name, quantity=item.quantity, price=item.price)
            )

    await db.commit()
    await db.refresh(template, attribute_names=["items"])
    return template


async def delete_template(db: AsyncSession, template_id: UUID, owner_id: UUID) -> None:
    template = await get_template(db, template_id, owner_id)
    await db.delete(template)
    await db.commit()
