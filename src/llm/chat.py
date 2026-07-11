import os

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from src.config import CHAT_MODEL, GOOGLE_MODEL, LLM_PROVIDER, OPENAI_MODEL

VALID_PROVIDERS = ("ollama", "openai", "google")


def _google_api_key() -> str | None:
    return os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")


def normalize_provider(provider: str | None = None) -> str:
    value = (provider or LLM_PROVIDER or "ollama").strip().lower()
    if value in {"gemini", "google-genai"}:
        value = "google"
    if value not in VALID_PROVIDERS:
        raise ValueError(f"Unknown LLM provider '{value}'. Use: {', '.join(VALID_PROVIDERS)}")
    return value


def get_chat_model(provider: str | None = None, *, temperature: float = 0) -> BaseChatModel:
    name = normalize_provider(provider)
    if name == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError(
                "OPENAI_API_KEY is not set. Add it to .env or export it in your shell."
            )
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=OPENAI_MODEL, temperature=temperature)

    if name == "google":
        api_key = _google_api_key()
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY (or GEMINI_API_KEY) is not set. Add it to .env."
            )
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=GOOGLE_MODEL,
            temperature=temperature,
            google_api_key=api_key,
        )

    from langchain_ollama import ChatOllama

    return ChatOllama(model=CHAT_MODEL, temperature=temperature)


def chat_complete(system: str, user: str, provider: str | None = None) -> str:
    llm = get_chat_model(provider)
    response = llm.invoke(
        [SystemMessage(content=system), HumanMessage(content=user)],
    )
    content = response.content
    if isinstance(content, str):
        return content
    return str(content)
