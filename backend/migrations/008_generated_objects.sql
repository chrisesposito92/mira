-- 008_generated_objects.sql: AI-generated m3ter configuration entities

CREATE TABLE IF NOT EXISTS generated_objects (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  use_case_id       UUID NOT NULL REFERENCES use_cases(id) ON DELETE CASCADE,
  entity_type       entity_type NOT NULL,
  name              TEXT NOT NULL,
  code              TEXT,
  data              JSONB NOT NULL DEFAULT '{}',
  status            object_status NOT NULL DEFAULT 'draft',
  validation_errors JSONB DEFAULT '[]',
  m3ter_id          UUID,
  depends_on        UUID[] DEFAULT '{}',
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_generated_objects_use_case_id ON generated_objects(use_case_id);
CREATE INDEX IF NOT EXISTS idx_generated_objects_entity_type ON generated_objects(entity_type);
CREATE INDEX IF NOT EXISTS idx_generated_objects_status ON generated_objects(status);

DROP TRIGGER IF EXISTS trg_generated_objects_updated_at ON generated_objects;
CREATE TRIGGER trg_generated_objects_updated_at
  BEFORE UPDATE ON generated_objects
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- RLS: via use_cases → projects ownership
ALTER TABLE generated_objects ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS generated_objects_all_own ON generated_objects;
CREATE POLICY generated_objects_all_own ON generated_objects
  FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM use_cases
      JOIN projects ON projects.id = use_cases.project_id
      WHERE use_cases.id = generated_objects.use_case_id
        AND projects.user_id = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM use_cases
      JOIN projects ON projects.id = use_cases.project_id
      WHERE use_cases.id = generated_objects.use_case_id
        AND projects.user_id = auth.uid()
    )
  );
