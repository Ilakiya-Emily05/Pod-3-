from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from pydantic import BaseModel, Field

from app.config.settings import get_settings


# Configuration from environment variables
def get_llm() -> ChatOpenAI | AzureChatOpenAI | None:
    """Lazily initialize the LLM. Supports both Azure and Standard OpenAI."""
    settings = get_settings()
    api_key = settings.openai_api_key
    if api_key:
        return ChatOpenAI(
            model="gpt-4o",
            api_key=api_key,
            temperature=0.9,
        )

    # Fallback to Azure if configured
    if settings.azure_openai_api_key and settings.azure_openai_endpoint:
        return AzureChatOpenAI(
            azure_deployment=settings.azure_openai_deployment,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            temperature=0.9,
        )
    return None


class AIAnalysisReport(BaseModel):
    summary: str = Field(description="A brief overview of the learner's core personality profile.")
    strength: str = Field(
        description="Highlight the most prominent positive traits (scores >= 40)."
    )
    concern: str = Field(
        description="Address the traits that may require development or monitoring (scores < 30)."
    )
    focus_areas: str = Field(
        description=(
            "Specific behavioral areas where the learner can improve or take an adaptive test."
        )
    )


class AIOption(BaseModel):
    option_text: str = Field(description="The text for this option.")
    score: int = Field(description="The score for the primary trait (1, 2, 4, or 5).")


class AIQuestion(BaseModel):
    trait: str = Field(description="The HEXACO trait this question belongs to.")
    question_text: str = Field(description="The question or situational prompt.")
    question_type: str = Field(
        description="Either 'likert' (Agree/Disagree) or 'situational' (Choice of actions)."
    )
    options: list[AIOption] = Field(description="List of exactly 4 options with scores.")


class HEXACOQuestionList(BaseModel):
    questions: list[AIQuestion] = Field(description="A list of assessment questions.")


async def generate_personality_report(hexaco_scores: dict[str, float]) -> dict[str, str]:
    llm = get_llm()
    if not llm:
        raise ValueError("AI Service Unconfigured: Please provide an OpenAI or Azure API Key.")

    scores_str = "\n".join(
        [f"{k.replace('_', '-').title()}: {v}" for k, v in hexaco_scores.items()]
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "You are an Educational and Behavioral Development Expert specialized in the "
                    "HEXACO model."
                ),
            ),
            (
                "user",
                "Analyze the following HEXACO trait scores (Max 5.0 each) to provide a personal "
                "growth report for a learner.\n"
                "Scores:\n{scores}\n"
                "Maximum 1 sentence per field. Maximum 4 lines total.",
            ),
        ]
    )

    chain = prompt | llm.with_structured_output(AIAnalysisReport)
    report = await chain.ainvoke({"scores": scores_str})
    if not isinstance(report, AIAnalysisReport):
        raise ValueError("AI failed to generate a valid personality report.")
    return report.model_dump()


async def generate_assessment_questions() -> list[AIQuestion]:
    traits = [
        "Honesty-Humility",
        "Emotionality",
        "Extraversion",
        "Agreeableness",
        "Conscientiousness",
        "Openness",
    ]

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "You are an expert psychometrician specialized in behavioral "
                    "assessments and the HEXACO model. You prioritize diversity and "
                    "uniqueness in question generation."
                ),
            ),
            (
                "user",
                (
                    "Generate a behavioral assessment questionnaire based on the HEXACO model.\n"
                    "Generate exactly 10 questions in total.\n"
                    "Traits: {traits}\n"
                    "Instructions:\n"
                    "1. For each question, FIRST internally select a completely different, highly "
                    "specific profession, subculture, or unique obscure situation from anywhere "
                    "in the world.\n"
                    "2. Base the scenario strictly on realistic daily challenges of that context.\n"
                    "3. Ensure novelty: it must not sound like a generic "
                    "psychological assessment.\n"
                    "- Each question: 4 options with scores (1, 2, 4, 5). "
                    "Likert or situational.\n"
                    "- Do not mention trait names in question text."
                ),
            ),
        ]
    )

    llm = get_llm()
    if not llm:
        raise ValueError(
            "AI Service Unconfigured: Please provide an API Key to generate questions."
        )

    chain = prompt | llm.with_structured_output(HEXACOQuestionList)
    result = await chain.ainvoke({"traits": ", ".join(traits)})
    if not isinstance(result, HEXACOQuestionList):
        raise ValueError("AI failed to generate valid assessment questions.")
    return result.questions


async def generate_adaptive_questions(traits: list[str]) -> list[AIQuestion]:
    if not traits:
        return []

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "You are an expert psychometrician. Focus on unique, deep-dive "
                    "scenarios for specific personality traits."
                ),
            ),
            (
                "user",
                (
                    "The candidate has shown lower scores in: {traits}.\n"
                    "Generate exactly {count} additional questions (3 per trait).\n"
                    "Instructions:\n"
                    "1. For each question, FIRST internally select a completely different, highly "
                    "specific profession, subculture, or unique obscure situation from anywhere "
                    "in the world.\n"
                    "2. Base the scenario strictly on realistic daily challenges of that context.\n"
                    "3. Ensure novelty: it must not sound like a generic "
                    "psychological assessment.\n"
                    "- Each question: 4 options with scores (1, 2, 4, 5).\n"
                    "- Do not mention trait names in question text."
                ),
            ),
        ]
    )

    llm = get_llm()
    if not llm:
        raise ValueError(
            "AI Service Unconfigured: Please provide an API Key to generate adaptive questions."
        )

    chain = prompt | llm.with_structured_output(HEXACOQuestionList)
    result = await chain.ainvoke({"traits": ", ".join(traits), "count": len(traits) * 3})
    if not isinstance(result, HEXACOQuestionList):
        raise ValueError("AI failed to generate adaptive questions.")
    return result.questions
