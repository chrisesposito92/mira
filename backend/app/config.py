import os as _os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # App
    app_name: str = "MIRA"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5173"]

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""

    # Database (direct connection for LangGraph checkpointer)
    database_url: str = ""

    # LLM API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""

    # Tavily (web search for use case generator)
    tavily_api_key: str = ""

    # LangSmith (optional — tracing enabled when LANGSMITH_TRACING=true)
    langsmith_tracing: str = ""
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_api_key: str = ""
    langsmith_project: str = "mira"

    # Encryption key for m3ter credentials
    encryption_key: str = ""

    # Embedding
    embedding_model: str = "text-embedding-3-small"
    embedding_batch_size: int = 100

    # RAG
    chunk_size: int = 4000
    chunk_overlap: int = 200
    retrieval_k: int = 5

    # Scraper
    m3ter_docs_url: str = "https://docs.m3ter.com"
    scraper_concurrency: int = 5
    scraper_delay: float = 0.5

    # File storage
    upload_dir: str = "uploads"

    # Logo.dev API token (for logo proxy and seed script)
    logo_dev_token: str = ""


settings = Settings()

# Export LangSmith env vars so the SDK picks them up
# (pydantic-settings env_file loading does NOT set os.environ)
if settings.langsmith_tracing:
    _os.environ.setdefault("LANGSMITH_TRACING", settings.langsmith_tracing)
if settings.langsmith_endpoint:
    _os.environ.setdefault("LANGSMITH_ENDPOINT", settings.langsmith_endpoint)
if settings.langsmith_api_key:
    _os.environ.setdefault("LANGSMITH_API_KEY", settings.langsmith_api_key)
if settings.langsmith_project:
    _os.environ.setdefault("LANGSMITH_PROJECT", settings.langsmith_project)
