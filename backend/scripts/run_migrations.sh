#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
MIGRATIONS_DIR="$BACKEND_DIR/migrations"

# Load DATABASE_URL from env or .env file
if [ -z "${DATABASE_URL:-}" ]; then
  if [ -f "$BACKEND_DIR/.env" ]; then
    DATABASE_URL=$(grep -E '^DATABASE_URL=' "$BACKEND_DIR/.env" | cut -d'=' -f2-)
  fi
fi

if [ -z "${DATABASE_URL:-}" ]; then
  echo "ERROR: DATABASE_URL not set. Export it or add to backend/.env"
  exit 1
fi

# Log target host without leaking credentials
DB_HOST="${DATABASE_URL#*@}"
echo "Running migrations against: ***@${DB_HOST}"

# Create tracking table if it doesn't exist
psql "$DATABASE_URL" -q <<'SQL'
CREATE TABLE IF NOT EXISTS schema_migrations (
  version TEXT PRIMARY KEY,
  applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
SQL

# Apply each migration in sorted order
for migration in "$MIGRATIONS_DIR"/*.sql; do
  [ -f "$migration" ] || continue
  filename=$(basename "$migration")

  already_applied=$(psql "$DATABASE_URL" -tAc \
    "SELECT 1 FROM schema_migrations WHERE version = '$filename'" 2>/dev/null || echo "")

  if [ "$already_applied" = "1" ]; then
    echo "SKIP  $filename (already applied)"
    continue
  fi

  echo "APPLY $filename ..."
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -1 -f "$migration"

  psql "$DATABASE_URL" -q -c \
    "INSERT INTO schema_migrations (version) VALUES ('$filename')"

  echo "  OK  $filename"
done

echo "All migrations applied."
