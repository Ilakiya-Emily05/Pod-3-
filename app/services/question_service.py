"""
Question Generation Service
Generates Easy / Medium / Hard open-ended Q&A pairs for a given keyword using OpenAI.
All questions are open-ended (no MCQ options) — designed for audio/voice answers.
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.config.settings import settings
from app.models.interview_system import DifficultyLevel


DIFFICULTY_PROMPTS = {
    DifficultyLevel.EASY: (
        "Generate 1 beginner-level open-ended interview question for the topic: '{keyword}'.\n"
        "The question should test basic definitions and concepts.\n"
        "Format your response EXACTLY as:\n"
        "QUESTION: <question text>\n"
        "IDEAL_ANSWER: <a concise ideal answer in 2-3 sentences>"
    ),
    DifficultyLevel.MEDIUM: (
        "Generate 1 intermediate-level open-ended interview question for the topic: '{keyword}'.\n"
        "The question should test practical application and problem-solving.\n"
        "Format your response EXACTLY as:\n"
        "QUESTION: <question text>\n"
        "IDEAL_ANSWER: <a concise ideal answer in 2-4 sentences>"
    ),
    DifficultyLevel.HARD: (
        "Generate 1 advanced-level open-ended interview question for the topic: '{keyword}'.\n"
        "The question should test deep expertise, system design, or architecture-level knowledge.\n"
        "Format your response EXACTLY as:\n"
        "QUESTION: <question text>\n"
        "IDEAL_ANSWER: <a thorough ideal answer in 3-5 sentences>"
    ),
}


def _get_llm() -> ChatOpenAI:
    """Build the OpenAI LLM client from settings."""
    return ChatOpenAI(
        model="gpt-4o",
        api_key=settings.OPENAI_API_KEY or "",
        temperature=0.7,
    )


def _parse_qa(response_text: str) -> tuple[str, list[str], str]:
    """Parse 'QUESTION: ... IDEAL_ANSWER: ...' format from LLM response."""
    lines = response_text.strip().splitlines()
    question = ""
    ideal_answer_lines: list[str] = []
    in_answer = False

    for line in lines:
        line_s = line.strip()
        if line_s.startswith("QUESTION:"):
            question = line_s.replace("QUESTION:", "").strip()
            in_answer = False
        elif line_s.startswith("IDEAL_ANSWER:"):
            ideal_answer_lines.append(line_s.replace("IDEAL_ANSWER:", "").strip())
            in_answer = True
        elif in_answer and line_s:
            # Multi-line ideal answers
            ideal_answer_lines.append(line_s)

    ideal_answer = " ".join(ideal_answer_lines).strip()
    return question, [], ideal_answer  # options=[] — no MCQ


async def generate_qa_for_keyword(
    keyword: str, difficulty: DifficultyLevel
) -> tuple[str, list[str], str]:
    """
    Calls OpenAI and returns (question_text, options, ideal_answer) for a keyword + difficulty.
    options is always [] — questions are open-ended for audio input.
    Returns ("", [], "") if the API key is not configured.
    """
    if not settings.OPENAI_API_KEY:
        return (
            f"[PLACEHOLDER] Explain a {difficulty.value}-level concept in {keyword}.",
            [],
            f"A solid understanding of {keyword} at the {difficulty.value} level.",
        )

    llm = _get_llm()
    prompt = DIFFICULTY_PROMPTS[difficulty].format(keyword=keyword)
    messages = [
        SystemMessage(content="You are an expert technical interviewer. Be concise and precise."),
        HumanMessage(content=prompt),
    ]
    response = await llm.ainvoke(messages)
    return _parse_qa(str(response.content))


async def evaluate_answer(question: str, ideal_answer: str, user_answer: str) -> tuple[bool, str]:
    """
    Semantically evaluates the user's transcribed audio answer against the ideal answer using LLM.
    Returns (is_correct: bool, feedback: str).
    is_correct is True if the answer demonstrates sufficient understanding.
    """
    if not settings.OPENAI_API_KEY:
        # Fallback: keyword overlap check
        overlap = len(set(user_answer.lower().split()) & set(ideal_answer.lower().split()))
        is_correct = overlap >= 3  # noqa: PLR2004
        feedback = "Good answer!" if is_correct else f"Try to cover: {ideal_answer}"
        return is_correct, feedback

    llm = ChatOpenAI(
        model="gpt-4o",
        api_key=settings.OPENAI_API_KEY or "",
        temperature=0.0,  # Deterministic for evaluation
    )
    prompt = (
        f"You are evaluating a candidate's spoken interview answer.\n\n"
        f"Question: {question}\n"
        f"Ideal Answer: {ideal_answer}\n"
        f"Candidate's Answer: {user_answer}\n\n"
        "Evaluate if the candidate's answer demonstrates adequate understanding of the concept.\n"
        "Minor omissions are acceptable; focus on correctness, not exact wording.\n\n"
        "Respond EXACTLY in this format:\n"
        "CORRECT: <yes or no>\n"
        "FEEDBACK: <one sentence of personalised, encouraging feedback>"
    )
    messages = [
        SystemMessage(content="You are a fair and encouraging technical interviewer."),
        HumanMessage(content=prompt),
    ]
    response = await llm.ainvoke(messages)
    text = str(response.content).strip()

    is_correct = False
    feedback = "Thank you for your answer."
    for line in text.splitlines():
        line_s = line.strip()
        if line_s.upper().startswith("CORRECT:"):
            is_correct = "yes" in line_s.lower()
        elif line_s.upper().startswith("FEEDBACK:"):
            feedback = line_s.replace("FEEDBACK:", "").replace("Feedback:", "").strip()

    return is_correct, feedback


async def generate_gap_analysis(session_history: list[dict]) -> str:
    """
    Generates the final Gap Analysis report for a completed mock interview.
    `session_history` is a list of dicts with keys: question, user_answer, is_correct, confidence.
    """
    if not settings.OPENAI_API_KEY:
        return (
            "[Placeholder Gap Analysis] OpenAI is not configured. "
            "Please add your credentials to .env to receive a real analysis."
        )

    llm = _get_llm()
    history_text = "\n\n".join(
        f"Q: {item['question']}\n"
        f"User Answer: {item['user_answer']}\n"
        f"Was Correct: {'Yes' if item['is_correct'] else 'No'}\n"
        f"Confidence Score: {item.get('confidence', 'N/A')}"
        for item in session_history
    )

    prompt = (
        f"Here is a mock interview transcript:\n\n{history_text}\n\n"
        "Based on this, provide a professional and encouraging gap analysis with:\n"
        "1. STRENGTHS: Topics the user answered well.\n"
        "2. WEAKNESSES: Topics where the user struggled or gave incorrect answers.\n"
        "3. RECOMMENDATIONS: Specific areas to study and improve.\n"
        "Keep each section concise and actionable."
    )
    messages = [
        SystemMessage(content="You are a professional career coach and technical interviewer."),
        HumanMessage(content=prompt),
    ]
    response = await llm.ainvoke(messages)
    return str(response.content)


async def segment_transcript(questions: list[str], transcript: str) -> dict[int, str]:
    """
    Uses LLM to split a continuous 5-minute transcript into answers for 10 sequential questions.
    Returns a mapping of question index (0-9) to answer text.
    Only returns entries for questions that were actually answered.
    """
    if not settings.OPENAI_API_KEY:
        # Fallback: Just give the whole thing to the first question
        return {0: transcript}

    llm = ChatOpenAI(
        model="gpt-4o",
        api_key=settings.OPENAI_API_KEY or "",
        temperature=0.0,
    )

    q_text = "\n".join([f"{i}. {q}" for i, q in enumerate(questions)])
    prompt = (
        f"The following is a list of sequential interview questions:\n{q_text}\n\n"
        f"The candidate provided a continuous audio response lasting about 5 minutes. "
        f"Here is the transcript:\n\n{transcript}\n\n"
        "Please segment this transcript into distinct answers for the questions provided. "
        "A candidate may have run out of time and only answered some questions. "
        "Return a JSON object where the keys are the question indices from the list above and the values are the extracted answer text. "
        "Format: { \"0\": \"answer...\", \"1\": \"answer...\" }"
    )

    messages = [
        SystemMessage(content="You are a helpful assistant that segments interview transcripts."),
        HumanMessage(content=prompt),
    ]
    response = await llm.ainvoke(messages)
    text = str(response.content).strip()

    # Simple JSON extraction from markdown if LLM includes it
    if "```json" in text:
        text = text.split("```json")[-1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[-1].split("```")[0].strip()

    import json
    try:
        data = json.loads(text)
        # Convert keys to int and ensure values are strings
        return {int(k): str(v) for k, v in data.items()}
    except (json.JSONDecodeError, ValueError):
        # Last resort fallback
        return {0: transcript}

