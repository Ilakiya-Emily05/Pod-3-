import logging
from typing import List, Optional

from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallLimitMiddleware
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.agents.prompts import PASSAGE_AGENT_PROMPT, PASSAGE_SYSTEM_PROMPT
from app.agents.tools.passage_tool import generate_passage_with_questions
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


passage_limiter = ToolCallLimitMiddleware(
    tool_name="generate_passage_with_questions",
    run_limit=1,
    exit_behavior="error",
)


class QuestionOutput(BaseModel):
    passage: Optional[str] = None
    question: str
    options: dict[str, str]
    correct_answer: str
    difficulty: str


class AgentOutput(BaseModel):
    questions: List[QuestionOutput]


def build_agent():
    llm = ChatOpenAI(
        model=get_settings().OPENAI_MODEL,
        api_key=get_settings().OPENAI_API_KEY,
    )
    return create_agent(
        model=llm,
        tools=[generate_passage_with_questions],
        middleware=[passage_limiter],
        system_prompt=PASSAGE_SYSTEM_PROMPT,
        response_format=AgentOutput,
    )


def run_agent():
    try:
        agent = build_agent()
        result = agent.invoke({"messages": [{"role": "user", "content": PASSAGE_AGENT_PROMPT}]})
        structured: AgentOutput = result["structured_response"]
        logger.info(f"Generated passage with {len(structured.questions)} questions")
        return {"questions": [question.model_dump() for question in structured.questions]}
    except Exception as e:
        logger.error(f"Passage generation failed: {type(e).__name__}: {str(e)}")
        raise
