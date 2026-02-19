import base64

import resend

from app.config import settings
from app.schemas.invoice import InvoiceResponse


def send_invoice_email(invoice: InvoiceResponse) -> dict:
    """Send invoice PDF as email attachment via Resend."""
    if not settings.RESEND_API_KEY:
        raise ValueError("RESEND_API_KEY is not configured")

    from app.services.pdf_service import generate_invoice_pdf

    resend.api_key = settings.RESEND_API_KEY
    pdf_bytes = generate_invoice_pdf(invoice)

    params = {
        "from": settings.EMAIL_FROM,
        "to": [invoice.client_email],
        "subject": f"Invoice {invoice.id} from {invoice.sender_address.city}",
        "html": (
            f"<p>Hi {invoice.client_name},</p>"
            f"<p>Please find attached invoice <strong>{invoice.id}</strong> "
            f"for <strong>${invoice.total}</strong>.</p>"
            f"<p>Payment is due by <strong>{invoice.payment_due}</strong>.</p>"
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
