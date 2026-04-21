from typing import TypedDict
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from app.config.settings import get_settings


class AnswerScoreResult(TypedDict):
    score: float
    feedback: str
    breakdown: dict


def get_llm():
    settings = get_settings()

    return AzureChatOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        deployment_name=settings.azure_openai_deployment,
        temperature=0.2,
    )


async def evaluate_answer_with_gpt(question_text: str, rubric: str, user_answer: str) -> AnswerScoreResult:
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert technical interviewer."),
        ("human", """
Evaluate the candidate's answer.

Question:
{question}

Rubric:
{rubric}

Answer:
{answer}

Return structured JSON:
- score (0–10 float)
- feedback (short)
- breakdown (clarity, accuracy, depth)
""")
    ])

    chain = (
        {
            "question": RunnablePassthrough(),
            "rubric": RunnablePassthrough(),
            "answer": RunnablePassthrough(),
        }
        | prompt
        | llm.with_structured_output(AnswerScoreResult)
    )

    result = await chain.ainvoke({
        "question": question_text,
        "rubric": rubric,
        "answer": user_answer,
    })

    return result