import base64
from html import escape

import resend
from fastapi import HTTPException, status

from app.config import settings
from app.schemas.invoice import InvoiceResponse


def send_invoice_email(invoice: InvoiceResponse) -> dict:
    """Send invoice PDF as email attachment via Resend."""
    if not settings.RESEND_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email service is not configured",
        )

    from app.services.pdf_service import generate_invoice_pdf

    resend.api_key = settings.RESEND_API_KEY
    pdf_bytes = generate_invoice_pdf(invoice)

    safe_name = escape(invoice.client_name)
    safe_id = escape(str(invoice.id))
    safe_total = escape(str(invoice.total))
    safe_due = escape(str(invoice.payment_due))
    safe_city = escape(str(invoice.sender_address.city))

    params = {
        "from": settings.EMAIL_FROM,
        "to": [invoice.client_email],
        "subject": f"Invoice {safe_id} from {safe_city}",
        "html": (
            f"<p>Hi {safe_name},</p>"
            f"<p>Please find attached invoice <strong>{safe_id}</strong> "
            f"for <strong>${safe_total}</strong>.</p>"
            f"<p>Payment is due by <strong>{safe_due}</strong>.</p>"
            f"<p>Thank you for your business!</p>"
        ),
        "attachments": [
            {
                "filename": f"invoice-{invoice.id}.pdf",
                "content": base64.b64encode(pdf_bytes).decode("utf-8"),
                "content_type": "application/pdf",
            }
        ],
    }

    response = resend.Emails.send(params)
    return {"message": "Invoice sent successfully", "email_id": response["id"]}
