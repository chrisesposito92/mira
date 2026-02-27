"""Tests for Row Level Security — user isolation at every nesting level."""

import json
import uuid

import pytest

pytestmark = pytest.mark.asyncio


async def _create_auth_user(conn, email: str) -> str:
    """Insert a user into auth.users and return their UUID."""
    user_id = await conn.fetchval(
        """
        INSERT INTO auth.users (
            id, instance_id, aud, role, email,
            encrypted_password, email_confirmed_at,
            created_at, updated_at, confirmation_token, recovery_token,
            email_change_token_new, email_change,
            is_sso_user, is_anonymous
        ) VALUES (
            gen_random_uuid(), '00000000-0000-0000-0000-000000000000',
            'authenticated', 'authenticated', $1,
            crypt('password123', gen_salt('bf')), now(),
            now(), now(), '', '', '', '',
            false, false
        ) RETURNING id
        """,
        email,
    )
    return str(user_id)


async def _set_rls_context(conn, user_id: str):
    """Set RLS context for the given user."""
    claims = json.dumps({"sub": user_id, "role": "authenticated"})
    await conn.execute("SET LOCAL role TO authenticated")
    await conn.execute(f"SET LOCAL request.jwt.claims TO '{claims}'")


async def _reset_to_postgres(conn):
    """Reset role back to postgres (superuser)."""
    await conn.execute("RESET role")


@pytest.fixture
async def two_users(db_conn):
    """Create two test users and return their IDs."""
    await db_conn.execute("SET LOCAL role TO postgres")
    user_a = await _create_auth_user(db_conn, f"user-a-{uuid.uuid4()}@test.com")
    user_b = await _create_auth_user(db_conn, f"user-b-{uuid.uuid4()}@test.com")
    return user_a, user_b


async def test_org_connections_isolation(db_conn, two_users):
    """User A's org_connections should be invisible to user B."""
    user_a, user_b = two_users

    # Insert as postgres (bypasses RLS)
    await _reset_to_postgres(db_conn)
    await db_conn.execute(
        """
        INSERT INTO org_connections (user_id, org_id, client_id, client_secret)
        VALUES ($1, 'org-a', 'cid-a', 'csec-a')
        """,
        uuid.UUID(user_a),
    )

    # User A should see their connection
    await _set_rls_context(db_conn, user_a)
    count_a = await db_conn.fetchval("SELECT count(*) FROM org_connections")
    assert count_a == 1

    # User B should see nothing
    await _reset_to_postgres(db_conn)
    await _set_rls_context(db_conn, user_b)
    count_b = await db_conn.fetchval("SELECT count(*) FROM org_connections")
    assert count_b == 0


async def test_projects_isolation(db_conn, two_users):
    """User A's projects visible to A, invisible to B."""
    user_a, user_b = two_users

    await _reset_to_postgres(db_conn)
    await db_conn.execute(
        "INSERT INTO projects (user_id, name) VALUES ($1, 'Project A')",
        uuid.UUID(user_a),
    )

    await _set_rls_context(db_conn, user_a)
    assert await db_conn.fetchval("SELECT count(*) FROM projects") == 1

    await _reset_to_postgres(db_conn)
    await _set_rls_context(db_conn, user_b)
    assert await db_conn.fetchval("SELECT count(*) FROM projects") == 0


async def test_nested_use_cases_isolation(db_conn, two_users):
    """Use cases (nested via project FK) invisible to non-owner."""
    user_a, user_b = two_users

    await _reset_to_postgres(db_conn)
    project_id = await db_conn.fetchval(
        "INSERT INTO projects (user_id, name) VALUES ($1, 'P') RETURNING id",
        uuid.UUID(user_a),
    )
    await db_conn.execute(
        "INSERT INTO use_cases (project_id, title) VALUES ($1, 'UC')",
        project_id,
    )

    await _set_rls_context(db_conn, user_a)
    assert await db_conn.fetchval("SELECT count(*) FROM use_cases") == 1

    await _reset_to_postgres(db_conn)
    await _set_rls_context(db_conn, user_b)
    assert await db_conn.fetchval("SELECT count(*) FROM use_cases") == 0


async def test_deeply_nested_chat_messages_rls(db_conn, two_users):
    """Chat messages (3-level join) protected by RLS."""
    user_a, user_b = two_users

    await _reset_to_postgres(db_conn)
    project_id = await db_conn.fetchval(
        "INSERT INTO projects (user_id, name) VALUES ($1, 'P') RETURNING id",
        uuid.UUID(user_a),
    )
    uc_id = await db_conn.fetchval(
        "INSERT INTO use_cases (project_id, title) VALUES ($1, 'UC') RETURNING id",
        project_id,
    )
    wf_id = await db_conn.fetchval(
        """
        INSERT INTO workflows (use_case_id, workflow_type, thread_id)
        VALUES ($1, 'plan_pricing', $2) RETURNING id
        """,
        uc_id,
        f"thread-{uuid.uuid4()}",
    )
    await db_conn.execute(
        """
        INSERT INTO chat_messages (workflow_id, role, content)
        VALUES ($1, 'user', 'hello')
        """,
        wf_id,
    )

    await _set_rls_context(db_conn, user_a)
    assert await db_conn.fetchval("SELECT count(*) FROM chat_messages") == 1

    await _reset_to_postgres(db_conn)
    await _set_rls_context(db_conn, user_b)
    assert await db_conn.fetchval("SELECT count(*) FROM chat_messages") == 0


async def test_global_embeddings_readable_by_any_user(db_conn, two_users):
    """Global m3ter_docs embeddings (project_id IS NULL) readable by any authenticated user."""
    _, user_b = two_users

    await _reset_to_postgres(db_conn)
    dim = 1536
    vec_str = "[" + ",".join(["0.01"] * dim) + "]"
    await db_conn.execute(
        """
        INSERT INTO embeddings (source_type, content, embedding, project_id)
        VALUES ('m3ter_docs', 'global doc', $1::vector, NULL)
        """,
        vec_str,
    )

    # User B (not the inserter) should still see global embeddings
    await _set_rls_context(db_conn, user_b)
    count = await db_conn.fetchval("SELECT count(*) FROM embeddings")
    assert count >= 1


async def test_project_scoped_embeddings_isolation(db_conn, two_users):
    """Project-scoped embeddings visible only to project owner."""
    user_a, user_b = two_users

    await _reset_to_postgres(db_conn)
    project_id = await db_conn.fetchval(
        "INSERT INTO projects (user_id, name) VALUES ($1, 'P') RETURNING id",
        uuid.UUID(user_a),
    )
    dim = 1536
    vec_str = "[" + ",".join(["0.01"] * dim) + "]"
    await db_conn.execute(
        """
        INSERT INTO embeddings (source_type, content, embedding, project_id)
        VALUES ('user_document', 'scoped doc', $1::vector, $2)
        """,
        vec_str,
        project_id,
    )

    await _set_rls_context(db_conn, user_a)
    count_a = await db_conn.fetchval(
        "SELECT count(*) FROM embeddings WHERE project_id IS NOT NULL"
    )
    assert count_a == 1

    await _reset_to_postgres(db_conn)
    await _set_rls_context(db_conn, user_b)
    count_b = await db_conn.fetchval(
        "SELECT count(*) FROM embeddings WHERE project_id IS NOT NULL"
    )
    assert count_b == 0


async def test_cascade_delete_project(db_conn, two_users):
    """Deleting a project should cascade to use_cases, workflows, etc."""
    user_a, _ = two_users

    await _reset_to_postgres(db_conn)
    project_id = await db_conn.fetchval(
        "INSERT INTO projects (user_id, name) VALUES ($1, 'P') RETURNING id",
        uuid.UUID(user_a),
    )
    uc_id = await db_conn.fetchval(
        "INSERT INTO use_cases (project_id, title) VALUES ($1, 'UC') RETURNING id",
        project_id,
    )
    await db_conn.execute(
        """
        INSERT INTO workflows (use_case_id, workflow_type, thread_id)
        VALUES ($1, 'plan_pricing', $2)
        """,
        uc_id,
        f"thread-{uuid.uuid4()}",
    )

    # Delete project
    await db_conn.execute("DELETE FROM projects WHERE id = $1", project_id)

    # Verify cascades
    uc_count = await db_conn.fetchval(
        "SELECT count(*) FROM use_cases WHERE project_id = $1", project_id
    )
    assert uc_count == 0
    assert await db_conn.fetchval(
        "SELECT count(*) FROM workflows WHERE use_case_id = $1", uc_id
    ) == 0
