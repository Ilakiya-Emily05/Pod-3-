from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from pydantic import BaseModel, Field

from app.config.settings import get_settings
from app.schemas.sentence_framing import SentenceFramingQuestion


class SentenceFramingEvaluation(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    structure_score: int = Field(ge=0, le=100)
    structure_comment: str
    tone_score: int = Field(ge=0, le=100)
    tone_comment: str
    grammar_score: int = Field(ge=0, le=100)
    grammar_comment: str
    grammar_corrections: list[str] = Field(default_factory=list)
    content_score: int = Field(ge=0, le=100)
    content_comment: str
    content_suggestions: list[str] = Field(default_factory=list)
    improved_version: str
    cefr_level: str = Field(
        description=("Estimated CEFR Level (A1, A2, B1, B2, C1, C2) based on the response quality.")
    )


def get_llm() -> ChatOpenAI | AzureChatOpenAI | None:
    """Lazily initialize the LLM. Supports both Azure and Standard OpenAI."""
    settings = get_settings()
    api_key = settings.openai_api_key
    if api_key:
        return ChatOpenAI(
            model="gpt-4o",
            api_key=api_key,
            temperature=0.7,
        )

    if settings.azure_openai_api_key and settings.azure_openai_endpoint:
        return AzureChatOpenAI(
            azure_deployment=settings.azure_openai_deployment,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            temperature=0.7,
        )

    return None


async def generate_sentence_exercise(
    cefr_level: str,
    topic: str | None = None,
    difficulty: str = "intermediate",
    industry: str | None = None,
    exercise_type: str = "free_form",
) -> SentenceFramingQuestion | None:
    llm = get_llm()
    if not llm:
        return None

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert in professional communication and English language coaching. "
                "Generate a unique, realistic business writing exercise tailored to a specific "
                "CEFR level.",
            ),
            (
                "user",
                (
                    "Create a sentence framing exercise with the following parameters:\n"
                    f"CEFR Level: {cefr_level}\n"
                    f"Topic/Context: {topic or 'Any professional business situation'}\n"
                    f"Difficulty: {difficulty}\n"
                    f"Industry: {industry or 'General Professional'}\n"
                    f"Exercise Type: {exercise_type}\n\n"
                    "Instructions:\n"
                    "1. For 'fill_in_blank' type, the 'template' MUST include underscores "
                    "(at least 15 underscores like '_______________') where the user needs to "
                    "fill in the critical parts of the sentence.\n"
                    "2. For 'reorder' type, the 'template' should be a list of sentences "
                    "to be reordered.\n"
                    "3. Hints must be exactly 3 concise, actionable tips.\n"
                    "4. Scenario must be realistic and professional. "
                    "Avoid placeholders like [Name].\n"
                    "5. PROFESSIONAL STRUCTURE: If the scenario involves an email, the 'template' "
                    "MUST include a 'Subject:' line, a professional salutation "
                    "(e.g., 'Dear Team,'), \n"
                    "Even for short messages, ensure the tone and format are "
                    "appropriate for a professional setting.\n"
                    "6. NO BRACKETS: Do NOT use brackets like [Your Name] or [Company]. "
                    "Use realistic, specific details instead.\n"
                    "Return structured output according to SentenceFramingQuestion."
                ),
            ),
        ]
    )

    chain = prompt | llm.with_structured_output(SentenceFramingQuestion)
    result = await chain.ainvoke({})
    if result is not None and not isinstance(result, SentenceFramingQuestion):
        raise ValueError("AI failed to generate a valid sentence framing question.")
    return result


async def evaluate_sentence_response(
    scenario: str,
    context: dict[str, str],
    user_response: str,
    exercise_type: str = "free_form",
    difficulty: str = "intermediate",
    cefr_level: str = "B1",
) -> SentenceFramingEvaluation | None:
    llm = get_llm()
    if not llm:
        return None

    difficulty_instructions = (
        f"The user is aiming for {cefr_level} proficiency ({difficulty} difficulty). "
        "Adjust your grading strictness accordingly. An executive level response should be "
        "high-level while a basic level response should focus on clarity and fundamental structure."
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an elite business communication coach. Evaluate the following user "
                "response with high precision and fairness.\n"
                f"{difficulty_instructions}\n\n"
                "SCORING RUBRIC:\n"
                "- Structure (0-100): Professional layout (Greeting, Intro, Body, Action, "
                "Closing).\n"
                "- Tone (0-100): Balanced professional/courteous.\n"
                "- Grammar (0-100): Technical correctness (spelling/syntax).\n"
                "- Content (0-100): Specificity and actionability.\n\n"
                "CRITICAL CONSTRAINTS:\n"
                "1. IMPROVED VERSION MUST NOT use ANY placeholders (like [Your Name]). "
                "Invent realistic details.\n"
                "2. BE SPECIFIC: Comments must specify EXACTLY what is missing or what word "
                "was misused.\n"
                "3. CEFR MAPPING: Provide a CEFR level (A1-C2) that best matches the response "
                "quality.",
            ),
            (
                "user",
                (
                    "Evaluate this professional communication:\n\n"
                    f"Scenario: {scenario}\n"
                    f"Exercise Type: {exercise_type}\n"
                    f"Expected Tone: {context.get('tone', 'professional')}\n"
                    f"Sender Role: {context.get('sender_role', 'Professional')}\n"
                    f"Recipient: {context.get('recipient', 'Colleague')}\n\n"
                    f"User's Response: {user_response}\n\n"
                    "Provide detailed feedback and scores in structured format."
                ),
            ),
        ]
    )

    chain = prompt | llm.with_structured_output(SentenceFramingEvaluation)
    result = await chain.ainvoke({})
    if result is not None and not isinstance(result, SentenceFramingEvaluation):
        raise ValueError("AI failed to generate a valid sentence framing evaluation.")
    return result
