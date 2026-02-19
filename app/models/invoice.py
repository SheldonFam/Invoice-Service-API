import uuid

from sqlalchemy import Column, Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String(10), primary_key=True)  # e.g. "INV-0001"
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(Date, nullable=False)
    payment_due = Column(Date, nullable=False)
    description = Column(String, nullable=False, default="")
    payment_terms = Column(Integer, nullable=False)  # 1 | 7 | 14 | 30
    client_name = Column(String, nullable=False, default="")
    client_email = Column(String, nullable=False, default="")
    status = Column(String, nullable=False, default="draft")  # draft | pending | paid

    # Sender address
    sender_street = Column(String, default="")
    sender_city = Column(String, default="")
    sender_post_code = Column(String, default="")
    sender_country = Column(String, default="")

    # Client address
    client_street = Column(String, default="")
    client_city = Column(String, default="")
    client_post_code = Column(String, default="")
    client_country = Column(String, default="")

    # Financials
    subtotal = Column(Numeric(10, 2), nullable=False, default=0)
    tax_rate = Column(Numeric(5, 2), nullable=False, default=0)  # percentage, e.g. 10.00
    tax_amount = Column(Numeric(10, 2), nullable=False, default=0)
    total = Column(Numeric(10, 2), nullable=False, default=0)

    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    owner = relationship("User", back_populates="invoices")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(String(10), ForeignKey("invoices.id"), nullable=False)
    name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)  # derived: quantity * price

    invoice = relationship("Invoice", back_populates="items")
