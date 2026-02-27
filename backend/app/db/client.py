"""Supabase client and asyncpg connection pool management."""

import asyncpg
from supabase import Client, create_client

from app.config import settings

# Module-level singletons
_supabase_client: Client | None = None
_supabase_anon_client: Client | None = None
_db_pool: asyncpg.Pool | None = None


def get_supabase_client() -> Client:
    """Cached Supabase client using service role key (bypasses RLS)."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key,
        )
    return _supabase_client


def get_supabase_anon_client() -> Client:
    """Cached Supabase client using anon key (respects RLS)."""
    global _supabase_anon_client
    if _supabase_anon_client is None:
        _supabase_anon_client = create_client(
            settings.supabase_url,
            settings.supabase_anon_key,
        )
    return _supabase_anon_client


async def get_db_pool() -> asyncpg.Pool:
    """Get or create asyncpg connection pool (for LangGraph checkpointer, raw SQL)."""
    global _db_pool
    if _db_pool is None:
        ssl = "require" if "supabase.co" in settings.database_url else None
        _db_pool = await asyncpg.create_pool(
            settings.database_url,
            min_size=2,
            max_size=10,
            ssl=ssl,
        )
    return _db_pool


async def close_db_pool() -> None:
    """Close the asyncpg connection pool on shutdown."""
    global _db_pool
    if _db_pool is not None:
        await _db_pool.close()
        _db_pool = None
