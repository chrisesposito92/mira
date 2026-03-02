"""LangGraph checkpoint persistence using AsyncPostgresSaver with psycopg pool."""

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

from app.config import settings

_checkpointer: AsyncPostgresSaver | None = None
_psycopg_pool: AsyncConnectionPool | None = None


async def get_checkpointer() -> AsyncPostgresSaver:
    """Return a cached AsyncPostgresSaver backed by a psycopg connection pool."""
    global _checkpointer, _psycopg_pool
    if _checkpointer is not None:
        return _checkpointer

    conninfo = settings.database_url

    # Supabase requires SSL
    if "supabase.co" in conninfo and "sslmode" not in conninfo:
        separator = "&" if "?" in conninfo else "?"
        conninfo = f"{conninfo}{separator}sslmode=require"

    _psycopg_pool = AsyncConnectionPool(
        conninfo=conninfo,
        min_size=2,
        max_size=10,
        open=False,
        kwargs={"autocommit": True, "prepare_threshold": 0},
    )
    await _psycopg_pool.open(wait=True)

    checkpointer = AsyncPostgresSaver(_psycopg_pool)
    await checkpointer.setup()
    _checkpointer = checkpointer
    return _checkpointer


async def close_checkpointer_pool() -> None:
    """Close the psycopg connection pool used by the checkpointer."""
    global _checkpointer, _psycopg_pool
    if _psycopg_pool is not None:
        await _psycopg_pool.close()
        _psycopg_pool = None
    _checkpointer = None
