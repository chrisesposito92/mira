"""Schemas for use case generator endpoints."""

from pydantic import BaseModel


class ExtractTextResponse(BaseModel):
    text: str
