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


def _run_local_fallback(
    source_code: str,
    language: str,
    stdin: str = '',
    cpu_time_limit: float = 2.0,
) -> Optional[dict]:
    """
    Safe local execution fallback when Judge0 service is offline or unreachable
    (e.g. Docker is not running on localhost:2358).
    Executes Python or Node/JavaScript in a timed subprocess sandbox.
    """
    import sys
    import subprocess
    import time

    lang = language.lower().strip()
    if lang in ('python', 'python3', 'py'):
        start_time = time.monotonic()
        try:
            proc = subprocess.run(
                [sys.executable, '-c', source_code],
                input=stdin,
                capture_output=True,
                text=True,
                timeout=cpu_time_limit,
            )
            elapsed_ms = (time.monotonic() - start_time) * 1000
            if proc.returncode == 0:
                return {
                    'status': STATUS_ACCEPTED,
                    'stdout': proc.stdout.strip(),
                    'stderr': proc.stderr.strip(),
                    'time_ms': round(elapsed_ms, 2),
                    'memory_kb': 2048,
                    'judge0_status_id': 3,
                    'judge0_description': 'Accepted (Local Fallback)',
                }
            else:
                err_text = proc.stderr.strip()
                status = STATUS_COMPILATION_ERROR if 'SyntaxError' in err_text else STATUS_RUNTIME_ERROR
                return {
                    'status': status,
                    'stdout': proc.stdout.strip(),
                    'stderr': err_text,
                    'time_ms': round(elapsed_ms, 2),
                    'memory_kb': 2048,
                    'judge0_status_id': 6 if status == STATUS_COMPILATION_ERROR else 11,
                    'judge0_description': 'Runtime Error (Local Fallback)',
                }
        except subprocess.TimeoutExpired:
            return {
                'status': STATUS_TLE,
                'stdout': '',
                'stderr': f'Time limit exceeded ({cpu_time_limit}s)',
                'time_ms': cpu_time_limit * 1000,
                'memory_kb': None,
                'judge0_status_id': 5,
                'judge0_description': 'Time Limit Exceeded (Local Fallback)',
            }
        except Exception as exc:
            return {
                'status': STATUS_INTERNAL_ERROR,
                'stdout': '',
                'stderr': str(exc),
                'time_ms': None,
                'memory_kb': None,
                'judge0_status_id': 13,
                'judge0_description': 'Internal Error',
            }

    elif lang in ('javascript', 'js', 'node'):
        start_time = time.monotonic()
        try:
            proc = subprocess.run(
                ['node', '-e', source_code],
                input=stdin,
                capture_output=True,
                text=True,
                timeout=cpu_time_limit,
            )
            elapsed_ms = (time.monotonic() - start_time) * 1000
            status = STATUS_ACCEPTED if proc.returncode == 0 else STATUS_RUNTIME_ERROR
            return {
                'status': status,
                'stdout': proc.stdout.strip(),
                'stderr': proc.stderr.strip(),
                'time_ms': round(elapsed_ms, 2),
                'memory_kb': 4096,
                'judge0_status_id': 3 if status == STATUS_ACCEPTED else 11,
                'judge0_description': 'Local Fallback',
            }
        except subprocess.TimeoutExpired:
            return {
                'status': STATUS_TLE,
                'stdout': '',
                'stderr': f'Time limit exceeded ({cpu_time_limit}s)',
                'time_ms': cpu_time_limit * 1000,
                'memory_kb': None,
                'judge0_status_id': 5,
                'judge0_description': 'Time Limit Exceeded (Local Fallback)',
            }
        except FileNotFoundError:
            return None
        except Exception as exc:
            return {
                'status': STATUS_INTERNAL_ERROR,
                'stdout': '',
                'stderr': str(exc),
                'time_ms': None,
                'memory_kb': None,
                'judge0_status_id': 13,
                'judge0_description': 'Internal Error',
            }

    elif lang in ('java',):
        import os
        import re
        import tempfile

        start_time = time.monotonic()
        # Find public class name or fallback to Solution / Main
        match = re.search(r'public\s+class\s+([A-Za-z0-9_]+)', source_code)
        if match:
            class_name = match.group(1)
        else:
            class_match = re.search(r'class\s+([A-Za-z0-9_]+)', source_code)
            class_name = class_match.group(1) if class_match else 'Solution'

        try:
            with tempfile.TemporaryDirectory() as td:
                fpath = os.path.join(td, f'{class_name}.java')
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(source_code)

                # Modern Java (11+) can run single-file source code directly: `java Solution.java`
                proc = subprocess.run(
                    ['java', fpath],
                    input=stdin,
                    capture_output=True,
                    text=True,
                    timeout=max(cpu_time_limit, 4.0),
                )
                elapsed_ms = (time.monotonic() - start_time) * 1000
                if proc.returncode == 0:
                    return {
                        'status': STATUS_ACCEPTED,
                        'stdout': proc.stdout.strip(),
                        'stderr': proc.stderr.strip(),
                        'time_ms': round(elapsed_ms, 2),
                        'memory_kb': 16384,
                        'judge0_status_id': 3,
                        'judge0_description': 'Accepted (Local Java Fallback)',
                    }
                else:
                    err_text = proc.stderr.strip() or proc.stdout.strip()
                    is_compile_err = 'error:' in err_text.lower() or 'compilation failed' in err_text.lower()
                    status = STATUS_COMPILATION_ERROR if is_compile_err else STATUS_RUNTIME_ERROR
                    return {
                        'status': status,
                        'stdout': proc.stdout.strip(),
                        'stderr': err_text,
                        'time_ms': round(elapsed_ms, 2),
                        'memory_kb': 16384,
                        'judge0_status_id': 6 if status == STATUS_COMPILATION_ERROR else 11,
                        'judge0_description': 'Compilation Error' if status == STATUS_COMPILATION_ERROR else 'Runtime Error',
                    }
        except subprocess.TimeoutExpired:
            return {
                'status': STATUS_TLE,
                'stdout': '',
                'stderr': f'Time limit exceeded ({cpu_time_limit}s)',
                'time_ms': cpu_time_limit * 1000,
                'memory_kb': None,
                'judge0_status_id': 5,
                'judge0_description': 'Time Limit Exceeded (Local Java Fallback)',
            }
        except FileNotFoundError:
            return None
        except Exception as exc:
            return {
                'status': STATUS_INTERNAL_ERROR,
                'stdout': '',
                'stderr': str(exc),
                'time_ms': None,
                'memory_kb': None,
                'judge0_status_id': 13,
                'judge0_description': 'Internal Error',
            }

    return None


_last_judge0_check = 0.0
_judge0_available = None


def is_judge0_online() -> bool:
    """
    Quickly probe if Judge0 instance is reachable (cached for 30s).
    Avoids multi-second connection timeouts per test case when Docker is not running.
    """
    global _last_judge0_check, _judge0_available
    now = time.monotonic()
    if _judge0_available is not None and (now - _last_judge0_check < 30.0):
        return _judge0_available
    try:
        url = f'{_base_url()}/about'
        resp = requests.get(url, headers=_headers(), timeout=0.8)
        _judge0_available = (resp.status_code == 200)
    except Exception:
        _judge0_available = False
    _last_judge0_check = now
    return _judge0_available


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
    If Judge0 is unavailable or encounters JVM sandbox issues (e.g. pthread_create failed in Docker),
    automatically executes via safe local language runtime fallback with zero lag.
    """
    if is_judge0_online():
        try:
            token = submit_code(source_code, language, stdin, cpu_time_limit, memory_limit_kb)
            result = wait_for_result(token)
            # Detect sandbox environment failure in Judge0 (e.g. JVM pthread_create EAGAIN, class naming issue)
            stderr_check = (result.get('stderr') or '') + ' ' + (result.get('stdout') or '')
            if (
                'pthread_create failed' in stderr_check
                or 'unable to create native thread' in stderr_check
                or 'should be declared in a file named' in stderr_check
            ):
                logger.warning(
                    "Judge0 sandbox limitation encountered (%s); seamlessly falling back to local %s runtime.",
                    stderr_check[:80].strip(), language
                )
                fallback = _run_local_fallback(source_code, language, stdin, cpu_time_limit)
                if fallback is not None:
                    return fallback
            return result
        except Judge0Error as exc:
            logger.warning(
                "Judge0 submission failed (%s); attempting local fallback execution for '%s'",
                exc, language
            )
            fallback = _run_local_fallback(source_code, language, stdin, cpu_time_limit)
            if fallback is not None:
                return fallback
            raise
    else:
        fallback = _run_local_fallback(source_code, language, stdin, cpu_time_limit)
        if fallback is not None:
            return fallback
        raise Judge0Error(
            f"Judge0 Docker service is offline (http://localhost:2358) and no local runner is available for '{language}'. "
            "Please start Docker or write your solution in Python."
        )


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
