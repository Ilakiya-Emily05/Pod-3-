from openai import AzureOpenAI
import logging
from langchain_openai import AzureChatOpenAI
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


get_chat_llm = AzureChatOpenAI(
    azure_endpoint=settings.azure_openai_endpoint,
    api_key=settings.azure_openai_api_key,
    api_version=settings.azure_openai_api_version,
    azure_deployment=settings.azure_openai_deployment,
    temperature=0,
    default_headers={"x-ms-client-request-id": "phenomes-analysis"},
)

# ✅ Raw Azure client (audio, etc.)
azure_openai_client = AzureOpenAI(
    api_key=settings.azure_openai_api_key,
    api_version=settings.azure_openai_api_version,
    azure_endpoint=settings.azure_openai_endpoint,
)