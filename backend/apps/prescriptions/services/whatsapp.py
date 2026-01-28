import base64
from typing import Tuple

def send_whatsapp_document(
        phone_number: str,
        pdf_bytes: bytes,
        filename: str,
) -> Tuple[bool, str]:
    
    encoded_pdf = base64.b64encode(pdf_bytes).decode("utf-8")

    payload = {
        "to": phone_number,
        "type": "document",
        "document": {
            "filename": filename,
            "mime_type": "application/pdf",
            "data": encoded_pdf,
        },
    }

    # TODO: call WhatsApp provider API here
    # response = requests.post(...)

    return True, "Sent successfully"