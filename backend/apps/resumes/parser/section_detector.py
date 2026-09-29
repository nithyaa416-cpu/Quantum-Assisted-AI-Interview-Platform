"""
Detect and split resume sections from raw text.
Uses header keyword matching with regex — no external dependencies.
"""
import re
from dataclasses import dataclass, field


# Section header patterns — order matters (most specific first)
SECTION_PATTERNS: list[tuple[str, list[str]]] = [
    ("education", [
        r"education", r"academic\s+background", r"academic\s+qualifications",
        r"educational\s+qualifications", r"degrees?",
    ]),
    ("experience", [
        r"(work\s+)?experience", r"employment(\s+history)?", r"professional\s+experience",
        r"internship", r"work\s+history", r"career\s+history",
    ]),
    ("projects", [
        r"projects?", r"personal\s+projects?", r"academic\s+projects?",
        r"key\s+projects?", r"notable\s+projects?",
    ]),
    ("skills", [
        r"(technical\s+)?skills?", r"core\s+competencies", r"technologies",
        r"tech\s+stack", r"tools?\s+&?\s+technologies", r"programming\s+languages?",
        r"expertise", r"competencies",
    ]),
    ("certifications", [
        r"certifications?", r"certificates?", r"courses?", r"credentials?",
        r"licenses?", r"achievements?",
    ]),
    ("summary", [
        r"(professional\s+)?summary", r"objective", r"profile",
        r"about(\s+me)?", r"career\s+objective", r"overview",
    ]),
    ("contact", [
        r"contact(\s+information)?", r"personal\s+(information|details)",
        r"basic\s+information",
    ]),
    ("additional", [
        r"additional\s+information", r"hobbies(\s+and\s+interests)?",
        r"interests?", r"strengths?", r"extracurricular(\s+activities)?",
    ]),
    ("declaration", [
        r"declaration",
    ]),
]


@dataclass
class ResumeSection:
    name: str
    text: str = ""
    lines: list[str] = field(default_factory=list)


def _build_header_pattern() -> re.Pattern:
    all_patterns = []
    for _name, patterns in SECTION_PATTERNS:
        all_patterns.extend(patterns)
    combined = "|".join(f"(?:{p})" for p in all_patterns)
    # A header line: short line (< 60 chars) matching a section keyword, possibly ALL CAPS
    return re.compile(
        r"^\s*(?:[\u2022\-\*\#]?\s*)?(" + combined + r")\s*[:\-]?\s*$",
        re.IGNORECASE | re.MULTILINE,
    )


_HEADER_RE = _build_header_pattern()


def _classify_header(line: str) -> str | None:
    """Return section name if the line is a section header, else None."""
    stripped = line.strip()
    if not stripped or len(stripped) > 80:
        return None
    for section_name, patterns in SECTION_PATTERNS:
        for p in patterns:
            if re.fullmatch(r"\s*" + p + r"\s*[:\-]?\s*", stripped, re.IGNORECASE):
                return section_name
    return None


def split_into_sections(text: str) -> dict[str, str]:
    """
    Split resume text into named sections.
    Returns a dict: section_name → section_text.
    'raw' always contains the full original text.
    """
    sections: dict[str, str] = {"raw": text}
    lines = text.splitlines()

    current_section = "header"
    buffer: list[str] = []
    section_texts: dict[str, list[str]] = {}

    for line in lines:
        detected = _classify_header(line)
        if detected:
            # Save buffer to previous section
            if buffer:
                section_texts.setdefault(current_section, []).extend(buffer)
            current_section = detected
            buffer = []
        else:
            buffer.append(line)

    # Flush last buffer
    if buffer:
        section_texts.setdefault(current_section, []).extend(buffer)

    for name, section_lines in section_texts.items():
        sections[name] = "\n".join(section_lines).strip()

    return sections
