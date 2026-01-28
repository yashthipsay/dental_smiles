from .pdf import generate_prescription_pdf
from .whatsapp import send_whatsapp_document

def send_pdf_on_whatsapp(prescription):
    pdf = generate_prescription_pdf(prescription)

    success, message = send_whatsapp_document(
        phone_number = prescription.user.phone_number,
        pdf_bytes=pdf,
        filename=f"prescription_{prescription.id}.pdf",
    )

    return success, message