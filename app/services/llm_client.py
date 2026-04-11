import logging

from langchain_openai import AzureChatOpenAI
from openai import AzureOpenAI

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def get_chat_llm(temperature: float = 0) -> AzureChatOpenAI:
    if not settings.azure_openai_api_key or not settings.azure_openai_endpoint:
        msg = "Azure OpenAI credentials are not configured"
        raise RuntimeError(msg)
    return AzureChatOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        azure_deployment=settings.azure_openai_deployment,
        temperature=temperature,
        default_headers={"x-ms-client-request-id": "phenomes-analysis"},
    )


def get_azure_openai_client() -> AzureOpenAI:
    if not settings.azure_openai_api_key or not settings.azure_openai_endpoint:
        msg = "Azure OpenAI credentials are not configured"
        raise RuntimeError(msg)
    return AzureOpenAI(
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        azure_endpoint=settings.azure_openai_endpoint,
    )
