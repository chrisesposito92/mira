"""LangGraph checkpoint and store persistence using psycopg pool.

Provides:
- AsyncPostgresSaver for short-term workflow state (checkpointer)
- AsyncPostgresStore for long-term cross-workflow memory (store)

Both share a single connection pool to minimize resource usage.
"""

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres.aio import AsyncPostgresStore
from psycopg_pool import AsyncConnectionPool

from app.config import settings

_checkpointer: AsyncPostgresSaver | None = None
_store: AsyncPostgresStore | None = None
_psycopg_pool: AsyncConnectionPool | None = None


async def _get_pool() -> AsyncConnectionPool:
    """Return a cached psycopg connection pool, creating it on first call."""
    global _psycopg_pool
    if _psycopg_pool is not None:
        return _psycopg_pool

    conninfo = settings.database_url

    # Supabase requires SSL
    if "supabase.co" in conninfo and "sslmode" not in conninfo:
        separator = "&" if "?" in conninfo else "?"
        conninfo = f"{conninfo}{separator}sslmode=require"

    _psycopg_pool = AsyncConnectionPool(
        conninfo=conninfo,
        min_size=2,
        max_size=15,
        open=False,
        kwargs={"autocommit": True, "prepare_threshold": 0},
    )
    await _psycopg_pool.open(wait=True)
    return _psycopg_pool


async def get_checkpointer() -> AsyncPostgresSaver:
    """Return a cached AsyncPostgresSaver backed by a psycopg connection pool."""
    global _checkpointer
    if _checkpointer is not None:
        return _checkpointer

    pool = await _get_pool()
    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()
    _checkpointer = checkpointer
    return _checkpointer


async def get_store() -> AsyncPostgresStore:
    """Return a cached AsyncPostgresStore backed by the shared connection pool."""
    global _store
    if _store is not None:
        return _store

    pool = await _get_pool()
    store = AsyncPostgresStore(pool)
    await store.setup()
    _store = store
    return _store


async def close_checkpointer_pool() -> None:
    """Close the psycopg connection pool and clear cached singletons."""
    global _checkpointer, _store, _psycopg_pool
    if _psycopg_pool is not None:
        await _psycopg_pool.close()
        _psycopg_pool = None
    _checkpointer = None
    _store = None
