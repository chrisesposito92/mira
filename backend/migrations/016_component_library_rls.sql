-- 016_component_library_rls.sql: Enable RLS on component_library (read-only for authenticated users)

ALTER TABLE component_library ENABLE ROW LEVEL SECURITY;

-- Authenticated users can read all component library entries (shared reference data)
CREATE POLICY "component_library_select_authenticated"
  ON component_library
  FOR SELECT
  TO authenticated
  USING (true);
