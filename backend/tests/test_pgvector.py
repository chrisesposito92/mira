"""Tests for pgvector functionality — insert, query, dimension validation."""

import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


async def test_insert_and_query_vector(db_conn):
    """Insert a 1536-dim vector and retrieve it with cosine similarity ~1.0."""
    await db_conn.execute("SET LOCAL role TO postgres")

    # Create a 1536-dim vector (all 0.01 values)
    dim = 1536
    vec_str = "[" + ",".join(["0.01"] * dim) + "]"

    row_id = await db_conn.fetchval(
        """
        INSERT INTO embeddings (source_type, content, embedding)
        VALUES ('m3ter_docs', 'test content', $1::vector)
        RETURNING id
        """,
        vec_str,
    )

    # Query cosine similarity against itself
    similarity = await db_conn.fetchval(
        """
        SELECT 1 - (embedding <=> $1::vector) AS similarity
        FROM embeddings WHERE id = $2
        """,
        vec_str,
        row_id,
    )

    assert similarity is not None
    assert similarity > 0.99, f"Self-similarity should be ~1.0, got {similarity}"


async def test_wrong_dimension_raises_error(db_conn):
    """Inserting a vector with wrong dimensions should raise an error."""
    await db_conn.execute("SET LOCAL role TO postgres")

    vec_100 = "[" + ",".join(["0.01"] * 100) + "]"

    with pytest.raises(Exception) as exc_info:
        await db_conn.execute(
            """
            INSERT INTO embeddings (source_type, content, embedding)
            VALUES ('m3ter_docs', 'wrong dim', $1::vector)
            """,
            vec_100,
        )

    assert "1536" in str(exc_info.value) or "dimension" in str(exc_info.value).lower()
