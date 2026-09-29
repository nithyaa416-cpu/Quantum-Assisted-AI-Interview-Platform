"""
PDF text extraction using pypdf (primary) with fallback to pdfminer.six.
Preserves structural newlines, spacing, and multi-page text cleanly.
"""
import io
import logging

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract raw text from a PDF file path.
    Uses pypdf as primary extractor (clean layout & line breaks), falls back to pdfminer.six.
    """
    # 1. Try pypdf first (much cleaner line breaks and text layout)
    try:
        import pypdf
        reader = pypdf.PdfReader(file_path)
        pages_text = []
        for page in reader.pages:
            t = page.extract_text()
            if t and t.strip():
                pages_text.append(t.strip())
        text = "\n\n".join(pages_text).strip()
        if text:
            return text
    except Exception as exc:
        logger.warning("pypdf failed on %s: %s, trying pdfminer fallback", file_path, exc)

    # 2. Fallback to pdfminer.six
    try:
        from pdfminer.high_level import extract_text as pdfminer_extract
        from pdfminer.layout import LAParams
        laparams = LAParams(
            line_margin=0.5,
            word_margin=0.1,
            char_margin=2.0,
            boxes_flow=0.5,
        )
        text = pdfminer_extract(file_path, laparams=laparams)
        return text or ""
    except Exception as exc:
        logger.error("PDF extraction failed for %s: %s", file_path, exc)
        return ""


def extract_text_from_bytes(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes (in-memory)."""
    # 1. Try pypdf first
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        pages_text = []
        for page in reader.pages:
            t = page.extract_text()
            if t and t.strip():
                pages_text.append(t.strip())
        text = "\n\n".join(pages_text).strip()
        if text:
            return text
    except Exception as exc:
        logger.warning("pypdf bytes extraction failed: %s, trying pdfminer fallback", exc)

    # 2. Fallback to pdfminer.six
    try:
        from pdfminer.high_level import extract_text as pdfminer_extract
        from pdfminer.layout import LAParams
        laparams = LAParams(line_margin=0.5, word_margin=0.1, char_margin=2.0)
        text = pdfminer_extract(io.BytesIO(pdf_bytes), laparams=laparams)
        return text or ""
    except Exception as exc:
        logger.error("PDF bytes extraction failed: %s", exc)
        return ""

