
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

# In-memory LRU cache for synthesized TTS audio (max 200 items)
_tts_cache: dict[str, bytes] = {}
_MAX_TTS_CACHE_SIZE = 200

# High-quality neural voice candidates for automatic fallback
DEFAULT_TTS_VOICE = "en-US-AriaNeural"
VOICE_FALLBACKS = [
    "en-US-AriaNeural",
    "en-US-JennyNeural",
    "en-US-ChristopherNeural",
    "en-US-GuyNeural",
    "en-GB-SoniaNeural",
]


def _clean_tts_text(text: str) -> str:
    """
    Sanitize question text for clean, natural speech synthesis.
    Strips raw markdown, bracketed tags, and converts special sentinels.
    """
    import re
    if not text:
        return ""
    t = text.strip()
    if "[CODING_PROBLEM]" in t:
        return "Here is your coding challenge. Please review the problem description on your screen and implement your solution in the editor."
    # Remove markdown bold/italic asterisks (*), backticks (`), and headers (#)
    t = re.sub(r'[*`#]', '', t)
    # Remove standalone italic markdown underscores (_word_ -> word) without altering identifiers (select_related)
    t = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'\1', t)
    # Remove bracketed metadata tags like [Candidate Name: ...] or [Resume Projects: ...]
    t = re.sub(r'\[.*?\]', '', t)
    # Normalize whitespaces
    t = re.sub(r'\s+', ' ', t).strip()
    return t


# ── Text to Speech (edge-tts) ──────────────────────────────────────────────────

async def _synthesize_edge_tts(text: str, voice: str = DEFAULT_TTS_VOICE) -> bytes:
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    buffer = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buffer.write(chunk["data"])
    return buffer.getvalue()


def generate_edge_tts_audio(text: str, voice: str = DEFAULT_TTS_VOICE) -> bytes:
    """
    Generate MP3 audio for given text using edge-tts.
    Features:
      - Memory caching for zero-latency repeats
      - Multi-voice fallbacks if Microsoft Edge endpoint throttles
      - Text sanitization for crystal clear natural speech
    """
    clean_text = _clean_tts_text(text)
    if not clean_text:
        return b""

    requested_voice = voice or DEFAULT_TTS_VOICE
    cache_key = f"{requested_voice}:{clean_text}"

    # 1. Return from in-memory cache if available
    if cache_key in _tts_cache:
        logger.debug("TTS cache hit for: %s...", clean_text[:40])
        return _tts_cache[cache_key]

    # 2. Build candidate voice list with requested voice first
    candidate_voices = [requested_voice]
    for v in VOICE_FALLBACKS:
        if v not in candidate_voices:
            candidate_voices.append(v)

    # 3. Attempt synthesis with fallback voices
    for candidate_voice in candidate_voices:
        try:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        audio_data = pool.submit(asyncio.run, _synthesize_edge_tts(clean_text, candidate_voice)).result()
                else:
                    audio_data = loop.run_until_complete(_synthesize_edge_tts(clean_text, candidate_voice))
            except RuntimeError:
                audio_data = asyncio.run(_synthesize_edge_tts(clean_text, candidate_voice))

            if audio_data and len(audio_data) > 200:
                # Store in cache
                if len(_tts_cache) >= _MAX_TTS_CACHE_SIZE:
                    _tts_cache.pop(next(iter(_tts_cache)))
                _tts_cache[cache_key] = audio_data
                logger.info("edge-tts generated %d bytes with voice '%s'", len(audio_data), candidate_voice)
                return audio_data
        except Exception as exc:
            logger.warning("edge-tts synthesis failed with voice '%s': %s", candidate_voice, exc)
            continue

    logger.error("All edge-tts voice candidates failed for text: %s", clean_text[:60])
    return b""


# ── Speech to Text (faster-whisper) ───────────────────────────────────────────

def build_dynamic_vocab_prompt(
    target_role: str = "",
    resume_skills: Optional[list[str]] = None,
    job_description: str = "",
) -> str:
    """
    Build role-adaptive speech recognition prompt for faster-whisper.
    Dynamically extracts vocabulary from the target role, candidate's resume, and JD,
    making the recognition accurate across any profession (tech, product, marketing, finance, HR).
    """
    skills = resume_skills or []
    terms = []
    if target_role:
        terms.append(target_role)
    if skills:
        terms.extend(skills[:15])

    if job_description:
        import re
        # Extract capitalized domain terms, tools, and acronyms from the Job Description
        matches = re.findall(r'\b[A-Z][a-zA-Z0-9\+\#\.\/\-]{2,}\b', job_description)
        stop_words = {
            'the', 'and', 'for', 'with', 'you', 'our', 'will', 'this', 'that',
            'from', 'have', 'are', 'your', 'about', 'team', 'work', 'role'
        }
        for m in matches:
            if len(m) <= 25 and m.lower() not in stop_words and m not in terms:
                terms.append(m)
            if len(terms) >= 35:
                break

    role_phrase = f"{target_role} professional interview" if target_role else "Professional interview"
    vocab_list = ", ".join(terms[:35]) if terms else "professional experience, projects, skills, education, leadership"
    return f"{role_phrase}. Key vocabulary: {vocab_list}."


TECHNICAL_VOCAB_PROMPT = build_dynamic_vocab_prompt(
    "Software Engineering",
    ["Python", "Java", "JavaScript", "TypeScript", "React", "Next.js", "Django", "DSA", "System Design"],
    "Software Engineer Technical Interview"
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


def transcribe_audio_faster_whisper(audio_bytes: bytes, vocab_prompt: Optional[str] = None) -> str:
    """
    Transcribe audio bytes (WAV, MP3, WebM) into text using faster-whisper
    with dynamic vocabulary biasing and voice activity detection (VAD).
    """
    if not audio_bytes or len(audio_bytes) < 400:
        return ""

    model = get_whisper_model()
    if not model:
        logger.warning("faster-whisper model unavailable")
        return ""

    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    prompt_to_use = vocab_prompt or TECHNICAL_VOCAB_PROMPT

    try:
        segments, _info = model.transcribe(
            tmp_path,
            beam_size=3,
            language="en",
            initial_prompt=prompt_to_use,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=400),
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
                    "max_tokens": 512,
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
                "max_tokens": 512,
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
            "options": {"temperature": 0.7, "num_predict": 512},
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


def generate_natural_feedback(
    question_text: str,
    candidate_answer: str,
    expected_concepts: Optional[list[str]] = None,
    score: float = 0.5,
    phase: str = "technical",
) -> str:
    """
    Generate immediate, natural, conversational spoken feedback for the candidate's answer.
    Very natural and human-like: gently corrects errors (e.g. 'CN' -> 'Actually, CN stands for Computer Networks.'),
    warmly affirms good answers, and stays concise (1-2 sentences maximum).
    """
    expected_concepts = expected_concepts or []
    expected_str = ", ".join(expected_concepts) if expected_concepts else "technical clarity and accuracy"

    system_prompt = (
        "You are an empathetic, concise, and expert human technical interviewer giving immediate verbal feedback in an interview room.\n"
        "Rules:\n"
        "1. Speak directly to the candidate in 1 or 2 natural, conversational sentences (maximum 25 words).\n"
        "2. If the candidate made an error, had a misconception, or gave an incorrect definition/expansion "
        "(e.g. said 'cloud networks' when asked for 'CN'), gently and directly state the correct answer "
        "(e.g. 'Actually, CN stands for Computer Networks.').\n"
        "3. If the candidate answered correctly, affirm it naturally without robotic praise "
        "(e.g. 'Spot on, exactly right.' or 'Nice explanation, you covered that well.').\n"
        "4. If the candidate gave a partial or vague answer, acknowledge their attempt and clarify the key missing concept conversationally.\n"
        "5. Never output numbers, scores, bullet points, markdown, or greetings like 'Candidate:'. Output ONLY the spoken reaction itself."
    )

    user_prompt = (
        f"Question Asked: {question_text}\n"
        f"Candidate's Answer: {candidate_answer}\n"
        f"Expected Concepts: {expected_str}\n"
        f"Answer Score: {score:.2f} (0.0=incorrect, 1.0=perfect)\n\n"
        "Provide your immediate, natural 1-2 sentence spoken feedback to the candidate:"
    )

    llm_resp = query_llama3(user_prompt, system_prompt)
    if llm_resp:
        clean = llm_resp.strip().strip('"').strip("'").strip()
        for prefix in ["Feedback:", "Interviewer:", "Correction:", "AI:"]:
            if clean.lower().startswith(prefix.lower()):
                clean = clean[len(prefix):].strip()
        if len(clean) >= 6:
            logger.info("Generated natural feedback via LLM: %s", clean)
            return clean

    # ── Conversational Contextual Fallback (Natural, Generic & Empathetic) ────
    if score < 0.35:
        if expected_concepts:
            primary = expected_concepts[0].strip()
            formatted_concept = primary.title() if len(primary) <= 25 else primary
            return f"Actually, the correct answer is {formatted_concept}."
        return "That's a good attempt, but keep in mind the fundamental definitions here."
    elif score >= 0.70:
        if expected_concepts:
            return f"Good answer! Spot on, you covered {expected_concepts[0]} very well."
        return "Great answer, you explained that clearly and accurately."
    else:
        if expected_concepts:
            return f"Good start. In addition to what you mentioned, remember that {expected_concepts[0]} is also key here."
        return "Good explanation, you're definitely on the right track."


def generate_interviewer_answer_to_candidate_question(
    candidate_question: str,
    target_role: str = "",
    job_description: str = "",
    candidate_name: str = "",
) -> str:
    """
    Generate an authentic, in-character spoken response when the candidate asks a question in the closing phase.
    The interviewer (Alex) answers the candidate's question warmly using context from the Job Description and role,
    then provides a gracious closing farewell.
    """
    interviewer_name = "Alex"
    system_prompt = (
        f"You are {interviewer_name}, an empathetic, senior interviewer conducting an authentic 1-on-1 interview.\n"
        "The candidate has reached the final Q&A stage of the interview and just asked you a question about the role, team, or company.\n"
        "Rules:\n"
        "1. Speak naturally and warmly directly to the candidate in 2 to 3 spoken sentences (maximum 45 words).\n"
        "2. Answer their question authentically based on the Job Description and role context provided.\n"
        "3. Conclude with a warm parting closing thanking them for their time and letting them know the recruiting team will follow up soon.\n"
        "4. Never output labels like 'Interviewer:', 'AI:', bullet points, or markdown. Output ONLY the spoken response."
    )
    user_prompt = (
        f"Candidate Name: {candidate_name or 'Candidate'}\n"
        f"Target Role: {target_role or 'this position'}\n"
        f"Job Description context: {job_description[:600] if job_description else 'Innovative and collaborative team culture'}\n\n"
        f"Candidate's Question: {candidate_question}\n\n"
        "Provide your warm, in-character spoken answer and closing farewell:"
    )
    llm_resp = query_llama3(user_prompt, system_prompt)
    if llm_resp:
        clean = llm_resp.strip().strip('"').strip("'").strip()
        for prefix in ["Alex:", "Interviewer:", "Answer:", "AI:"]:
            if clean.lower().startswith(prefix.lower()):
                clean = clean[len(prefix):].strip()
        if len(clean) >= 20:
            return clean

    # Fallback answer
    candidate_part = f", {candidate_name}" if candidate_name else ""
    return (
        f"That's a fantastic question! In this role, you'll be collaborating closely with our cross-functional team on high-impact initiatives. "
        f"Thank you so much for your time and thoughtful responses today{candidate_part}. It was a real pleasure speaking with you, "
        "and our team will be in touch with next steps soon. Have a wonderful rest of your day!"
    )


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
    job_description: str = "",
    uncovered_topics: Optional[list[str]] = None,
    covered_topics: Optional[list[str]] = None,
    remaining_time_seconds: Optional[int] = None,
    remaining_turns: Optional[int] = None,
) -> dict:
    """
    Generate dynamic, contextual interview questions using an LLM.
    Synthesizes ALL holistic factors:
      - Interviewer Persona (Alex) with natural conversational transitions
      - Any Domain / Role (Software, Product, Design, Data, Business, Marketing)
      - Resume (skills, past projects, experience)
      - Job Description (core role requirements & competencies)
      - Topics Uncovered (ensuring broad evaluation without lingering on one tangent)
      - Remaining Time & Turns (temporal awareness and interview pacing)
      - Previous Answer (conversational bridge, simplifying on struggles, probing deeper on strengths)
    """
    interviewer_name = "Alex"

    # ── Turn 1 for CODING sessions — skip warmup, go straight to coding ────────
    if turn_number <= 1 and session_type == 'coding':
        return {
            "question_text": (
                f"Welcome{f', {candidate_name}' if candidate_name else ''}! "
                f"My name is {interviewer_name}. Let's get straight into the coding round. "
                "I'll present you with a programming problem on your screen. "
                "Take a moment to understand the problem, then write your solution. "
                "Feel free to ask for clarification if needed."
            ),
            "topic": "coding_introduction",
            "phase": "coding",
            "difficulty": difficulty,
            "question_type": "coding",
            "expected_concepts": ["algorithm", "problem_solving", "code"],
        }

    # ── Turn 1 for ALL OTHER sessions — Welcoming Personal Introduction & Agenda ───
    if turn_number <= 1:
        target_mention = f" for the {target_role} position" if target_role else ""
        candidate_greeting = f"Hi {candidate_name}, " if candidate_name else "Hello, "
        return {
            "question_text": (
                f"{candidate_greeting}welcome! My name is {interviewer_name}, and I'll be conducting your interview today{target_mention}. "
                "We have about 30 minutes together. We'll start with a brief overview of your background, explore some of your past work and projects, "
                "dive into core domain scenarios, and save the last few minutes for any questions you might have for me. "
                "To kick off, could you briefly introduce yourself, walk me through your background, and share what brings you to this role?"
            ),
            "topic": "introduction",
            "phase": "warmup",
            "difficulty": "easy",
            "question_type": "situational",
            "expected_concepts": ["name", "background", "education", "goals", "skills", "experience"],
        }

    # ── Closing Phase — Candidate Q&A ("Do you have any questions for me?") ────
    if current_phase == "closing":
        candidate_mention = f", {candidate_name}" if candidate_name else ""
        return {
            "question_text": (
                f"Thank you for sharing your experience with me today{candidate_mention}. "
                "We've covered a lot of ground, and we have a few minutes left. "
                "I'd love to open the floor to you: do you have any questions for me about the role, our team, or the company?"
            ),
            "topic": "candidate_qa",
            "phase": "closing",
            "difficulty": "easy",
            "question_type": "situational",
            "expected_concepts": ["questions", "role", "team", "culture", "company"],
        }

    # ── Turn 2+ Query LLM for next dynamic question balancing ALL factors ───────
    system_prompt = (
        f"You are {interviewer_name}, an expert, empathetic human interviewer conducting a realistic 1-on-1 interview.\n"
        "Your mission is to formulate the next interview question by synthesizing ALL of the following factors:\n"
        "1. CONVERSATIONAL BRIDGES: Always bridge smoothly from what the candidate just answered with natural transitions "
        "(e.g., 'That's a great point on...', 'Building on what you mentioned about...', 'Let's shift gears to...').\n"
        "2. ROLE & JOB DESCRIPTION: Tailor questions directly to the target role (technical, product, data, business, or operational) "
        "and the specific competencies outlined in the Job Description.\n"
        "3. RESUME & PROJECTS: Probe into their stated skills, tools, and past projects.\n"
        "4. TOPIC COVERAGE: Prioritize UNCOVERED competencies to maintain a well-rounded evaluation.\n"
        "5. PACING & REMAINING TIME: Be aware of remaining time and questions so all key areas are evaluated.\n"
        "Rules:\n"
        "1. Ask exactly ONE clear, conversational question (1-2 sentences maximum).\n"
        "2. Speak in the first person as Alex ('I'd love to know...', 'Could you tell me...').\n"
        "3. Address the candidate naturally by name when appropriate.\n"
        "4. Output ONLY the question text itself. Do not add quotes, markdown, or commentary."
    )

    skills_str = ", ".join(resume_skills[:8]) if resume_skills else "Domain Competencies"
    projects_str = ", ".join(resume_projects[:4]) if resume_projects else "Past Projects"

    jd_section = f"Job Description / Key Requirements:\n{job_description[:1200].strip()}\n\n" if job_description else ""

    uncovered_list = uncovered_topics or []
    covered_list = covered_topics or []
    uncovered_str = ", ".join(uncovered_list[:6]) if uncovered_list else "All core topics touched; probe deeper into domain skills"
    covered_str = ", ".join(covered_list[:6]) if covered_list else "None yet (initial round)"

    mins_left = (remaining_time_seconds // 60) if remaining_time_seconds is not None else 15
    turns_left = remaining_turns if remaining_turns is not None else 5
    pacing_str = f"Time Remaining: ~{mins_left} mins | Questions Remaining: {turns_left}"

    is_weak = last_score is not None and last_score < 0.35
    score_guidance = (
        "The candidate struggled or gave an incomplete answer on the previous turn. "
        "Acknowledge the concept and ask a simpler fundamental question, then steer toward an uncovered requirement."
        if is_weak
        else "The candidate responded well. Build upon their answer or smoothly pivot to an essential uncovered requirement from the JD/resume."
    )

    user_prompt = (
        f"Candidate Name: {candidate_name or 'Candidate'}\n"
        f"Target Role: {target_role or 'Professional Role'}\n"
        f"Pacing & Time: {pacing_str}\n"
        f"{jd_section}"
        f"Resume Skills: {skills_str}\n"
        f"Resume Projects: {projects_str}\n"
        f"Already Covered Topics: {covered_str}\n"
        f"PRIORITY UNCOVERED TOPICS (Test these next): {uncovered_str}\n"
        f"Current Phase: {current_phase} | Difficulty: {difficulty} | Turn: {turn_number}\n\n"
        f"Previous Question Asked: {last_question_text}\n"
        f"Candidate's Previous Answer: {last_answer_text or 'Introduced themselves'}\n"
        f"Answer Score: {last_score if last_score is not None else 'N/A'}\n\n"
        f"Guidance: {score_guidance}\n\n"
        "Generate the next question by balancing ALL factors: bridge naturally from the previous answer, "
        "target an uncovered competency from the Job Description / Resume, and respect the remaining time."
    )

    llm_response = query_llama3(user_prompt, system_prompt)

    if llm_response:
        clean_q = llm_response.strip().strip('"').strip("'").strip()
        for prefix in ["Question:", "Alex:", "Interviewer:", "Next Question:", "Q:"]:
            if clean_q.lower().startswith(prefix.lower()):
                clean_q = clean_q[len(prefix):].strip()

        if len(clean_q) > 20:
            if not clean_q.endswith("?"):
                clean_q += "?"
            logger.info("Successfully generated dynamic LLM question for turn %d", turn_number)
            concepts = [w.lower() for w in clean_q.replace("?", "").split() if len(w) > 4][:5]
            if resume_skills:
                concepts.extend([s.lower() for s in resume_skills[:4]])
            return {
                "question_text": clean_q,
                "topic": current_phase,
                "phase": current_phase,
                "difficulty": difficulty,
                "question_type": "conceptual" if current_phase in ("technical", "case_study") else "project",
                "expected_concepts": list(set(concepts)),
            }

    # ── Smart Contextual Fallback (Synthesizes Resume, JD, Time, & Uncovered Topics) ──
    logger.info("Using smart contextual question generator for turn %d", turn_number)
    primary_skill = resume_skills[0] if resume_skills else "core competencies"
    second_skill = resume_skills[1] if len(resume_skills) > 1 else "domain knowledge"
    primary_project = resume_projects[0] if resume_projects else "your primary project"

    clean_words = [
        w.strip(",.!?\"'").lower() for w in (last_answer_text or "").split()
        if len(w) > 3 and w.lower() not in {
            "this", "that", "with", "have", "from", "they", "will", "about",
            "would", "there", "their", "what", "which", "when", "where",
            "could", "should", "think", "maybe", "pretty", "really", "basic"
        }
    ]
    key_topic = " ".join(clean_words[:2]) if clean_words else (primary_skill if resume_skills else "this concept")

    # Pick the next high-priority uncovered topic from JD or Resume
    next_uncovered = (
        uncovered_topics[0] if uncovered_topics
        else (resume_skills[1] if len(resume_skills) > 1 else primary_skill)
    )

    # 1. If candidate gave a weak answer on previous question:
    if last_answer_text and last_score is not None and last_score < 0.35:
        clean_q = f"Let's break that down with a simpler question: can you explain what {key_topic} is used for and why it matters in your domain?"
        topic = f"{key_topic} fundamentals"

    # 2. If time / turns are running low (1-2 questions left or under 5 mins), ask a high-impact synthesis question:
    elif remaining_turns is not None and remaining_turns <= 2 and current_phase not in ("closing", "hr"):
        clean_q = (
            f"With our remaining time, I'd like to touch on {next_uncovered}, which is key for the {target_role} role. "
            f"Could you summarize your practical experience with {next_uncovered} and the key trade-offs you consider?"
        )
        topic = f"{next_uncovered} synthesis"

    # 3. If in project phase and resume project exists:
    elif current_phase == "project" and primary_project:
        clean_q = (
            f"Regarding your work on {primary_project}, and connecting to what you mentioned about {key_topic}: "
            f"could you walk me through the overall design, how you structured your deliverables, and what measurable impact you achieved?"
        )
        topic = f"{primary_project} design"

    # 4. If in technical/case_study phase and we have uncovered topics from JD/Resume:
    elif current_phase in ("technical", "case_study"):
        clean_q = (
            f"You touched on {key_topic}. Another critical requirement for this role is {next_uncovered}. "
            f"How have you applied {next_uncovered} in real-world scenarios, and how do you handle unexpected challenges or edge cases?"
        )
        topic = next_uncovered

    # 5. Standard contextual progression building from answer and resume:
    elif turn_number == 2:
        clean_q = (
            f"Thank you {candidate_name or ''}. You highlighted your experience with {primary_skill}. "
            f"Could you walk me through a notable project or initiative where you applied {primary_skill} and explain the key challenges you resolved?"
        ).strip()
        topic = "project deep-dive"

    elif current_phase == "hr":
        clean_q = (
            "Tell me about a time when you had to work under a tight deadline or resolve a disagreement with a team member. How did you navigate it?"
        )
        topic = "behavioral"

    else:
        clean_q = (
            f"Thank you for sharing your experience with me today{f', {candidate_name}' if candidate_name else ''}. "
            "We have a few minutes left, and I'd love to open the floor to you: do you have any questions for me about the role or our team?"
        )
        topic = "candidate_qa"

    return {
        "question_text": clean_q,
        "topic": topic,
        "phase": current_phase,
        "difficulty": difficulty,
        "question_type": "conceptual",
        "expected_concepts": [next_uncovered.lower(), key_topic.lower(), primary_skill.lower()],
    }
