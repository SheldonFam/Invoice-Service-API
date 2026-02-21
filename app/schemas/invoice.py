from datetime import date
from decimal import Decimal
from typing import Generic, List, Literal, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

T = TypeVar("T")


class AddressSchema(BaseModel):
    street: str
    city: str
    post_code: str
    country: str

    @classmethod
    def from_flat(cls, prefix: str, obj: object) -> "AddressSchema":
        """Build from flat ORM fields like sender_street, sender_city, etc."""
        return cls(
            street=getattr(obj, f"{prefix}_street", "") or "",
            city=getattr(obj, f"{prefix}_city", "") or "",
            post_code=getattr(obj, f"{prefix}_post_code", "") or "",
            country=getattr(obj, f"{prefix}_country", "") or "",
        )


class InvoiceItemInput(BaseModel):
    name: str
    quantity: int = Field(gt=0)
    price: Decimal = Field(ge=0)


class InvoiceCreateRequest(BaseModel):
    created_at: date
    description: str
    payment_terms: Literal[1, 7, 14, 30]
    client_name: str
    client_email: EmailStr
    sender_address: AddressSchema
    client_address: AddressSchema
    items: List[InvoiceItemInput] = Field(min_length=1)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    submit_mode: Literal["draft", "pending"] = "pending"


class InvoiceUpdateRequest(BaseModel):
    created_at: Optional[date] = None
    description: Optional[str] = None
    payment_terms: Optional[Literal[1, 7, 14, 30]] = None
    client_name: Optional[str] = None
    client_email: Optional[EmailStr] = None
    sender_address: Optional[AddressSchema] = None
    client_address: Optional[AddressSchema] = None
    items: Optional[List[InvoiceItemInput]] = Field(default=None, min_length=1)
    tax_rate: Optional[Decimal] = Field(default=None, ge=0, le=100)


class InvoiceItemResponse(BaseModel):
    id: UUID
    name: str
    quantity: int
    price: Decimal
    total: Decimal


class InvoiceResponse(BaseModel):
    id: str
    created_at: date
    payment_due: date
    description: str
    payment_terms: int
    client_name: str
    client_email: str
    status: str
    sender_address: AddressSchema
    client_address: AddressSchema
    items: List[InvoiceItemResponse]
    subtotal: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    total: Decimal
    is_overdue: bool

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_model(cls, invoice) -> "InvoiceResponse":
        today = date.today()
        return cls(
            id=invoice.id,
            created_at=invoice.created_at,
            payment_due=invoice.payment_due,
            description=invoice.description,
            payment_terms=invoice.payment_terms,
            client_name=invoice.client_name,
            client_email=invoice.client_email,
            status=invoice.status,
            sender_address=AddressSchema.from_flat("sender", invoice),
            client_address=AddressSchema.from_flat("client", invoice),
            items=[
                InvoiceItemResponse.model_validate(item, from_attributes=True)
                for item in invoice.items
            ],
            subtotal=invoice.subtotal,
            tax_rate=invoice.tax_rate,
            tax_amount=invoice.tax_amount,
            total=invoice.total,
            is_overdue=invoice.status != "paid" and invoice.payment_due < today,
        )


# --- Statistics ---

class InvoiceStatistics(BaseModel):
    total_revenue: Decimal
    pending_amount: Decimal
    paid_this_month: Decimal
    overdue_count: int
    total_invoices: int


# --- Pagination ---

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    limit: int
    offset: int


# --- Invoice Templates ---

class TemplateItemInput(BaseModel):
    name: str
    quantity: int = Field(gt=0)
    price: Decimal = Field(ge=0)


class InvoiceTemplateCreate(BaseModel):
    name: str
    description: str = ""
    payment_terms: Literal[1, 7, 14, 30] = 30
    sender_address: Optional[AddressSchema] = None
    items: List[TemplateItemInput] = Field(default_factory=list)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100)


class InvoiceTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    payment_terms: Optional[Literal[1, 7, 14, 30]] = None
    sender_address: Optional[AddressSchema] = None
    items: Optional[List[TemplateItemInput]] = None
    tax_rate: Optional[Decimal] = Field(default=None, ge=0, le=100)


class TemplateItemResponse(BaseModel):
    id: UUID
    name: str
    quantity: int
    price: Decimal


class InvoiceTemplateResponse(BaseModel):
    id: UUID
    name: str
    description: str
    payment_terms: int
    sender_address: Optional[AddressSchema]
    items: List[TemplateItemResponse]
    tax_rate: Decimal
    created_at: date

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_model(cls, template) -> "InvoiceTemplateResponse":
        sender_address = (
            AddressSchema.from_flat("sender", template)
            if template.sender_street
            else None
        )
        return cls(
            id=template.id,
            name=template.name,
            description=template.description,
            payment_terms=template.payment_terms,
            sender_address=sender_address,
            items=[
                TemplateItemResponse.model_validate(item, from_attributes=True)
                for item in template.items
            ],
            tax_rate=template.tax_rate,
            created_at=template.created_at,
        )
