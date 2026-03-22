"""
Question Generation Service
Generates Easy / Medium / Hard Q&A pairs for a given keyword using Azure OpenAI.
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.config.settings import settings
from app.models.interview_system import DifficultyLevel


DIFFICULTY_PROMPTS = {
    DifficultyLevel.EASY: (
        "Generate 1 beginner-level multiple-choice interview question for the topic: '{keyword}'.\n"
        "The question should test basic definitions and concepts.\n"
        "Format your response EXACTLY as:\n"
        "QUESTION: <question text>\n"
        "A: <option 1>\n"
        "B: <option 2>\n"
        "C: <option 3>\n"
        "D: <option 4>\n"
        "ANSWER: <A, B, C, or D>"
    ),
    DifficultyLevel.MEDIUM: (
        "Generate 1 intermediate-level multiple-choice interview question for the topic: '{keyword}'.\n"
        "The question should test practical application and problem-solving.\n"
        "Format your response EXACTLY as:\n"
        "QUESTION: <question text>\n"
        "A: <option 1>\n"
        "B: <option 2>\n"
        "C: <option 3>\n"
        "D: <option 4>\n"
        "ANSWER: <A, B, C, or D>"
    ),
    DifficultyLevel.HARD: (
        "Generate 1 advanced-level multiple-choice interview question for the topic: '{keyword}'.\n"
        "The question should test deep expertise, system design, or architecture-level knowledge.\n"
        "Format your response EXACTLY as:\n"
        "QUESTION: <question text>\n"
        "A: <option 1>\n"
        "B: <option 2>\n"
        "C: <option 3>\n"
        "D: <option 4>\n"
        "ANSWER: <A, B, C, or D>"
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
    """Parse 'QUESTION: ... A: ... ANSWER: ...' format from LLM response."""
    lines = response_text.strip().splitlines()
    question, answer_key = "", ""
    options_dict = {}
    for line in lines:
        line_s = line.strip()
        if line_s.startswith("QUESTION:"):
            question = line_s.replace("QUESTION:", "").strip()
        elif line_s.startswith("A:"):
            options_dict["A"] = line_s.replace("A:", "").strip()
        elif line_s.startswith("B:"):
            options_dict["B"] = line_s.replace("B:", "").strip()
        elif line_s.startswith("C:"):
            options_dict["C"] = line_s.replace("C:", "").strip()
        elif line_s.startswith("D:"):
            options_dict["D"] = line_s.replace("D:", "").strip()
        elif line_s.startswith("ANSWER:"):
            answer_key = line_s.replace("ANSWER:", "").strip()
    
    options = [
        options_dict.get("A", ""),
        options_dict.get("B", ""),
        options_dict.get("C", ""),
        options_dict.get("D", "")
    ]
    return question, options, answer_key


async def generate_qa_for_keyword(
    keyword: str, difficulty: DifficultyLevel
) -> tuple[str, list[str], str]:
    """
    Calls Azure OpenAI and returns (question_text, options, answer_key) for a keyword + difficulty.
    Returns ("", [], "") if the API key is not configured.
    """
    if not settings.OPENAI_API_KEY:
        # Placeholder when API keys are not yet available
        return (
            f"[PLACEHOLDER] What is a {difficulty.value}-level concept in {keyword}?",
            ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"],
            "A",
        )

    llm = _get_llm()
    prompt = DIFFICULTY_PROMPTS[difficulty].format(keyword=keyword)
    messages = [
        SystemMessage(content="You are an expert technical interviewer. Be concise and precise."),
        HumanMessage(content=prompt),
    ]
    response = await llm.ainvoke(messages)
    return _parse_qa(str(response.content))


async def evaluate_answer(question: str, correct_answer: str, user_answer: str) -> tuple[bool, str]:
    """
    Evaluates the user's answer against the correct answer.
    Since this is a multiple-choice question, the evaluation is a simple string comparison.
    Returns (is_correct: bool, feedback: str).
    """
    is_correct = user_answer.strip().upper() == correct_answer.strip().upper()
    
    if is_correct:
        feedback = "Correct! Great job."
    else:
        feedback = f"Incorrect. The correct answer was {correct_answer}."
        
    return is_correct, feedback


async def generate_gap_analysis(session_history: list[dict]) -> str:
    """
    Generates the final Gap Analysis report for a completed mock interview.
    `session_history` is a list of dicts with keys: question, user_answer, is_correct.
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
        f"Was Correct: {'Yes' if item['is_correct'] else 'No'}"
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
