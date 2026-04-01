import io
import re
import logging

log = logging.getLogger(__name__)


def extract_text(file_bytes: bytes, filename: str = "") -> str:
    """Main entry point. Returns cleaned text or empty string."""
    text = _try_pdfplumber(file_bytes, filename)
    if not text.strip():
        log.warning(f"pdfplumber_empty for {filename}, falling back to pymupdf")
        text = _try_pymupdf(file_bytes, filename)
    cleaned = _clean(text)
    log.info(f"Extracted {len(cleaned)} chars from {filename}")
    return cleaned


def _try_pdfplumber(file_bytes: bytes, filename: str) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages = []
            for page in pdf.pages:
                t = page.extract_text(x_tolerance=2, y_tolerance=2)
                if t:
                    pages.append(t)
            return "\n\n".join(pages)
    except Exception as exc:
        log.warning(f"pdfplumber_failed for {filename}: {exc}")
        return ""


def _try_pymupdf(file_bytes: bytes, filename: str) -> str:
    try:
        import fitz
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        pages = [page.get_text("text") for page in doc]
        doc.close()
        return "\n\n".join(pages)
    except Exception as exc:
        log.error(f"pymupdf_failed for {filename}: {exc}")
        return ""


def _clean(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[^\x20-\x7E\n]", " ", text)
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(lines).strip()
