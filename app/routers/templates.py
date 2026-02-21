from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.invoice import (
    InvoiceTemplateCreate,
    InvoiceTemplateResponse,
    InvoiceTemplateUpdate,
    PaginatedResponse,
)
from app.services import template_service

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=PaginatedResponse[InvoiceTemplateResponse])
async def list_templates(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    templates, total = await template_service.list_templates(
        db, current_user.id, limit, offset
    )
    return PaginatedResponse(
        items=[InvoiceTemplateResponse.from_orm_model(t) for t in templates],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=InvoiceTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: InvoiceTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    template = await template_service.create_template(db, data, current_user.id)
    return InvoiceTemplateResponse.from_orm_model(template)


@router.get("/{id}", response_model=InvoiceTemplateResponse)
async def get_template(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    template = await template_service.get_template(db, id, current_user.id)
    return InvoiceTemplateResponse.from_orm_model(template)


@router.put("/{id}", response_model=InvoiceTemplateResponse)
async def update_template(
    id: UUID,
    data: InvoiceTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    template = await template_service.update_template(db, id, data, current_user.id)
    return InvoiceTemplateResponse.from_orm_model(template)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await template_service.delete_template(db, id, current_user.id)
