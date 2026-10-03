"""
Judge0 CE client.

ALL student source code execution goes through this module.
Django never runs student code directly.

Environment variables (set in .env / Django settings):
  JUDGE0_API_URL  — base URL of Judge0 instance (no trailing slash)
  JUDGE0_API_KEY  — optional API key for hosted deployments (blank for local CE)

The language → Judge0 language_id mapping is read from Django settings
(JUDGE0_LANGUAGE_IDS) so IDs are centrally configurable without touching code.
"""
import logging
import time
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# ── Internal normalised status codes ─────────────────────────────────────────
# These decouple frontend/backend from Judge0 numeric status IDs.

STATUS_ACCEPTED             = 'accepted'
STATUS_WRONG_ANSWER         = 'wrong_answer'
STATUS_COMPILATION_ERROR    = 'compilation_error'
STATUS_RUNTIME_ERROR        = 'runtime_error'
STATUS_TLE                  = 'time_limit_exceeded'
STATUS_MLE                  = 'memory_limit_exceeded'
STATUS_INTERNAL_ERROR       = 'internal_error'
STATUS_PENDING              = 'pending'

# Judge0 status_id → our normalised status
_J0_STATUS_MAP: dict[int, str] = {
    1:  STATUS_PENDING,           # In Queue
    2:  STATUS_PENDING,           # Processing
    3:  STATUS_ACCEPTED,          # Accepted
    4:  STATUS_WRONG_ANSWER,      # Wrong Answer
    5:  STATUS_TLE,               # Time Limit Exceeded
    6:  STATUS_COMPILATION_ERROR, # Compilation Error
    7:  STATUS_RUNTIME_ERROR,     # Runtime Error (SIGSEGV)
    8:  STATUS_RUNTIME_ERROR,     # Runtime Error (SIGXFSZ)
    9:  STATUS_RUNTIME_ERROR,     # Runtime Error (SIGFPE)
    10: STATUS_RUNTIME_ERROR,     # Runtime Error (SIGABRT)
    11: STATUS_RUNTIME_ERROR,     # Runtime Error (NZEC)
    12: STATUS_RUNTIME_ERROR,     # Runtime Error (Other)
    13: STATUS_INTERNAL_ERROR,    # Internal Error
    14: STATUS_MLE,               # Exec Format Error / Memory Limit
}


class Judge0Error(Exception):
    """Raised when Judge0 returns an unexpected response or is unreachable."""


def _base_url() -> str:
    url = getattr(settings, 'JUDGE0_API_URL', 'http://localhost:2358').rstrip('/')
    return url


def _headers() -> dict:
    api_key = getattr(settings, 'JUDGE0_API_KEY', '')
    h = {'Content-Type': 'application/json'}
    if api_key:
        # RapidAPI hosted Judge0 uses X-RapidAPI-Key
        h['X-RapidAPI-Key'] = api_key
        h['X-RapidAPI-Host'] = 'judge0-ce.p.rapidapi.com'
    return h


def get_language_id(language: str) -> int:
    """
    Map a frontend language string ('python', 'java', 'cpp') to
    the Judge0 language_id configured in Django settings.

    Raises ValueError for unsupported languages.
    """
    mapping: dict[str, int] = getattr(settings, 'JUDGE0_LANGUAGE_IDS', {})
    if language not in mapping:
        raise ValueError(
            f"Unsupported language '{language}'. "
            f"Supported: {list(mapping.keys())}"
        )
    return mapping[language]


def submit_code(
    source_code: str,
    language: str,
    stdin: str = '',
    cpu_time_limit: float = 2.0,
    memory_limit_kb: int = 262144,   # 256 MB
) -> str:
    """
    Submit source_code to Judge0 (non-wait mode) and return the token.
    Raises Judge0Error on failure.
    """
    language_id = get_language_id(language)
    payload = {
        'source_code': source_code,
        'language_id': language_id,
        'stdin':        stdin,
        'cpu_time_limit': cpu_time_limit,
        'memory_limit':   memory_limit_kb,
    }
    url = f'{_base_url()}/submissions?base64_encoded=false&wait=false'
    try:
        resp = requests.post(url, json=payload, headers=_headers(), timeout=10)
        resp.raise_for_status()
        token = resp.json().get('token')
        if not token:
            raise Judge0Error(f'Judge0 returned no token. Response: {resp.text}')
        return token
    except requests.RequestException as exc:
        logger.error('Judge0 submission failed: %s', exc)
        raise Judge0Error(f'Judge0 unreachable: {exc}') from exc


def get_result(token: str) -> dict:
    """
    Poll Judge0 for the result of a previously submitted token.
    Returns the raw Judge0 response dict.
    Raises Judge0Error on failure.
    """
    url = f'{_base_url()}/submissions/{token}?base64_encoded=false&fields=status_id,status,stdout,stderr,compile_output,time,memory,message'
    try:
        resp = requests.get(url, headers=_headers(), timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        logger.error('Judge0 result fetch failed: %s', exc)
        raise Judge0Error(f'Judge0 unreachable: {exc}') from exc


def wait_for_result(
    token: str,
    timeout_seconds: Optional[int] = None,
    poll_interval: float = 0.5,
) -> dict:
    """
    Poll Judge0 until execution finishes (status_id > 2) or timeout.
    Returns normalised result dict (see _normalise).
    """
    if timeout_seconds is None:
        timeout_seconds = getattr(settings, 'JUDGE0_TIMEOUT_SECONDS', 15)

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        raw = get_result(token)
        status_id = raw.get('status_id') or raw.get('status', {}).get('id', 0)
        if status_id and status_id > 2:   # finished (not in-queue / processing)
            return _normalise(raw)
        time.sleep(poll_interval)

    raise Judge0Error('Judge0 execution timed out waiting for result.')


def run_code(
    source_code: str,
    language: str,
    stdin: str = '',
    cpu_time_limit: float = 2.0,
    memory_limit_kb: int = 262144,
) -> dict:
    """
    Convenience: submit + wait + return normalised result.
    This is the main entry point called by coding_views.py.
    """
    token = submit_code(source_code, language, stdin, cpu_time_limit, memory_limit_kb)
    return wait_for_result(token)


# ── Normalisation ─────────────────────────────────────────────────────────────

def _normalise(raw: dict) -> dict:
    """
    Convert a raw Judge0 response into our project's normalised format.
    Frontend should only ever see normalised statuses, never Judge0 IDs.
    """
    status_obj = raw.get('status') or {}
    status_id  = raw.get('status_id') or status_obj.get('id') or 0
    status_desc = status_obj.get('description', '')

    normalised_status = _J0_STATUS_MAP.get(int(status_id), STATUS_INTERNAL_ERROR)

    stdout  = raw.get('stdout') or ''
    stderr  = raw.get('stderr') or ''
    compile_output = raw.get('compile_output') or ''

    # For compilation errors, Judge0 puts the message in compile_output
    if normalised_status == STATUS_COMPILATION_ERROR and compile_output:
        stderr = compile_output

    time_ms: Optional[float] = None
    raw_time = raw.get('time')
    if raw_time is not None:
        try:
            time_ms = float(raw_time) * 1000   # seconds → ms
        except (TypeError, ValueError):
            pass

    memory_kb: Optional[int] = None
    raw_mem = raw.get('memory')
    if raw_mem is not None:
        try:
            memory_kb = int(raw_mem)
        except (TypeError, ValueError):
            pass

    return {
        'status':    normalised_status,
        'stdout':    stdout.strip(),
        'stderr':    stderr.strip(),
        'time_ms':   time_ms,
        'memory_kb': memory_kb,
        'judge0_status_id':   status_id,
        'judge0_description': status_desc,
    }
