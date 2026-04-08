"""
LLM Client for pronunciation service.
Uses LangChain ChatOpenAI — raw openai SDK only for audio transcription.
"""

import logging

from langchain_openai import ChatOpenAI
from openai import OpenAI

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Raw OpenAI client — audio transcription only (no LangChain audio support)
openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

# LangChain client — all text generation
chat_llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    openai_api_key=settings.OPENAI_API_KEY,
)


def get_chat_llm(temperature: float = 0.0) -> ChatOpenAI:
    """Return a ChatOpenAI instance with the given temperature."""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=temperature,
        openai_api_key=settings.OPENAI_API_KEY,
    )
