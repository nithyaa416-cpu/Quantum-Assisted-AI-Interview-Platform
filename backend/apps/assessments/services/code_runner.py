"""
code_runner.py — orchestrates running multiple test cases through Judge0
and evaluating each result.

Keeps the Judge0 interaction and evaluation logic separate from the
Django views so views stay thin.
"""
import logging
import re
from typing import Optional

from .judge0_client import (
    run_code, Judge0Error,
    STATUS_ACCEPTED, STATUS_COMPILATION_ERROR,
)
from .evaluator import outputs_match

logger = logging.getLogger(__name__)


def wrap_with_driver_code(source_code: str, language: str, driver_code: Optional[str] = None) -> str:
    """
    Combines candidate source code (function only) with the problem's driver code.
    If the candidate already supplied their own main/driver entrypoint, leaves code intact.
    """
    if not driver_code or not driver_code.strip():
        return source_code

    lang = language.lower().strip()

    # Python: check if user wrote their own entry point
    if lang in ('python', 'python3', 'py'):
        if '__main__' in source_code or 'sys.stdin' in source_code:
            return source_code
        return f"{source_code.rstrip()}\n\n{driver_code.strip()}\n"

    # Java: check if user wrote their own main
    if lang in ('java',):
        if 'public static void main' in source_code or 'void main(' in source_code:
            return source_code
        # Ensure candidate's class is not 'public' to avoid javac multiple public class errors with driver Main
        cleaned_user_code = re.sub(r'\bpublic\s+class\s+([A-Za-z0-9_]+)', r'class \1', source_code)
        return f"{cleaned_user_code.rstrip()}\n\n{driver_code.strip()}\n"

    # C++: check if user wrote their own int main
    if lang in ('cpp', 'c++'):
        if 'int main(' in source_code or 'int main (' in source_code:
            return source_code
        return f"{source_code.rstrip()}\n\n{driver_code.strip()}\n"

    # JavaScript / Node
    if lang in ('javascript', 'js', 'node'):
        if 'process.stdin' in source_code or 'readline' in source_code:
            return source_code
        return f"{source_code.rstrip()}\n\n{driver_code.strip()}\n"

    return f"{source_code.rstrip()}\n\n{driver_code.strip()}\n"


def run_test_cases(
    source_code: str,
    language: str,
    test_cases: list[dict],   # [{'id': str, 'input': str, 'expected_output': str}, ...]
    time_limit: float = 2.0,
    memory_limit_mb: int = 256,
    driver_code: Optional[str] = None,
) -> dict:
    """
    Run source_code against each test case via Judge0.

    Returns:
    {
        'overall_status': 'accepted' | 'wrong_answer' | 'compilation_error' | ...,
        'passed':  int,
        'total':   int,
        'runtime_ms':  float | None,   # max across test cases
        'memory_kb':   int | None,     # max across test cases
        'results': [
            {
                'test_case_id': str,
                'status':       str,   # normalised
                'stdout':       str,
                'stderr':       str,
                'time_ms':      float | None,
                'memory_kb':    int | None,
                'passed':       bool,
            },
            ...
        ]
    }

    SECURITY: source_code is NEVER executed here; it is sent to Judge0.
    """
    results = []
    passed_count = 0
    max_time_ms: Optional[float] = None
    max_memory_kb: Optional[int] = None
    overall_status = STATUS_ACCEPTED
    executable_code = wrap_with_driver_code(source_code, language, driver_code)

    for tc in test_cases:
        tc_id    = str(tc.get('id', ''))
        stdin    = tc.get('input', '')
        expected = tc.get('expected_output', '')

        try:
            result = run_code(
                source_code=executable_code,
                language=language,
                stdin=stdin,
                cpu_time_limit=time_limit,
                memory_limit_kb=memory_limit_mb * 1024,
            )
        except Judge0Error as exc:
            logger.error('Judge0 error for test case %s: %s', tc_id, exc)
            result = {
                'status':    'internal_error',
                'stdout':    '',
                'stderr':    str(exc),
                'time_ms':   None,
                'memory_kb': None,
            }

        # Determine pass/fail for this test case
        tc_passed = (
            result['status'] == STATUS_ACCEPTED
            and outputs_match(expected, result['stdout'])
        )
        if tc_passed:
            passed_count += 1
        else:
            # First non-pass determines the overall status
            if overall_status == STATUS_ACCEPTED:
                overall_status = result['status']

        # Track max time + memory
        if result['time_ms'] is not None:
            max_time_ms = max(max_time_ms or 0, result['time_ms'])
        if result['memory_kb'] is not None:
            max_memory_kb = max(max_memory_kb or 0, result['memory_kb'])

        # Early exit on compilation error — no point running more test cases
        if result['status'] == STATUS_COMPILATION_ERROR:
            results.append({
                'test_case_id': tc_id,
                'status':       result['status'],
                'stdout':       result['stdout'],
                'stderr':       result['stderr'],
                'time_ms':      result['time_ms'],
                'memory_kb':    result['memory_kb'],
                'passed':       False,
            })
            overall_status = STATUS_COMPILATION_ERROR
            break

        results.append({
            'test_case_id': tc_id,
            'status':       result['status'] if not tc_passed else STATUS_ACCEPTED,
            'stdout':       result['stdout'],
            'stderr':       result['stderr'],
            'time_ms':      result['time_ms'],
            'memory_kb':    result['memory_kb'],
            'passed':       tc_passed,
        })

    total = len(test_cases)

    return {
        'overall_status': overall_status,
        'passed':         passed_count,
        'total':          total,
        'runtime_ms':     round(max_time_ms, 2) if max_time_ms is not None else None,
        'memory_kb':      max_memory_kb,
        'results':        results,
    }
