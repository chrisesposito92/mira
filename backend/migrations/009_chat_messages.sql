-- 009_chat_messages.sql: Conversation history (immutable — no updated_at)

CREATE TABLE IF NOT EXISTS chat_messages (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
  role        message_role NOT NULL,
  content     TEXT NOT NULL,
  metadata    JSONB DEFAULT '{}',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_workflow_created
  ON chat_messages(workflow_id, created_at);

-- RLS: 3-level nested — chat_messages → workflows → use_cases → projects
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS chat_messages_all_own ON chat_messages;
CREATE POLICY chat_messages_all_own ON chat_messages
  FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM workflows
      JOIN use_cases ON use_cases.id = workflows.use_case_id
      JOIN projects ON projects.id = use_cases.project_id
      WHERE workflows.id = chat_messages.workflow_id
        AND projects.user_id = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM workflows
      JOIN use_cases ON use_cases.id = workflows.use_case_id
      JOIN projects ON projects.id = use_cases.project_id
      WHERE workflows.id = chat_messages.workflow_id
        AND projects.user_id = auth.uid()
    )
  );
