-- 004_org_connections.sql: m3ter organization credentials

CREATE TABLE IF NOT EXISTS org_connections (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id        UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  org_id         TEXT NOT NULL,
  org_name       TEXT NOT NULL DEFAULT '',
  api_url        TEXT NOT NULL DEFAULT 'https://api.m3ter.com',
  client_id      TEXT NOT NULL,
  client_secret  TEXT NOT NULL,
  status         connection_status NOT NULL DEFAULT 'inactive',
  last_tested_at TIMESTAMPTZ,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(org_id, user_id)
);

DROP TRIGGER IF EXISTS trg_org_connections_updated_at ON org_connections;
CREATE TRIGGER trg_org_connections_updated_at
  BEFORE UPDATE ON org_connections
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- RLS: users can only access their own connections
ALTER TABLE org_connections ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS org_connections_all_own ON org_connections;
CREATE POLICY org_connections_all_own ON org_connections
  FOR ALL USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());
