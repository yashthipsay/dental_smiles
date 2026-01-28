from pathlib import Path
from django.conf import settings
from django.template.loader import render_to_string
from django.conf import settings
from django.template.loader import render_to_string
from weasyprint import HTML


def generate_prescription_pdf(prescription):
    image_path = Path(settings.STATIC_ROOT) / "prescriptions" / "template.png"
    background_image_url = f"file://{image_path}" if image_path.exists() else ""

    html = render_to_string(
        "prescriptions/prescription_pdf.html",
        {
            "prescription": prescription,
            "background_image": background_image_url
        }
    )

    pdf_bytes = HTML(string = html).write_pdf()
    return pdf_bytes

