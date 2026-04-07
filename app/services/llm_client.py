import logging

from langchain_openai import AzureChatOpenAI

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# ── Azure LLM (ALL text generation goes through this) ───────────────────────
_chat_llm = AzureChatOpenAI(
    azure_endpoint=settings.azure_openai_endpoint,
    api_key=settings.azure_openai_api_key,
    api_version=settings.azure_openai_api_version,
    azure_deployment=settings.azure_openai_deployment,
    temperature=0,
    default_headers={"x-ms-client-request-id": "phenomes-analysis"},
)


def get_chat_llm(temperature: float = 0.0) -> AzureChatOpenAI:
    """Return LLM instance (reuse singleton when temp=0)."""
    if temperature == 0.0:
        return _chat_llm

    return AzureChatOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        azure_deployment=settings.azure_openai_deployment,
        temperature=temperature,
        default_headers={"x-ms-client-request-id": "phenomes-analysis"},
    )
