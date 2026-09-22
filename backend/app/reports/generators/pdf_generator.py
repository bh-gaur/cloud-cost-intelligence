"""
PDF Report Generator
Converts HTML FinOps report templates into executive-ready PDF documents using xhtml2pdf.
"""

from io import BytesIO
from typing import Any, Dict
from xhtml2pdf import pisa
from app.reports.generators.html_generator import HTMLReportGenerator


class PDFReportGenerator:
    def __init__(self):
        self.html_generator = HTMLReportGenerator()

    def generate_bytes(self, data: Dict[str, Any]) -> bytes:
        """Renders HTML template and compiles it into PDF binary data."""
        html_content = self.html_generator.generate(data)
        pdf_stream = BytesIO()
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_stream)

        if pisa_status.err:
            raise RuntimeError(f"PDF generation failed with pisa error code: {pisa_status.err}")

        return pdf_stream.getvalue()

    def generate(self, data: Dict[str, Any]) -> bytes:
        return self.generate_bytes(data)
