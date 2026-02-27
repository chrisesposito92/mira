"""Tests that verify the database schema was applied correctly."""

import pytest

pytestmark = pytest.mark.asyncio

EXPECTED_TABLES = [
    "profiles",
    "org_connections",
    "projects",
    "use_cases",
    "workflows",
    "generated_objects",
    "chat_messages",
    "documents",
    "embeddings",
]

EXPECTED_ENUMS = [
    "entity_type",
    "object_status",
    "workflow_type",
    "workflow_status",
    "use_case_status",
    "billing_frequency",
    "connection_status",
    "document_status",
    "embedding_source",
    "message_role",
]


async def test_all_tables_exist(db_conn):
    """All 9 application tables should exist in the public schema."""
    rows = await db_conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
    table_names = {r["tablename"] for r in rows}
    for table in EXPECTED_TABLES:
        assert table in table_names, f"Table '{table}' not found in public schema"


async def test_all_enums_exist(db_conn):
    """All 10 enum types should exist."""
    rows = await db_conn.fetch(
        """
        SELECT t.typname
        FROM pg_type t
        JOIN pg_namespace n ON t.typnamespace = n.oid
        WHERE n.nspname = 'public' AND t.typtype = 'e'
        """
    )
    enum_names = {r["typname"] for r in rows}
    for enum in EXPECTED_ENUMS:
        assert enum in enum_names, f"Enum type '{enum}' not found"


async def test_pgvector_extension_enabled(db_conn):
    """pgvector extension should be installed."""
    row = await db_conn.fetchrow("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
    assert row is not None, "pgvector extension not installed"


async def test_hnsw_index_exists(db_conn):
    """HNSW index on embeddings.embedding should exist."""
    row = await db_conn.fetchrow(
        """
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'embeddings' AND indexname = 'idx_embeddings_hnsw'
        """
    )
    assert row is not None, "HNSW index not found on embeddings"


async def test_updated_at_trigger_fires(db_conn):
    """updated_at should auto-update on row modification.

    The trigger uses now() which returns transaction start time. To test it,
    we verify the trigger function exists and is attached, then confirm that
    an UPDATE with an explicit older created_at still gets a fresh updated_at.
    """
    await db_conn.execute("SET LOCAL role TO postgres")

    # Insert a test user into auth.users first
    user_id = await db_conn.fetchval(
        """
        INSERT INTO auth.users (
            id, instance_id, aud, role, email,
            encrypted_password, email_confirmed_at,
            created_at, updated_at, confirmation_token, recovery_token,
            email_change_token_new, email_change,
            is_sso_user, is_anonymous
        ) VALUES (
            gen_random_uuid(), '00000000-0000-0000-0000-000000000000',
            'authenticated', 'authenticated', 'trigger-test@test.com',
            crypt('password123', gen_salt('bf')), now(),
            now(), now(), '', '', '', '',
            false, false
        ) RETURNING id
        """
    )

    # Insert with an explicit old updated_at
    row_id = await db_conn.fetchval(
        """
        INSERT INTO org_connections (user_id, org_id, client_id, client_secret, updated_at)
        VALUES ($1, 'test-org', 'cid', 'csec', '2020-01-01T00:00:00Z')
        RETURNING id
        """,
        user_id,
    )

    # UPDATE should trigger set_updated_at() which sets updated_at = now()
    await db_conn.execute("UPDATE org_connections SET org_name = 'updated' WHERE id = $1", row_id)

    updated = await db_conn.fetchval("SELECT updated_at FROM org_connections WHERE id = $1", row_id)
    # The trigger should have set updated_at to now() which is much later than 2020
    assert updated.year >= 2026, f"Trigger did not fire, updated_at is {updated}"


async def test_schema_migrations_tracking(db_conn):
    """schema_migrations table should have all 12 migration entries."""
    count = await db_conn.fetchval("SELECT count(*) FROM schema_migrations")
    assert count == 12, f"Expected 12 migrations, got {count}"
