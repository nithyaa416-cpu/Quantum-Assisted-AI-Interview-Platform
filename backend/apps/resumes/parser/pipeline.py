"""
Main resume parsing pipeline.
Orchestrates: PDF extraction → section detection → per-section extraction → structured output.
"""
import os
import logging
import time
from typing import Any

from .pdf_extractor import extract_text_from_pdf, extract_text_from_bytes
from .docx_extractor import extract_text_from_docx, extract_text_from_doc
from .section_detector import split_into_sections
from .extractors import (
    extract_contact,
    extract_skills,
    extract_education,
    extract_experience,
    extract_projects,
    extract_certifications,
    generate_summary,
)

logger = logging.getLogger(__name__)


def parse_resume_file(file_path: str) -> dict[str, Any]:
    """
    Full pipeline: file path → structured parsed data dict.
    Supports PDF (.pdf), modern Word (.docx), legacy Word (.doc), and text (.txt).
    Safe — never raises; on failure returns a partial/empty result with error info.
    """
    start = time.time()
    result: dict[str, Any] = {
        "success": False,
        "error": None,
        "contact": {},
        "skills": [],
        "education": [],
        "experience": [],
        "projects": [],
        "certifications": [],
        "summary": "",
        "raw_text": "",
        "word_count": 0,
        "parse_time_ms": 0,
    }

    try:
        # Step 1: Extract raw text based on file extension
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.docx':
            raw_text = extract_text_from_docx(file_path)
        elif ext == '.doc':
            raw_text = extract_text_from_doc(file_path)
        elif ext == '.txt':
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    raw_text = f.read()
            except Exception:
                raw_text = ""
        else:
            # Default to PDF
            raw_text = extract_text_from_pdf(file_path)
            # If PDF extraction failed and file isn't explicitly .pdf, attempt DOCX
            if not raw_text.strip() and ext != '.pdf':
                raw_text = extract_text_from_docx(file_path)

        if not raw_text.strip():
            fmt = ext.replace('.', '').upper() if ext else 'file'
            result["error"] = f"Could not extract text from {fmt}. The file may be image-based, empty, or corrupted."
            return result

        result["raw_text"] = raw_text
        result["word_count"] = len(raw_text.split())

        # Step 2: Split into sections
        sections = split_into_sections(raw_text)

        # Step 3: Extract contact from the top of the resume
        header_text = sections.get("header", raw_text[:500])
        result["contact"] = extract_contact(raw_text[:1000])

        # Step 4: Extract skills
        skills_text = sections.get("skills", "")
        # Also scan full document for skills not in the skills section
        result["skills"] = _deduplicate_skills(
            extract_skills(skills_text) + extract_skills(raw_text)
        )

        # Step 5: Education
        edu_text = sections.get("education", "")
        result["education"] = extract_education(edu_text or raw_text)

        # Step 6: Experience
        exp_text = sections.get("experience", "")
        result["experience"] = extract_experience(exp_text or raw_text)

        # Step 7: Projects
        proj_text = sections.get("projects", "")
        result["projects"] = extract_projects(proj_text or raw_text)

        # Step 8: Certifications
        cert_text = sections.get("certifications", "")
        result["certifications"] = extract_certifications(cert_text or raw_text)

        # Step 9: Generate summary
        result["summary"] = generate_summary(
            result["contact"],
            result["skills"],
            result["education"],
            result["experience"],
            result["projects"],
        )

        result["success"] = True

    except Exception as exc:
        logger.exception("Resume parsing pipeline error: %s", exc)
        result["error"] = f"Parsing error: {str(exc)}"

    finally:
        result["parse_time_ms"] = int((time.time() - start) * 1000)

    return result


def parse_resume_bytes(pdf_bytes: bytes) -> dict[str, Any]:
    """Variant that accepts raw PDF bytes instead of a file path."""
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name
    try:
        return parse_resume_file(tmp_path)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def _deduplicate_skills(skills: list[dict]) -> list[dict]:
    """Keep highest-confidence version of each skill by name."""
    seen: dict[str, dict] = {}
    confidence_order = {"high": 2, "medium": 1, "low": 0}
    for skill in skills:
        name = skill["name"]
        existing = seen.get(name)
        if not existing or (
            confidence_order.get(skill["confidence"], 0)
            > confidence_order.get(existing["confidence"], 0)
        ):
            seen[name] = skill
    return list(seen.values())
