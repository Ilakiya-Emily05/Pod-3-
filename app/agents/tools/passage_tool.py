import json
from typing import Literal

from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.agents.prompts import PASSAGE_TOOL_PROMPT_TEMPLATE
from app.config.settings import get_settings


class ComprehensionQuestion(BaseModel):
    question: str
    options: dict[str, str]
    correct_answer: Literal["a", "b", "c", "d"]
    difficulty: Literal["easy", "medium", "hard"]
    explanation: str


class ComprehensionPassage(BaseModel):
    passage: str
    questions: list[ComprehensionQuestion]


def generate_passage_with_questions(topic_hint: str | None = None) -> dict:
    """Generate a comprehension passage and a list of structured questions.

    Returns a dict matching the ComprehensionPassage schema with the passage text
    and its questions. This function asks the LLM to return JSON and parses it
    locally to avoid strict OpenAI response_format validation errors.
    """
    settings = get_settings()
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0.5,
        max_tokens=1200,
    )
    # Ask the model to return JSON only, then parse with Pydantic locally.
    topic_clause = f"\nTopic focus: {topic_hint}." if topic_hint else ""
    prompt = PASSAGE_TOOL_PROMPT_TEMPLATE + topic_clause

    raw = llm.invoke(prompt)
    # llm.invoke may return a string or an object with content
    if not isinstance(raw, str):
        raw = getattr(raw, "content", None) or str(raw)

    parsed = json.loads(raw)
    structured = ComprehensionPassage.model_validate(parsed)
    return structured.model_dump()
