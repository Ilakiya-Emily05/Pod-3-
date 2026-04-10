import logging
import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.agents.prompts import SYSTEM_PROMPT
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class GrammarQuestion(BaseModel):
    question: str
    options: dict[str, str]
    correct_answer: str
    explanation: str


class GrammarQuestionsOutput(BaseModel):
    questions: list[GrammarQuestion]


class AIGeneratorService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.model = os.getenv("OPENAI_MODEL", self.settings.OPENAI_MODEL)

    def _llm(self) -> ChatOpenAI:
        return ChatOpenAI(
            model=self.model,
            api_key=self.settings.OPENAI_API_KEY,
            temperature=0.7,
        )

    def generate_questions(
        self, topic: str, difficulty: str, count: int, subtopic: str | None = None
    ) -> list[dict]:
        try:
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", SYSTEM_PROMPT),
                    (
                        "human",
                        "Generate {count} UNIQUE grammar MCQs. Topic: {topic}. Subtopic: {subtopic}. Difficulty: {difficulty}. Return JSON only.",
                    ),
                ]
            )
            chain = prompt | self._llm().with_structured_output(
                GrammarQuestionsOutput, method="function_calling"
            )
            result = chain.invoke(
                {
                    "topic": topic,
                    "subtopic": subtopic or "general",
                    "difficulty": difficulty,
                    "count": count,
                }
            )
            logger.info(f"Generated {len(result.questions)} questions for {topic}/{subtopic}")
            return [question.model_dump() for question in result.questions]
        except Exception as e:
            logger.error(
                f"AI generation failed for topic={topic}, subtopic={subtopic}, error={type(e).__name__}: {e!s}"
            )
            raise
