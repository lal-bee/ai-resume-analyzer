from io import BytesIO

import pdfplumber


def parse_pdf_text(pdf_bytes: bytes) -> str:
    pages_text = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            pages_text.append(page_text.strip())
    return "\n\n".join([p for p in pages_text if p]).strip()

