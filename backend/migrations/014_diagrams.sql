-- 014_diagrams.sql: Diagrams table for integration architecture diagrams

CREATE TABLE IF NOT EXISTS diagrams (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  project_id        UUID REFERENCES projects(id) ON DELETE SET NULL,
  customer_name     TEXT NOT NULL,
  title             TEXT NOT NULL DEFAULT '',
  content           JSONB NOT NULL DEFAULT '{"systems":[],"connections":[],"settings":{}}'::jsonb,
  schema_version    INTEGER NOT NULL DEFAULT 1,
  thumbnail_base64  TEXT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_diagrams_user_id ON diagrams(user_id);
CREATE INDEX IF NOT EXISTS idx_diagrams_project_id ON diagrams(project_id);
CREATE INDEX IF NOT EXISTS idx_diagrams_updated_at ON diagrams(updated_at);

DROP TRIGGER IF EXISTS trg_diagrams_updated_at ON diagrams;
CREATE TRIGGER trg_diagrams_updated_at
  BEFORE UPDATE ON diagrams
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- RLS: users can only access their own diagrams
ALTER TABLE diagrams ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS diagrams_all_own ON diagrams;
CREATE POLICY diagrams_all_own ON diagrams
  FOR ALL USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());
