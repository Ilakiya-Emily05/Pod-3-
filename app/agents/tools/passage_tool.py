from typing import List, Literal

from langchain_openai import ChatOpenAI
import json
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
    questions: List[ComprehensionQuestion]


def generate_passage_with_questions(topic_hint: str | None = None) -> dict:
    """Generate a comprehension passage and a list of structured questions.

    Returns a dict matching the ComprehensionPassage schema with the passage text
    and its questions. This function asks the LLM to return JSON and parses it
    locally to avoid strict OpenAI response_format validation errors.
    """
    llm = ChatOpenAI(
        model=get_settings().OPENAI_MODEL,
        api_key=get_settings().OPENAI_API_KEY,
        temperature=0.5,
        max_tokens=1200,
    )
    # Ask the model to return JSON only, then parse with Pydantic locally.
    topic_clause = f"\nTopic focus: {topic_hint}." if topic_hint else ""
    prompt = PASSAGE_TOOL_PROMPT_TEMPLATE + topic_clause + (
        "\n\nReturn JSON only with this shape: {\"passage\": string, \"questions\": [\n"
        "{\"question\": string, \"options\": {\"a\": string, \"b\": string, \"c\": string, \"d\": string}, "
        "\"correct_answer\": \"a|b|c|d\", \"difficulty\": \"easy|medium|hard\", \"explanation\": string\n} ] }"
    )

    raw = llm.invoke(prompt)
    # llm.invoke may return a string or an object with content
    if not isinstance(raw, str):
        raw = getattr(raw, "content", None) or str(raw)

    parsed = json.loads(raw)
    structured = ComprehensionPassage.model_validate(parsed)
    return structured.model_dump()
