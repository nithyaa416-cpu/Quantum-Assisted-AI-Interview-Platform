"""
code_runner.py — orchestrates running multiple test cases through Judge0
and evaluating each result.

Keeps the Judge0 interaction and evaluation logic separate from the
Django views so views stay thin.
"""
import logging
from typing import Optional

from .judge0_client import (
    run_code, Judge0Error,
    STATUS_ACCEPTED, STATUS_COMPILATION_ERROR,
)
from .evaluator import outputs_match

logger = logging.getLogger(__name__)


def run_test_cases(
    source_code: str,
    language: str,
    test_cases: list[dict],   # [{'id': str, 'input': str, 'expected_output': str}, ...]
    time_limit: float = 2.0,
    memory_limit_mb: int = 256,
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

    for tc in test_cases:
        tc_id    = str(tc.get('id', ''))
        stdin    = tc.get('input', '')
        expected = tc.get('expected_output', '')

        try:
            result = run_code(
                source_code=source_code,
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
