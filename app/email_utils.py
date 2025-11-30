import os
import io
from email.message import EmailMessage
from aiosmtplib import send
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


async def send_invoice_email(smtp_config: dict, to_email: str, subject: str, body: str, pdf_bytes: bytes, filename: str = "invoice.pdf"):
    msg = EmailMessage()
    msg["From"] = smtp_config.get("SMTP_FROM") or smtp_config.get("SMTP_USERNAME")
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=filename)

    await send(msg, hostname=smtp_config.get("SMTP_HOST"), port=int(smtp_config.get("SMTP_PORT", 587)), username=smtp_config.get("SMTP_USERNAME"), password=smtp_config.get("SMTP_PASSWORD"), start_tls=True)


def generate_invoice_pdf_bytes(purchase, items):
    """Generate a simple invoice PDF and return bytes"""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    width, height = letter
    x = 50
    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, "Invoice")
    c.setFont("Helvetica", 10)
    y -= 30
    c.drawString(x, y, f"Customer: {purchase.customer_email}")
    y -= 20
    c.drawString(x, y, f"Invoice ID: {purchase.id}")
    y -= 20
    c.drawString(x, y, f"Date: {purchase.created_at}")
    y -= 30
    c.drawString(x, y, "Items:")
    y -= 20
    for it in items:
        c.drawString(x, y, f"{it.quantity} x {it.product_name} @ {it.unit_price:.2f} = {it.line_total:.2f}")
        y -= 15
        if y < 80:
            c.showPage()
            y = height - 50
    y -= 10
    c.drawString(x, y, f"Subtotal: {purchase.subtotal:.2f}")
    y -= 15
    c.drawString(x, y, f"Tax: {purchase.tax:.2f}")
    y -= 15
    c.drawString(x, y, f"Total: {purchase.total:.2f}")
    y -= 15
    c.drawString(x, y, f"Paid: {purchase.paid_amount:.2f}")
    y -= 15
    c.drawString(x, y, f"Change: {purchase.change_amount:.2f}")

    c.save()
    buf.seek(0)
    return buf.read()
