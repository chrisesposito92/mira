-- 011_embeddings.sql: Vector embeddings with HNSW index

CREATE TABLE IF NOT EXISTS embeddings (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_type embedding_source NOT NULL,
  source_id   UUID REFERENCES documents(id) ON DELETE CASCADE,
  content     TEXT NOT NULL,
  metadata    JSONB DEFAULT '{}',
  embedding   vector(1536) NOT NULL,
  project_id  UUID REFERENCES projects(id) ON DELETE CASCADE,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_embeddings_project_id ON embeddings(project_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_source ON embeddings(source_type, source_id);

-- HNSW index for fast cosine similarity search
CREATE INDEX IF NOT EXISTS idx_embeddings_hnsw ON embeddings
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- RLS: dual policy
ALTER TABLE embeddings ENABLE ROW LEVEL SECURITY;

-- Global m3ter_docs (project_id IS NULL): readable by any authenticated user
DROP POLICY IF EXISTS embeddings_select_global ON embeddings;
CREATE POLICY embeddings_select_global ON embeddings
  FOR SELECT
  USING (project_id IS NULL);

-- Project-scoped: full access for project owner
DROP POLICY IF EXISTS embeddings_all_project_own ON embeddings;
CREATE POLICY embeddings_all_project_own ON embeddings
  FOR ALL
  USING (
    project_id IS NOT NULL
    AND EXISTS (
      SELECT 1 FROM projects
      WHERE projects.id = embeddings.project_id
        AND projects.user_id = auth.uid()
    )
  )
  WITH CHECK (
    project_id IS NOT NULL
    AND EXISTS (
      SELECT 1 FROM projects
      WHERE projects.id = embeddings.project_id
        AND projects.user_id = auth.uid()
    )
  );
