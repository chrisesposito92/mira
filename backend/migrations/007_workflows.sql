-- 007_workflows.sql: LangGraph workflow tracking

CREATE TABLE IF NOT EXISTS workflows (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  use_case_id       UUID NOT NULL REFERENCES use_cases(id) ON DELETE CASCADE,
  workflow_type     workflow_type NOT NULL,
  thread_id         TEXT NOT NULL UNIQUE,
  model_id          TEXT,
  status            workflow_status NOT NULL DEFAULT 'pending',
  interrupt_payload JSONB,
  error_message     TEXT,
  started_at        TIMESTAMPTZ,
  completed_at      TIMESTAMPTZ,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_workflows_use_case_id ON workflows(use_case_id);

DROP TRIGGER IF EXISTS trg_workflows_updated_at ON workflows;
CREATE TRIGGER trg_workflows_updated_at
  BEFORE UPDATE ON workflows
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- RLS: 2-level nested — workflows → use_cases → projects
ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS workflows_all_own ON workflows;
CREATE POLICY workflows_all_own ON workflows
  FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM use_cases
      JOIN projects ON projects.id = use_cases.project_id
      WHERE use_cases.id = workflows.use_case_id
        AND projects.user_id = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM use_cases
      JOIN projects ON projects.id = use_cases.project_id
      WHERE use_cases.id = workflows.use_case_id
        AND projects.user_id = auth.uid()
    )
  );
