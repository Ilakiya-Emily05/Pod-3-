from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.config.settings import get_settings


class AIGeneratedExercise(BaseModel):
    category: str = Field(description="Main category of the exercise")
    subcategory: str = Field(description="Subcategory of the exercise")
    exercise_type: str = Field(description="Type: free_form, fill_in_blank, or reorder")
    scenario: str = Field(description="The professional scenario description")
    sender_role: str = Field(description="Role of the person sending the message")
    recipient: str = Field(description="Person receiving the message")
    tone: str = Field(description="Desired professional tone")
    template: str | None = Field(None, description="Template with blanks if fill_in_blank")
    hints: list[str] = Field(default_factory=list, description="3 helpful hints for the user")
    example_answer: str = Field(description="A model professional response")


class AIEvaluationResult(BaseModel):
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


def get_llm_mini():
    """Initialize GPT-4o-mini for cost-effective evaluation."""
    settings = get_settings()
    if settings.openai_api_key:
        return ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.openai_api_key,
            temperature=0.7,
        )
    return None


async def generate_sentence_exercise(
    category: str,
    subcategory: str | None = None,
    difficulty: str = "intermediate",
    industry: str | None = None,
    exercise_type: str = "free_form",
) -> AIGeneratedExercise | None:
    llm = get_llm_mini()
    if not llm:
        return None

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert in professional communication. Generate a unique, realistic business writing exercise.",
            ),
            (
                "user",
                (
                    "Create a sentence framing exercise with the following parameters:\n"
                    f"Category: {category}\n"
                    f"Subcategory: {subcategory or 'Any relevant'}\n"
                    f"Difficulty: {difficulty}\n"
                    f"Industry: {industry or 'General Professional'}\n"
                    f"Exercise Type: {exercise_type}\n\n"
                    "For 'fill_in_blank' type, the 'template' MUST include underscores (at least 15 underscores like '_______________') where the user needs to fill in the critical parts of the sentence. "
                    "The template should provide structure but leave the specific professional framing to the user. "
                    "Hints must be exactly 3 concise, actionable tips for writing this specific scenario. "
                    "Ensure the scenario is specific and practical. Return structured output."
                ),
            ),
        ]
    )

    chain = prompt | llm.with_structured_output(AIGeneratedExercise)
    result = await chain.ainvoke({})
    return result


async def evaluate_sentence_response(
    scenario: str,
    context: dict[str, Any],
    user_response: str,
    exercise_type: str = "free_form",
    difficulty: str = "intermediate",
) -> AIEvaluationResult | None:
    llm = get_llm_mini()
    if not llm:
        return None

    # Adjust constraints based on difficulty
    difficulty_instructions = ""
    if difficulty.lower() == "executive":
        difficulty_instructions = (
            "EXECUTIVE LEVEL: Be extremely strict. Demand high-level vocabulary, perfect strategic framing, "
            "and sophisticated tone. A simple 'good' email is not enough for a 90+ score; it must be exceptional."
        )
    elif difficulty.lower() == "basic":
        difficulty_instructions = (
            "BASIC LEVEL: Be encouraging. Focus on clarity and basic professional structure. "
            "Do not penalize for lack of advanced vocabulary."
        )

    type_instructions = ""
    if exercise_type == "fill_in_blank":
        type_instructions = "TYPE: Fill-in-the-blank. Evaluate how well the user completed the missing parts and integrated them into the overall flow."
    elif exercise_type == "reorder":
        type_instructions = "TYPE: Sentence Reordering. Evaluate if the user has organized the sentences into the most logical and professionally effective sequence."

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an elite business communication coach. Evaluate the following user response with high precision and fairness. "
                f"\n\n{difficulty_instructions}\n"
                f"\n\n{type_instructions}\n"
                "\n\nSCORING RUBRIC:\n"
                "- Structure (80-100): Professional layout (Greeting, Intro, Body, Action, Closing) should get at least 80. Only dock points if it's messy or confusing.\n"
                "- Tone (80-100): Balanced professional/courteous. Avoid 'heavy' or 'panic-mode' words (e.g., use 'challenges' instead of 'serious issues').\n"
                "- Grammar (80-100): DO NOT confuse style/phrasing with grammar. If it's technically correct (spelling/syntax), the score should be 90-100. Mention phrasing issues as 'Style/Clarity' points, not grammar errors.\n"
                "- Content (0-100): If specific and actionable, 90-100. If vague or missing key info, 70-80.\n"
                "\n\nCRITICAL CONSTRAINTS:\n"
                "1. NO NITPICKING: If a response is professional and clear, it MUST be in the 95-100 range. Avoid deducting points just to have 'room for improvement'.\n"
                "2. NO PLACEHOLDERS: IMPROVED VERSION MUST NOT use ANY placeholders, brackets, or generic labels like '[Your Name]', '[Company Name]', '[Date]', or '[... details]'. You MUST invent realistic names, specific company names, actual dates, and specific details based on the scenario to make it a 100% ready-to-send email.\n"
                "3. BE SPECIFIC: Comments must specify EXACTLY what is missing or what word was misused.\n"
            ),
            (
                "user",
                (
                    "Evaluate this professional communication:\n\n"
                    f"Scenario: {scenario}\n"
                    f"Expected Tone: {context.get('tone', 'professional')}\n"
                    f"Sender Role: {context.get('sender_role', 'Professional')}\n"
                    f"Recipient: {context.get('recipient', 'Colleague')}\n\n"
                    f"User's Response: {user_response}\n\n"
                    "Provide scores (0-100) and detailed feedback for: Structure, Tone, Grammar, and Content. "
                    "In the 'improved_version', provide a polished, natural, and HIGHLY SPECIFIC response with NO placeholders."
                ),
            ),
        ]
    )

    chain = prompt | llm.with_structured_output(AIEvaluationResult)
    result = await chain.ainvoke({})
    return result
