"""LangGraph checkpoint persistence using AsyncPostgresSaver."""

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.db.client import get_db_pool

_checkpointer: AsyncPostgresSaver | None = None


async def get_checkpointer() -> AsyncPostgresSaver:
    """Return a cached AsyncPostgresSaver backed by the shared asyncpg pool."""
    global _checkpointer
    if _checkpointer is not None:
        return _checkpointer
    pool = await get_db_pool()
    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()
    _checkpointer = checkpointer
    return _checkpointer
