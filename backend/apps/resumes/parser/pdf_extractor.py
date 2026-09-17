"""
PDF text extraction using pdfminer.six.
Returns raw text preserving structure as much as possible.
"""
import logging
import io
from pdfminer.high_level import extract_text as pdfminer_extract
from pdfminer.layout import LAParams

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract raw text from a PDF file path.
    Returns empty string on failure — caller handles the error.
    """
    try:
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
    try:
        laparams = LAParams(line_margin=0.5, word_margin=0.1, char_margin=2.0)
        text = pdfminer_extract(io.BytesIO(pdf_bytes), laparams=laparams)
        return text or ""
    except Exception as exc:
        logger.error("PDF bytes extraction failed: %s", exc)
        return ""
