"""
AI Services for Interview Module:
- Text-To-Speech: edge-tts (Microsoft Azure Edge neural voices)
- Speech-To-Text: faster-whisper (fast local speech transcription)
- LLM: Llama 3 (via local Ollama, Groq, or OpenAI-compatible endpoint with adaptive fallback)
"""
import io
import os
import logging
import asyncio
import tempfile
import urllib.request
import json
from typing import Optional

logger = logging.getLogger(__name__)

# Cache faster-whisper model instance in memory
_whisper_model = None


# ── Text to Speech (edge-tts) ──────────────────────────────────────────────────

async def _synthesize_edge_tts(text: str, voice: str = "en-US-AriaNeural") -> bytes:
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    buffer = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buffer.write(chunk["data"])
    return buffer.getvalue()


def generate_edge_tts_audio(text: str, voice: str = "en-US-AriaNeural") -> bytes:
    """
    Generate MP3 audio for given text using edge-tts.
    Runs asynchronously and returns raw audio bytes.
    """
    clean_text = text.strip()
    if not clean_text:
        return b""
    try:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(asyncio.run, _synthesize_edge_tts(clean_text, voice)).result()
            else:
                return loop.run_until_complete(_synthesize_edge_tts(clean_text, voice))
        except RuntimeError:
            return asyncio.run(_synthesize_edge_tts(clean_text, voice))
    except Exception as exc:
        logger.error("edge-tts generation failed: %s", exc)
        return b""


# ── Speech to Text (faster-whisper) ───────────────────────────────────────────

TECHNICAL_VOCAB_PROMPT = (
    "Software engineering technical interview. "
    "Key vocabulary: Python, Java, JavaScript, TypeScript, React, Next.js, Node.js, Django, "
    "HTML, CSS, OpenCV, Machine Learning, Deep Learning, Generative AI, Prompt Engineering, "
    "DSA, Data Structures, Algorithms, SQL, PostgreSQL, MongoDB, Git, GitHub, REST APIs, "
    "Frontend, Backend, Full Stack, Computer Science, B.Tech, CGPA, Narayana, Bhashyam, Krify, "
    "Scientific Calculator, OOP, Object Oriented Programming, AWS, Docker, Kubernetes."
)


def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            logger.info("Loading faster-whisper (base.en) model...")
            _whisper_model = WhisperModel("base.en", device="cpu", compute_type="int8")
            logger.info("faster-whisper (base.en) model loaded successfully.")
        except Exception as exc:
            logger.error("Failed to load faster-whisper model: %s", exc)
            return None
    return _whisper_model


def transcribe_audio_faster_whisper(audio_bytes: bytes) -> str:
    """
    Transcribe audio bytes (WAV, MP3, WebM) into text using faster-whisper
    with technical vocabulary biasing.
    """
    if not audio_bytes:
        return ""

    model = get_whisper_model()
    if not model:
        logger.warning("faster-whisper model unavailable")
        return ""

    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        segments, _info = model.transcribe(
            tmp_path,
            beam_size=3,
            language="en",
            initial_prompt=TECHNICAL_VOCAB_PROMPT,
        )
        transcribed_text = " ".join(seg.text.strip() for seg in segments).strip()
        logger.info("Transcribed audio (%d bytes) -> %s", len(audio_bytes), transcribed_text[:80])
        return transcribed_text
    except Exception as exc:
        logger.error("faster-whisper transcription failed: %s", exc)
        return ""
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


# ── LLM (Llama 3 via Groq API, Local Ollama, or OpenAI) ───────────────────────

def _get_env(key: str, default: str = "") -> str:
    val = os.environ.get(key, "").strip()
    if not val:
        # Also check backend/.env file directly if not exported in shell
        try:
            env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
            if os.path.exists(env_path):
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith(f"{key}="):
                            val = line.split("=", 1)[1].strip().strip('"').strip("'")
                            break
        except Exception:
            pass
    return val or default


def query_llama3(prompt: str, system_prompt: str = "") -> Optional[str]:
    """
    Query LLM (Llama 3 / OpenAI / Ollama).
    Checks:
      1. Groq Cloud API if GROQ_API_KEY is configured (free & ultra-fast Llama 3)
      2. OpenAI API if OPENAI_API_KEY is configured
      3. Local Ollama instance (http://localhost:11434)
      4. Returns None on failure so caller can use smart contextual engine
    """
    groq_api_key = _get_env("GROQ_API_KEY")
    openai_api_key = _get_env("OPENAI_API_KEY")
    ollama_url = _get_env("OLLAMA_URL", "http://localhost:11434/api/generate")
    ollama_model = _get_env("OLLAMA_MODEL", "llama3")

    # 1. Try Groq Cloud if API key available (Free & Blazing Fast)
    if groq_api_key:
        candidate_models = ["openai/gpt-oss-120b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant", "qwen/qwen3.8-27b"]
        for model_name in candidate_models:
            try:
                groq_url = "https://api.groq.com/openai/v1/chat/completions"
                groq_payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt or "You are an expert technical interviewer."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.6,
                    "max_tokens": 300,
                }
                data = json.dumps(groq_payload).encode("utf-8")
                req = urllib.request.Request(
                    groq_url,
                    data=data,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {groq_api_key}",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) QAIP/1.0",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200:
                        res = json.loads(resp.read().decode("utf-8"))
                        text = res["choices"][0]["message"]["content"].strip()
                        logger.info("Generated question from Groq (%s)", model_name)
                        return text
            except Exception as exc:
                logger.debug("Groq %s attempt failed: %s", model_name, exc)
                continue

    # 2. Try OpenAI API if key available
    if openai_api_key:
        try:
            openai_url = "https://api.openai.com/v1/chat/completions"
            openai_payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt or "You are an expert technical interviewer."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.6,
                "max_tokens": 300,
            }
            data = json.dumps(openai_payload).encode("utf-8")
            req = urllib.request.Request(
                openai_url,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {openai_api_key}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=6) as resp:
                if resp.status == 200:
                    res = json.loads(resp.read().decode("utf-8"))
                    text = res["choices"][0]["message"]["content"].strip()
                    logger.info("Generated question from OpenAI API")
                    return text
        except Exception as exc:
            logger.warning("OpenAI API query failed: %s", exc)

    # 3. Try local Ollama Llama 3
    try:
        payload = {
            "model": ollama_model,
            "prompt": f"{system_prompt}\n\n{prompt}" if system_prompt else prompt,
            "stream": False,
            "options": {"temperature": 0.7, "num_predict": 256},
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            ollama_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            if resp.status == 200:
                result = json.loads(resp.read().decode("utf-8"))
                response_text = result.get("response", "").strip()
                if response_text:
                    logger.info("Generated question from local Ollama Llama 3")
                    return response_text
    except Exception as exc:
        logger.debug("Local Ollama Llama 3 not available: %s", exc)

    return None


def generate_llm_interview_question(
    candidate_name: str,
    target_role: str,
    resume_skills: list[str],
    resume_projects: list[str],
    current_phase: str,
    turn_number: int,
    difficulty: str,
    last_question_text: str = "",
    last_answer_text: str = "",
    last_score: Optional[float] = None,
    session_type: str = "mixed",
) -> dict:
    """
    Generate dynamic, contextual interview questions using an LLM.
    - Non-coding Turn 1: Warm human introduction
    - Coding session Turn 1: Coding-focused opener (NOT warmup)
    - Turn 2+: Contextual questions building on candidate's actual verbal answers
    """
    # ── Turn 1 for CODING sessions — skip warmup, go straight to coding ────────
    if turn_number <= 1 and session_type == 'coding':
        return {
            "question_text": (
                f"Welcome{f', {candidate_name}' if candidate_name else ''}! "
                "Let's get straight into the coding round. "
                "I'll present you with a programming problem. "
                "Take a moment to understand the problem, then write your solution. "
                "Feel free to ask for clarification if needed."
            ),
            "topic": "coding_introduction",
            "phase": "coding",
            "difficulty": difficulty,
            "question_type": "coding",
            "expected_concepts": ["algorithm", "problem_solving", "code"],
        }

    # ── Turn 1 for ALL OTHER sessions is ALWAYS the welcoming personal intro ───
    if turn_number <= 1:
        return {
            "question_text": "Hello! Welcome to your interview today. Could you please start by introducing yourself, stating your full name, your educational background, and what role you are aiming for?",
            "topic": "introduction",
            "phase": "warmup",
            "difficulty": "easy",
            "question_type": "situational",
            "expected_concepts": ["name", "background", "education", "goals", "skills"],
        }


    # ── Turn 2+ Query LLM for next dynamic question / follow-up ────────────────
    system_prompt = (
        "You are an expert AI Technical Interviewer conducting a realistic, conversational 1-on-1 interview. "
        "Your goal is to evaluate the candidate's authentic skills through dynamic, adaptive questions. "
        "Listen to what the candidate just said and build directly on their response. "
        "Rules:\n"
        "1. Ask exactly ONE clear, conversational question.\n"
        "2. Keep the question concise (1-2 sentences maximum) so it is easy to listen to.\n"
        "3. Address the candidate naturally by name if appropriate.\n"
        "4. DO NOT include greetings like 'Thank you for answering' or 'Next question:'.\n"
        "5. Output ONLY the question text itself. Do not add quotes, markdown, or commentary."
    )

    skills_str = ", ".join(resume_skills[:6]) if resume_skills else "Software Engineering"
    projects_str = ", ".join(resume_projects[:3]) if resume_projects else "Technical Projects"

    user_prompt = (
        f"Candidate Name: {candidate_name or 'Candidate'}\n"
        f"Target Role: {target_role or 'Software Engineer'}\n"
        f"Resume Skills: {skills_str}\n"
        f"Resume Projects: {projects_str}\n"
        f"Current Phase: {current_phase} (warmup, technical, project, hr, closing)\n"
        f"Difficulty: {difficulty}\n"
        f"Turn Number: {turn_number}\n\n"
        f"Previous Question Asked: {last_question_text}\n"
        f"Candidate's Verbal Answer: {last_answer_text or 'Introduced themselves'}\n\n"
        f"Generate the next logical interview question or follow-up. "
        f"If the candidate mentioned technologies (like Python, React, OpenCV, etc.), ask them how they used them or ask an in-depth architectural question."
    )

    llm_response = query_llama3(user_prompt, system_prompt)

    if llm_response:
        # Clean response
        clean_q = llm_response.strip().strip('"').strip("'").strip()
        # Remove any leading labels
        for prefix in ["Question:", "Interviewer:", "Next Question:", "Q:"]:
            if clean_q.lower().startswith(prefix.lower()):
                clean_q = clean_q[len(prefix):].strip()

        if len(clean_q) > 20 and "?" in clean_q:
            logger.info("Successfully generated dynamic LLM question for turn %d", turn_number)
            # Infer expected concepts from skills and question words
            concepts = [w.lower() for w in clean_q.replace("?", "").split() if len(w) > 4][:5]
            if resume_skills:
                concepts.extend([s.lower() for s in resume_skills[:3]])
            return {
                "question_text": clean_q,
                "topic": current_phase,
                "phase": current_phase,
                "difficulty": difficulty,
                "question_type": "conceptual" if current_phase == "technical" else "project",
                "expected_concepts": list(set(concepts)),
            }

    # ── Smart Contextual Fallback (Uses actual resume & answer dynamically) ───
    logger.info("Using smart contextual question generator for turn %d", turn_number)
    primary_skill = resume_skills[0] if resume_skills else "software engineering"
    second_skill = resume_skills[1] if len(resume_skills) > 1 else "database design"
    primary_project = resume_projects[0] if resume_projects else "your primary application"

    # Contextual progression
    if turn_number == 2:
        clean_q = (
            f"Thank you {candidate_name or ''}. You mentioned your experience with {primary_skill}. "
            f"Could you walk me through a notable project where you implemented {primary_skill} and explain the technical challenges you solved?"
        ).strip()
        topic = "project architecture"
    elif current_phase == "project":
        clean_q = (
            f"Regarding {primary_project}, could you explain the overall system architecture, "
            f"how you structured your data flow, and how you ensured high performance?"
        )
        topic = "system design"
    elif current_phase == "technical":
        clean_q = (
            f"In your work with {second_skill} and {primary_skill}, how do you approach debugging, "
            f"error handling, and optimizing performance under heavy load?"
        )
        topic = "optimization"
    elif current_phase == "hr":
        clean_q = (
            "Tell me about a time when you had to work under a tight deadline or resolve a disagreement with a team member. How did you handle it?"
        )
        topic = "behavioral"
    else:
        clean_q = (
            "Thank you for sharing your experience. As we conclude, do you have any questions for me regarding the role or the engineering team?"
        )
        topic = "closing"

    return {
        "question_text": clean_q,
        "topic": topic,
        "phase": current_phase,
        "difficulty": difficulty,
        "question_type": "conceptual",
        "expected_concepts": [primary_skill.lower(), "architecture", "performance", "challenges"],
    }
