-- 006_use_cases.sql: Use cases table (nested under projects)

CREATE TABLE IF NOT EXISTS use_cases (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id           UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  title                TEXT NOT NULL,
  description          TEXT NOT NULL DEFAULT '',
  contract_start_date  DATE,
  billing_frequency    billing_frequency,
  currency             TEXT NOT NULL DEFAULT 'USD',
  target_billing_model TEXT NOT NULL DEFAULT '',
  notes                TEXT NOT NULL DEFAULT '',
  status               use_case_status NOT NULL DEFAULT 'draft',
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_use_cases_project_id ON use_cases(project_id);

DROP TRIGGER IF EXISTS trg_use_cases_updated_at ON use_cases;
CREATE TRIGGER trg_use_cases_updated_at
  BEFORE UPDATE ON use_cases
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- RLS: access via project ownership (JOIN-based)
ALTER TABLE use_cases ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS use_cases_all_own ON use_cases;
CREATE POLICY use_cases_all_own ON use_cases
  FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM projects
      WHERE projects.id = use_cases.project_id
        AND projects.user_id = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM projects
      WHERE projects.id = use_cases.project_id
        AND projects.user_id = auth.uid()
    )
  );
