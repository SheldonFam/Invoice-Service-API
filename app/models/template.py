import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class InvoiceTemplate(Base):
    __tablename__ = "invoice_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    payment_terms: Mapped[int] = mapped_column(nullable=False, default=30)
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=0
    )

    # Sender address (optional on templates)
    sender_street: Mapped[str] = mapped_column(String, default="")
    sender_city: Mapped[str] = mapped_column(String, default="")
    sender_post_code: Mapped[str] = mapped_column(String, default="")
    sender_country: Mapped[str] = mapped_column(String, default="")

    created_at: Mapped[date] = mapped_column(nullable=False, default=date.today)

    items: Mapped[list["TemplateItem"]] = relationship(
        back_populates="template", cascade="all, delete-orphan"
    )
    owner: Mapped["User"] = relationship(back_populates="templates")


class TemplateItem(Base):
    __tablename__ = "template_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoice_templates.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    template: Mapped["InvoiceTemplate"] = relationship(back_populates="items")
