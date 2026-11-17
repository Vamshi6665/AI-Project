"""PDF -> text with PyMuPDF.

Text-based PDFs (exported from an EHR or Word) work out of the box. Scanned PDFs have no text
layer, so they come back empty and the API returns NO_TEXT_FOUND; adding OCR (Amazon Textract)
is the natural next feature.
"""
from dataclasses import dataclass

import pymupdf

from ..errors import EmptyDocumentError, InvalidFileError

PDF_MAGIC = b"%PDF-"


@dataclass
class PdfText:
    text: str
    pages: int
    chars: int
    truncated: bool


def extract_text(data: bytes, max_pages: int, max_chars: int) -> PdfText:
    # Check the file's magic bytes, not just the extension or the browser's content-type.
    if not data.startswith(PDF_MAGIC):
        raise InvalidFileError("File is not a valid PDF")

    try:
        doc = pymupdf.open(stream=data, filetype="pdf")
    except Exception as exc:  # corrupted file
        raise InvalidFileError("PDF could not be opened", details=str(exc))

    with doc:
        if doc.needs_pass:
            raise InvalidFileError("Password-protected PDFs are not supported")
        page_count = doc.page_count
        if page_count > max_pages:
            raise InvalidFileError(f"PDF has {page_count} pages; the limit is {max_pages}")

        parts = []
        for i, page in enumerate(doc, start=1):
            page_text = page.get_text("text").strip()
            if page_text:
                parts.append(f"--- Page {i} ---\n{page_text}")

    full_text = "\n\n".join(parts)
    if len(full_text.strip()) < 20:
        raise EmptyDocumentError(
            "No readable text found. The PDF is probably a scanned image; OCR is not enabled yet."
        )

    truncated = len(full_text) > max_chars
    return PdfText(
        text=full_text[:max_chars],
        pages=page_count,
        chars=len(full_text),
        truncated=truncated,
    )
