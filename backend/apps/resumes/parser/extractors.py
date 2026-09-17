"""
Individual extractors for each resume section.
Each extractor takes raw section text and returns structured data.
No external models required — pure regex + ontology matching.
"""
import re
import logging
from typing import Any
from .skill_ontology import ALL_SKILLS, normalise_skill

logger = logging.getLogger(__name__)


# ── Contact / Personal info ───────────────────────────────────────────────────

EMAIL_RE    = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE    = re.compile(r"(?:\+?\d[\d\s\-().]{7,15}\d)")
LINKEDIN_RE = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-]+/?", re.IGNORECASE)
GITHUB_RE   = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[\w\-]+/?", re.IGNORECASE)
NAME_RE     = re.compile(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})$", re.MULTILINE)


def extract_contact(text: str) -> dict[str, str]:
    emails    = EMAIL_RE.findall(text)
    phones    = PHONE_RE.findall(text)
    linkedins = LINKEDIN_RE.findall(text)
    githubs   = GITHUB_RE.findall(text)
    names     = NAME_RE.findall(text[:500])   # Name is usually at the top

    return {
        "name":     names[0].strip()     if names     else "",
        "email":    emails[0].strip()    if emails    else "",
        "phone":    phones[0].strip()    if phones    else "",
        "linkedin": linkedins[0].strip() if linkedins else "",
        "github":   githubs[0].strip()   if githubs   else "",
    }


# ── Skills ────────────────────────────────────────────────────────────────────

def extract_skills(text: str) -> list[dict[str, str]]:
    """
    Extract skills from text using ontology matching.
    Handles comma/bullet/pipe-separated lists and inline mentions.
    Returns [{name, category, confidence}]
    """
    found: dict[str, dict[str, str]] = {}

    # Normalise text: replace bullets, pipes
    clean = re.sub(r"[•·|▪▸►‣⁃]", ",", text)
    clean = re.sub(r"\n+", " ", clean)

    # Try to extract from a skills section (comma/slash separated first)
    tokens = re.split(r"[,/\n]+", clean)
    for token in tokens:
        token = token.strip().strip("•-–—*").strip()
        if 2 <= len(token) <= 40:
            lower = token.lower()
            if lower in ALL_SKILLS:
                canonical, category = normalise_skill(token)
                found[canonical] = {"name": canonical, "category": category, "confidence": "high"}

    # Full-text scan for skills that might not be in comma-separated lists
    lower_text = clean.lower()
    for skill_lower, category in ALL_SKILLS.items():
        if skill_lower in found:
            continue
        # Word-boundary aware search
        pattern = r"(?<![a-z])" + re.escape(skill_lower) + r"(?![a-z])"
        if re.search(pattern, lower_text):
            canonical, cat = normalise_skill(skill_lower)
            if canonical not in found:
                found[canonical] = {"name": canonical, "category": category, "confidence": "medium"}

    return list(found.values())


# ── Education ─────────────────────────────────────────────────────────────────

DEGREE_PATTERNS = [
    r"(?:bachelor(?:'s)?|b\.?tech|b\.?e\.?|b\.?sc?\.?|b\.?a\.?)\s*(?:of|in)?\s*[\w\s]+",
    r"(?:master(?:'s)?|m\.?tech|m\.?e\.?|m\.?sc?\.?|m\.?b\.?a\.?)\s*(?:of|in)?\s*[\w\s]+",
    r"(?:phd|ph\.d\.?|doctorate)\s*(?:in)?\s*[\w\s]*",
    r"(?:diploma|certificate|certification)\s*(?:in)?\s*[\w\s]+",
]

YEAR_RE    = re.compile(r"\b((?:19|20)\d{2})\b")
GPA_RE     = re.compile(r"(?:gpa|cgpa|grade)[\s:]*([0-9]+\.?[0-9]*)", re.IGNORECASE)
COLLEGE_RE = re.compile(
    r"(?:university|college|institute|iit|nit|iiit|bits|vit|srm|anna|manipal)[\w\s,]+",
    re.IGNORECASE,
)


def extract_education(text: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    for i, line in enumerate(lines):
        lower = line.lower()
        # Check if line mentions a degree
        is_degree = any(
            re.search(p, lower) for p in DEGREE_PATTERNS
        )
        is_college = bool(COLLEGE_RE.search(line))

        if is_degree or is_college:
            # Grab context (this line + next 3)
            context = " ".join(lines[i:i+4])
            years = YEAR_RE.findall(context)
            gpa_match = GPA_RE.search(context)
            colleges = COLLEGE_RE.findall(context)

            entry: dict[str, Any] = {
                "degree":     line if is_degree else "",
                "institution": colleges[0].strip() if colleges else "",
                "start_year": years[0] if len(years) > 1 else "",
                "end_year":   years[-1] if years else "",
                "gpa":        gpa_match.group(1) if gpa_match else "",
            }
            # Avoid duplicates
            if not any(e["degree"] == entry["degree"] and e["institution"] == entry["institution"] for e in entries):
                entries.append(entry)

    return entries


# ── Experience ────────────────────────────────────────────────────────────────

MONTH_RE = re.compile(
    r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b",
    re.IGNORECASE,
)
DATE_RANGE_RE = re.compile(
    r"(?:"
    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d{4}"
    r"|present|current|now|\d{4}"
    r")\s*[-–—to]+\s*"
    r"(?:"
    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d{4}"
    r"|present|current|now|\d{4}"
    r")",
    re.IGNORECASE,
)
ROLE_KEYWORDS = [
    "engineer", "developer", "intern", "analyst", "designer", "manager",
    "lead", "architect", "consultant", "scientist", "researcher", "specialist",
    "associate", "director", "executive", "officer", "head", "founder",
]


def extract_experience(text: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    i = 0
    while i < len(lines):
        line = lines[i]
        lower = line.lower()
        is_role_line = any(kw in lower for kw in ROLE_KEYWORDS)
        has_dates = bool(DATE_RANGE_RE.search(line)) or bool(YEAR_RE.search(line))

        if is_role_line or has_dates:
            # Collect bullet points / description lines (next 6 lines)
            description_lines = []
            for j in range(i+1, min(i+7, len(lines))):
                next_line = lines[j].strip()
                # Stop if we hit another role/section header
                if any(kw in next_line.lower() for kw in ROLE_KEYWORDS) and YEAR_RE.search(next_line):
                    break
                if next_line.startswith(("•", "-", "–", "*", "▪")):
                    description_lines.append(next_line.lstrip("•-–*▪ ").strip())
                elif next_line:
                    description_lines.append(next_line)

            date_match = DATE_RANGE_RE.search(line)
            entry: dict[str, Any] = {
                "role":        line if is_role_line else "",
                "company":     "",    # hard to extract reliably without NER
                "date_range":  date_match.group(0) if date_match else "",
                "description": description_lines,
                "technologies": [],
            }

            # Extract technologies mentioned in description
            desc_text = " ".join(description_lines)
            tech_skills = extract_skills(desc_text)
            entry["technologies"] = [s["name"] for s in tech_skills]

            if entry["role"] or entry["date_range"]:
                entries.append(entry)

        i += 1

    # Deduplicate
    seen_roles: set[str] = set()
    unique_entries = []
    for e in entries:
        key = e["role"][:40]
        if key not in seen_roles:
            seen_roles.add(key)
            unique_entries.append(e)

    return unique_entries[:10]   # cap at 10 experience entries


# ── Projects ──────────────────────────────────────────────────────────────────

def extract_projects(text: str) -> list[dict[str, Any]]:
    """
    Extract project entries from the projects section.
    Each project has: title, description, technologies, url.
    """
    URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)
    entries: list[dict[str, Any]] = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    current_project: dict[str, Any] | None = None

    for line in lines:
        # Project title heuristic: short line (< 80 chars), not starting with bullet
        is_title = (
            len(line) < 80
            and not line.startswith(("•", "-", "–", "*", "▪"))
            and not DATE_RANGE_RE.search(line)
            and not line[0].isdigit()
            and len(line.split()) >= 2
        )

        urls = URL_RE.findall(line)

        if is_title and not urls:
            if current_project:
                entries.append(current_project)
            current_project = {
                "title":        line,
                "description":  [],
                "technologies": [],
                "url":          "",
            }
        elif current_project:
            if urls:
                current_project["url"] = urls[0]
            # Extract description
            desc_line = line.lstrip("•-–*▪ ").strip()
            if desc_line:
                current_project["description"].append(desc_line)
                # Extract tech from description
                tech = extract_skills(desc_line)
                new_tech = [t["name"] for t in tech if t["name"] not in current_project["technologies"]]
                current_project["technologies"].extend(new_tech)

    if current_project:
        entries.append(current_project)

    # Convert description list to string
    for e in entries:
        e["description"] = " ".join(e["description"])[:500]

    return entries[:15]   # cap at 15 projects


# ── Certifications ────────────────────────────────────────────────────────────

CERT_KEYWORDS = [
    "aws", "azure", "gcp", "google", "oracle", "cisco", "comptia", "certified",
    "certification", "certificate", "udemy", "coursera", "edx", "nptel",
    "microsoft", "red hat", "kubernetes", "docker",
]


def extract_certifications(text: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    for line in lines:
        lower = line.lower()
        if any(kw in lower for kw in CERT_KEYWORDS):
            years = YEAR_RE.findall(line)
            entries.append({
                "name": line.lstrip("•-–*▪ ").strip(),
                "year": years[-1] if years else "",
            })

    return entries


# ── Summary generator (rule-based) ───────────────────────────────────────────

def generate_summary(
    contact: dict,
    skills: list[dict],
    education: list[dict],
    experience: list[dict],
    projects: list[dict],
) -> str:
    """Build a brief text summary of the parsed resume."""
    parts = []

    name = contact.get("name", "The candidate")
    parts.append(f"{name} is")

    # Education level
    degrees = [e["degree"] for e in education if e.get("degree")]
    if degrees:
        parts.append(f"a {degrees[0].lower()} graduate")
    else:
        parts.append("a student")

    # Top skills by category
    top_skills = [s["name"] for s in skills[:5]]
    if top_skills:
        parts.append(f"with expertise in {', '.join(top_skills)}")

    # Experience
    if experience:
        parts.append(f"and has {len(experience)} work/internship experience(s)")

    # Projects
    if projects:
        parts.append(f"with {len(projects)} notable project(s)")

    return " ".join(parts) + "."
