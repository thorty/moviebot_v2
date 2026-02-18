#!/bin/sh
set -eu

DB_HOST="${DB_HOST:-supabase-db}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-postgres}"
DB_PASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"
DB_USER="${DB_USER:-postgres}"
MIGRATION_DIR="/workspace/supabase/migrations"

DB_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

echo "[migrations] ensuring migration tracking table exists"
psql "$DB_URL" -v ON_ERROR_STOP=1 <<'SQL'
create table if not exists public.schema_migrations (
  version text primary key,
  checksum text not null,
  applied_at timestamptz not null default timezone('utc', now())
);
SQL

found_any=0
for file in "${MIGRATION_DIR}"/*.sql; do
  if [ ! -f "$file" ]; then
    continue
  fi

  found_any=1
  version="$(basename "$file")"
  checksum="$(cksum "$file" | awk '{print $1}')"

  already_applied="$(psql "$DB_URL" -tA -v ON_ERROR_STOP=1 -c "select 1 from public.schema_migrations where version = '$version' limit 1;")"
  if [ "$already_applied" = "1" ]; then
    echo "[migrations] skip $version (already applied)"
    continue
  fi

  echo "[migrations] apply $version"
  psql "$DB_URL" -v ON_ERROR_STOP=1 -f "$file"
  psql "$DB_URL" -v ON_ERROR_STOP=1 -c "insert into public.schema_migrations(version, checksum) values ('$version', '$checksum');"
done

if [ "$found_any" -eq 0 ]; then
  echo "[migrations] no SQL files found in ${MIGRATION_DIR}"
  exit 1
fi

echo "[migrations] notifying PostgREST schema cache reload"
psql "$DB_URL" -v ON_ERROR_STOP=1 -c "NOTIFY pgrst, 'reload schema';"

echo "[migrations] completed"
