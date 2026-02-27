"""Schemas for RAG embeddings and retrieval."""

from pydantic import BaseModel, Field


class RetrievalRequest(BaseModel):
    query: str
    project_id: str | None = None
    k: int = Field(default=5, ge=1, le=50)


class RetrievalResult(BaseModel):
    content: str
    metadata: dict
    score: float
    source_type: str
