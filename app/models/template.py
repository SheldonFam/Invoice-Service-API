import uuid
from datetime import date

from sqlalchemy import Column, Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class InvoiceTemplate(Base):
    __tablename__ = "invoice_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False, default="")
    payment_terms = Column(Integer, nullable=False, default=30)
    tax_rate = Column(Numeric(5, 2), nullable=False, default=0)

    # Sender address (optional on templates)
    sender_street = Column(String, default="")
    sender_city = Column(String, default="")
    sender_post_code = Column(String, default="")
    sender_country = Column(String, default="")

    created_at = Column(Date, nullable=False, default=date.today)

    items = relationship("TemplateItem", back_populates="template", cascade="all, delete-orphan")
    owner = relationship("User", back_populates="templates")


class TemplateItem(Base):
    __tablename__ = "template_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(UUID(as_uuid=True), ForeignKey("invoice_templates.id"), nullable=False)
    name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)

    template = relationship("InvoiceTemplate", back_populates="items")
