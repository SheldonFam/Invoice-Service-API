import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(String(10), primary_key=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[date] = mapped_column(nullable=False)
    payment_due: Mapped[date] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    payment_terms: Mapped[int] = mapped_column(nullable=False)
    client_name: Mapped[str] = mapped_column(String, nullable=False, default="")
    client_email: Mapped[str] = mapped_column(String, nullable=False, default="")
    status: Mapped[str] = mapped_column(String, nullable=False, default="draft")

    # Sender address
    sender_street: Mapped[str] = mapped_column(String, default="")
    sender_city: Mapped[str] = mapped_column(String, default="")
    sender_post_code: Mapped[str] = mapped_column(String, default="")
    sender_country: Mapped[str] = mapped_column(String, default="")

    # Client address
    client_street: Mapped[str] = mapped_column(String, default="")
    client_city: Mapped[str] = mapped_column(String, default="")
    client_post_code: Mapped[str] = mapped_column(String, default="")
    client_country: Mapped[str] = mapped_column(String, default="")

    # Financials
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=0
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
    total: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )

    items: Mapped[list["InvoiceItem"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )
    owner: Mapped["User"] = relationship(back_populates="invoices")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    invoice_id: Mapped[str] = mapped_column(
        String(10), ForeignKey("invoices.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    invoice: Mapped["Invoice"] = relationship(back_populates="items")
