"""
Output evaluation helpers.

Keeps comparison logic isolated so it can be adjusted without touching
the rest of the codebase.

Rules:
  - Strip leading/trailing whitespace from both expected and actual.
  - Normalise line endings (CRLF → LF).
  - Compare line-by-line, stripping trailing spaces from each line.
  - This handles the vast majority of judge differences without being
    so loose that wrong answers pass.
"""


def normalise_output(raw: str) -> str:
    """
    Normalise a program's output for comparison.
    Returns a canonical string that can be compared with ==.
    """
    # Normalise line endings
    text = raw.replace('\r\n', '\n').replace('\r', '\n')
    # Strip each line's trailing spaces, then strip leading/trailing blank lines
    lines = [line.rstrip() for line in text.split('\n')]
    # Remove trailing empty lines
    while lines and lines[-1] == '':
        lines.pop()
    return '\n'.join(lines)


def outputs_match(expected: str, actual: str) -> bool:
    """
    Return True if expected and actual outputs are equivalent after normalisation.
    """
    return normalise_output(expected) == normalise_output(actual)
