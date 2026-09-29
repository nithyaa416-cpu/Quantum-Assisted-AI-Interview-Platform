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

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", re.IGNORECASE)
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3,5}\)?[-.\s]?\d{3,5}[-.\s]?\d{3,5}\b")
LINKEDIN_RE = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-]+/?", re.IGNORECASE)
GITHUB_RE = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[\w\-]+/?", re.IGNORECASE)

DISALLOWED_NAME_KEYWORDS = {
    "software", "developer", "engineer", "designer", "architect", "lead", "intern",
    "manager", "resume", "curriculum", "vitae", "cv", "profile", "contact", "summary",
    "objective", "education", "experience", "skills", "projects", "declaration",
    "personal", "information", "phone", "email", "address", "portfolio", "details",
}


def extract_contact(text: str) -> dict[str, str]:
    emails = EMAIL_RE.findall(text)
    raw_phones = PHONE_RE.findall(text)
    phones = [p.strip() for p in raw_phones if len(re.sub(r"\D", "", p)) >= 10]
    linkedins = LINKEDIN_RE.findall(text)
    githubs = GITHUB_RE.findall(text)

    # Clean linkedin URL
    linkedin_url = ""
    if linkedins:
        l = linkedins[0].strip()
        if not l.startswith("http"):
            l = f"https://{l}"
        linkedin_url = l

    # Clean github URL
    github_url = ""
    if githubs:
        g = githubs[0].strip()
        if not g.startswith("http"):
            g = f"https://{g}"
        github_url = g

    # Name extraction heuristic: check first 10 non-empty lines
    candidate_name = ""
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    for line in lines[:10]:
        if EMAIL_RE.search(line) or LINKEDIN_RE.search(line) or GITHUB_RE.search(line) or PHONE_RE.search(line):
            continue
        words = line.split()
        if not (2 <= len(words) <= 5):
            continue
        lower_words = {w.lower().strip(":,|-") for w in words}
        if lower_words & DISALLOWED_NAME_KEYWORDS:
            continue

        # Check for ALL-CAPS name (e.g. KUPPALA MANOJ LAKSHMI NARAYANA)
        if re.match(r"^[A-Z][A-Z\s\.\-]{2,60}$", line):
            candidate_name = " ".join(w.capitalize() for w in words)
            break
        # Check for Title Case name (e.g. Manoj Kuppala)
        if re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4}$", line):
            candidate_name = line
            break

    return {
        "name": candidate_name,
        "email": emails[0].strip() if emails else "",
        "phone": phones[0].strip() if phones else "",
        "linkedin": linkedin_url,
        "github": github_url,
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
    clean_lines = clean.splitlines()

    for line in clean_lines:
        line_clean = line.strip().strip("•-–—*")
        if not line_clean:
            continue
        tokens = re.split(r"[,/]+", line_clean)
        for token in tokens:
            t = token.strip().strip("•-–—*").strip()
            if 2 <= len(t) <= 40:
                lower = t.lower()
                if lower in ALL_SKILLS:
                    canonical, category = normalise_skill(t)
                    found[canonical] = {"name": canonical, "category": category, "confidence": "high"}

    lower_text = clean.lower()
    for skill_lower, category in ALL_SKILLS.items():
        if len(skill_lower) <= 2 and skill_lower not in {"c", "r", "go", "ai", "ml", "ui"}:
            continue
        pattern = r"(?<![a-z0-9])" + re.escape(skill_lower) + r"(?![a-z0-9])"
        if re.search(pattern, lower_text):
            canonical, cat = normalise_skill(skill_lower)
            if canonical not in found:
                found[canonical] = {"name": canonical, "category": category, "confidence": "medium"}

    return list(found.values())


# ── Education ─────────────────────────────────────────────────────────────────

YEAR_RE = re.compile(r"\b((?:19|20)\d{2})\b")
YEAR_RANGE_RE = re.compile(
    r"\b((?:19|20)\d{2})\s*[-–—to]+\s*((?:19|20)\d{2}|ongoing|present|current)\b",
    re.IGNORECASE,
)
GPA_PERCENT_RE = re.compile(r"(?:cgpa|percentage|gpa|grade|score)\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?%?)", re.IGNORECASE)
COLLEGE_RE = re.compile(
    r"\b(?:institute|college|university|school|academy|vidyalaya|iit|nit|iiit|bits|vit|srm)\b",
    re.IGNORECASE,
)

DEGREE_RE = re.compile(
    r"\b(?:b\.?\s*tech|b\.?\s*e\.?|bachelor(?:\'s)?|m\.?\s*tech|m\.?\s*e\.?|master(?:\'s)?|"
    r"b\.?\s*sc|m\.?\s*sc|bca|mca|bba|mba|ph\.?d|doctorate|"
    r"intermediate|senior\s+secondary|higher\s+secondary|"
    r"12th\s+(?:standard|grade|class)|10th\s+(?:standard|grade|class)|"
    r"\bssc\b|\bhsc\b|\bcbse\b|\bicse\b)\b",
    re.IGNORECASE,
)


def extract_education(text: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    degree_indices = []
    for i, line in enumerate(lines):
        if len(line) > 160:
            continue
        if GPA_PERCENT_RE.search(line) and not DEGREE_RE.search(line):
            continue
        if DEGREE_RE.search(line):
            degree_indices.append(i)

    for k, idx in enumerate(degree_indices):
        line = lines[idx]
        year_match = YEAR_RANGE_RE.search(line)
        single_year = YEAR_RE.search(line) if not year_match else None

        cleaned_degree = line
        if year_match:
            cleaned_degree = YEAR_RANGE_RE.sub("", cleaned_degree).strip()
        elif single_year:
            cleaned_degree = re.sub(r"\b(?:19|20)\d{2}\b", "", cleaned_degree).strip()
        cleaned_degree = re.sub(r"\s+", " ", cleaned_degree).strip(" -|:,")

        start_year = year_match.group(1) if year_match else ""
        end_year = year_match.group(2) if year_match else (single_year.group(1) if single_year else "")

        prev_idx = degree_indices[k - 1] if k > 0 else -1
        next_idx = degree_indices[k + 1] if k + 1 < len(degree_indices) else len(lines)

        institution = ""
        gpa = ""

        # Search within block lines between previous and next degree (up to 4 lines away)
        min_j = max(prev_idx + 1, idx - 3)
        max_j = min(next_idx, idx + 5)
        search_order = [j for j in range(min_j, max_j) if j != idx]
        # Prioritize closest lines
        search_order.sort(key=lambda j: (abs(j - idx), j < idx))

        for target in search_order:
            cand = lines[target]
            if not institution and COLLEGE_RE.search(cand) and len(cand) < 120:
                institution = cand
            if not gpa:
                gm = GPA_PERCENT_RE.search(cand)
                if gm:
                    gpa = gm.group(1)
            if not end_year:
                yr = YEAR_RANGE_RE.search(cand)
                s_yr = YEAR_RE.search(cand)
                if yr:
                    start_year = yr.group(1)
                    end_year = yr.group(2)
                elif s_yr:
                    end_year = s_yr.group(1)


        entry = {
            "degree": cleaned_degree,
            "institution": institution,
            "start_year": start_year,
            "end_year": end_year,
            "gpa": gpa,
        }

        if not any(e["degree"] == entry["degree"] for e in entries):
            entries.append(entry)

    return entries


# ── Experience ────────────────────────────────────────────────────────────────

DATE_RANGE_RE = re.compile(
    r"(?:"
    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*(?:\d{1,2},?\s*)?(?:19|20)\d{2}"
    r"|present|ongoing|current|now|\b(?:19|20)\d{2}\b"
    r")\s*[-–—to]+\s*"
    r"(?:"
    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*(?:\d{1,2},?\s*)?(?:19|20)\d{2}"
    r"|present|ongoing|current|now|\b(?:19|20)\d{2}\b"
    r")",
    re.IGNORECASE,
)

ROLE_KEYWORDS = [
    "developer", "engineer", "intern", "analyst", "designer", "manager",
    "lead", "architect", "consultant", "scientist", "researcher", "specialist",
    "associate", "director", "executive", "officer", "head", "founder",
]

COMPANY_KEYWORDS = [
    "technologies", "software", "solutions", "systems", "labs", "inc", "ltd",
    "pvt", "limited", "corp", "corporation", "infotech", "tech", "services",
]


def extract_experience(text: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    i = 0
    while i < len(lines):
        line = lines[i]
        if len(line) > 250:
            i += 1
            continue

        lower = line.lower()
        is_role_line = any(kw in lower for kw in ROLE_KEYWORDS)
        date_match = DATE_RANGE_RE.search(line)

        if is_role_line or date_match:
            role_text = line
            date_str = ""
            if date_match:
                date_str = date_match.group(0).strip()
                role_text = DATE_RANGE_RE.sub("", role_text).strip(" -|:,")

            company = ""
            for check_idx in [i + 1, i - 1]:
                if 0 <= check_idx < len(lines):
                    cand = lines[check_idx]
                    cand_lower = cand.lower()
                    if (
                        len(cand) < 100
                        and not DATE_RANGE_RE.search(cand)
                        and not any(r in cand_lower for r in ROLE_KEYWORDS)
                    ):
                        if any(ck in cand_lower for ck in COMPANY_KEYWORDS) or re.match(r"^[A-Z][\w\s&.,-]{2,60}$", cand):
                            company = cand
                            break

            description_lines = []
            for j in range(i + 1, min(i + 7, len(lines))):
                next_line = lines[j].strip()
                if any(kw in next_line.lower() for kw in ROLE_KEYWORDS) and (
                    DATE_RANGE_RE.search(next_line) or YEAR_RE.search(next_line)
                ):
                    break
                if next_line == company:
                    continue
                if next_line.startswith(("•", "-", "–", "*", "▪")):
                    description_lines.append(next_line.lstrip("•-–*▪ ").strip())
                elif len(next_line) > 20 and not DATE_RANGE_RE.search(next_line):
                    description_lines.append(next_line)

            entry: dict[str, Any] = {
                "role": role_text if is_role_line else "Software Engineer",
                "company": company,
                "date_range": date_str,
                "description": description_lines,
                "technologies": [],
            }

            desc_text = " ".join(description_lines)
            tech_skills = extract_skills(desc_text)
            entry["technologies"] = [s["name"] for s in tech_skills]

            if entry["role"]:
                entries.append(entry)

        i += 1

    seen_roles: set[str] = set()
    unique_entries = []
    for e in entries:
        key = (e["role"][:40] + e.get("company", "")[:40]).lower()
        if key not in seen_roles:
            seen_roles.add(key)
            unique_entries.append(e)

    return unique_entries[:10]


# ── Projects ──────────────────────────────────────────────────────────────────

PROJECT_ACTION_RE = re.compile(
    r"(?:developed|built|designed|created|implemented)\s+a\s+(?:fully\s+functional\s+)?([A-Za-z0-9\s\-]+?)\s+(?:using|with|in|for)\s+([^\n\.]+)",
    re.IGNORECASE,
)


def extract_projects(text: str, fallback_full_text: str = "") -> list[dict[str, Any]]:
    """
    Extract project entries from text.
    Handles explicit project sections AND inline project descriptions.
    """
    URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)
    entries: list[dict[str, Any]] = []

    # If text provided is not just a dump of the whole resume, try structured line parse
    if text and text != fallback_full_text:
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        current_project: dict[str, Any] | None = None

        for line in lines:
            if len(line) > 300:
                continue

            is_title = (
                len(line) < 80
                and not line.startswith(("•", "-", "–", "*", "▪"))
                and not DATE_RANGE_RE.search(line)
                and not line[0].isdigit()
                and len(line.split()) >= 2
                and not any(kw in line.lower() for kw in ["objective", "summary", "skills", "experience", "education"])
            )

            urls = URL_RE.findall(line)

            if is_title and not urls and not line.lower().startswith(("developed", "built", "implemented", "designed")):
                if current_project and current_project["title"]:
                    entries.append(current_project)
                current_project = {
                    "title": line,
                    "description": [],
                    "technologies": [],
                    "url": "",
                }
            elif current_project:
                if urls:
                    current_project["url"] = urls[0]
                desc_line = line.lstrip("•-–*▪ ").strip()
                if desc_line:
                    current_project["description"].append(desc_line)
                    tech = extract_skills(desc_line)
                    for t in tech:
                        if t["name"] not in current_project["technologies"]:
                            current_project["technologies"].append(t["name"])

        if current_project and current_project["title"]:
            entries.append(current_project)

    # If no projects found, scan for action sentence projects (e.g. 'Developed a fully functional scientific calculator...')
    scan_source = text if text else fallback_full_text
    if not entries and scan_source:
        m = PROJECT_ACTION_RE.search(scan_source)
        if m:
            raw_title = m.group(1).strip().title()
            tech_clause = m.group(2).strip()
            techs = [s["name"] for s in extract_skills(tech_clause)]
            # Collect consecutive descriptive lines
            desc_lines = []
            for l in scan_source.splitlines():
                ls = l.strip()
                if ls.lower().startswith(("developed", "implemented", "optimized", "built", "designed")) or (
                    desc_lines and len(ls) > 30 and not any(h in ls.upper() for h in ["EXPERIENCE", "OBJECTIVE", "EDUCATION", "SKILLS"])
                ):
                    desc_lines.append(ls)
                elif desc_lines and any(h in ls.upper() for h in ["EXPERIENCE", "OBJECTIVE", "EDUCATION", "SKILLS"]):
                    break

            description = " ".join(desc_lines) if desc_lines else m.group(0)

            entries.append({
                "title": raw_title if len(raw_title) > 3 else "Academic Project",
                "description": description[:500],
                "technologies": techs,
                "url": "",
            })

    for e in entries:
        if isinstance(e["description"], list):
            e["description"] = " ".join(e["description"])[:500]

    return entries[:10]


# ── Certifications ────────────────────────────────────────────────────────────

CERT_KEYWORDS = [
    "aws", "azure", "gcp", "google", "oracle", "cisco", "comptia", "certified",
    "certification", "certificate", "udemy", "coursera", "edx", "nptel",
    "microsoft", "red hat", "kubernetes", "docker", "course", "generative ai",
]

NON_CERT_KEYWORDS = [
    "hobbies", "interests", "strengths", "languages", "declaration", "father", "mother",
    "playing games", "solving codechef", "self motivated",
]


def extract_certifications(text: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    for line in lines:
        if len(line) > 160:
            continue
        lower = line.lower()
        if any(bad in lower for bad in NON_CERT_KEYWORDS):
            continue

        if any(kw in lower for kw in CERT_KEYWORDS):
            years = YEAR_RE.findall(line)
            clean_name = line.lstrip("•-–*▪ ").strip()
            clean_name = re.sub(r"\b(?:CERTIFICATION|COURSES?)\b", "", clean_name, flags=re.I).strip(" -|:")
            if len(clean_name) >= 4:
                entries.append({
                    "name": clean_name,
                    "year": years[-1] if years else "",
                })

    seen = set()
    unique = []
    for e in entries:
        k = e["name"].lower()
        if k not in seen:
            seen.add(k)
            unique.append(e)

    return unique[:10]


# ── Summary generator ─────────────────────────────────────────────────────────

def generate_summary(
    contact: dict,
    skills: list[dict],
    education: list[dict],
    experience: list[dict],
    projects: list[dict],
) -> str:
    """Build a brief text summary of the parsed resume."""
    parts = []
    name = contact.get("name", "").strip() or "Candidate"
    parts.append(f"{name} is")

    degrees = [e["degree"] for e in education if e.get("degree")]
    if degrees:
        parts.append(f"a {degrees[0]} student/graduate")
    else:
        parts.append("a professional")

    top_skills = [s["name"] for s in skills[:6]]
    if top_skills:
        parts.append(f"skilled in {', '.join(top_skills)}")

    if experience:
        roles = [e["role"] for e in experience if e.get("role")]
        if roles:
            parts.append(f"with experience as {roles[0]}")

    if projects:
        parts.append(f"and has {len(projects)} featured project(s)")

    return " ".join(parts) + "."
