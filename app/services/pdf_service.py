from jinja2 import Environment, FileSystemLoader

from app.schemas.invoice import InvoiceResponse

env = Environment(loader=FileSystemLoader("templates"))


def generate_invoice_pdf(invoice: InvoiceResponse) -> bytes:
    # Lazy import so WeasyPrint doesn't crash the app on startup
    # if system libraries (pango, gobject) aren't available
    from weasyprint import HTML

    template = env.get_template("invoice.html")
    html_str = template.render(invoice=invoice)
    pdf_bytes = HTML(string=html_str).write_pdf()
    return pdf_bytes
