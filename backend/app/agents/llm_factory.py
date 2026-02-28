"""Model registry and LLM initialization using langchain init_chat_model."""

import os

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from app.config import settings

# Model registry: model_id → (provider, model_name)
MODEL_REGISTRY: dict[str, tuple[str, str]] = {
    "gpt-5.2": ("openai", "gpt-5.2"),
    "gemini-3-flash-preview": ("google_genai", "gemini-3-flash-preview"),
    "gemini-3.1-pro-preview": ("google_genai", "gemini-3.1-pro-preview"),
    "claude-opus-4-6": ("anthropic", "claude-opus-4-6"),
    "claude-sonnet-4-6": ("anthropic", "claude-sonnet-4-6"),
}

# Provider → (env var name, settings attribute)
_PROVIDER_KEY_MAP: dict[str, tuple[str, str]] = {
    "openai": ("OPENAI_API_KEY", "openai_api_key"),
    "anthropic": ("ANTHROPIC_API_KEY", "anthropic_api_key"),
    "google_genai": ("GOOGLE_API_KEY", "google_api_key"),
}


def _ensure_api_key(provider: str) -> None:
    """Set the provider's API key env var from settings if not already set."""
    env_var, settings_attr = _PROVIDER_KEY_MAP[provider]
    if not os.environ.get(env_var):
        key = getattr(settings, settings_attr, "")
        if key:
            os.environ[env_var] = key


def get_llm(
    model_id: str,
    temperature: float = 0.2,
    streaming: bool = True,
) -> BaseChatModel:
    """Initialize a chat model by model_id using langchain's init_chat_model.

    Args:
        model_id: Key from MODEL_REGISTRY (e.g. "claude-sonnet-4-6").
        temperature: Sampling temperature (default 0.2 for deterministic output).
        streaming: Whether to enable streaming (default True).

    Returns:
        A BaseChatModel instance routed to the correct provider.

    Raises:
        ValueError: If model_id is not in the registry.
    """
    if model_id not in MODEL_REGISTRY:
        available = ", ".join(sorted(MODEL_REGISTRY.keys()))
        raise ValueError(f"Unknown model_id '{model_id}'. Available models: {available}")

    provider, model_name = MODEL_REGISTRY[model_id]
    _ensure_api_key(provider)

    return init_chat_model(
        model=model_name,
        model_provider=provider,
        temperature=temperature,
        streaming=streaming,
    )


def list_models() -> list[dict]:
    """Return available models with id, provider, and display name.

    Returns:
        List of dicts with keys: id, provider, display_name.
    """
    models = []
    for model_id, (provider, model_name) in MODEL_REGISTRY.items():
        display_name = model_name.replace("-", " ").title()
        models.append(
            {
                "id": model_id,
                "provider": provider,
                "display_name": display_name,
            }
        )
    return models
