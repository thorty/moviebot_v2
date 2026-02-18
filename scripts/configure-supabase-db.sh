#!/usr/bin/env sh
set -eu

DB_HOST="${DB_HOST:-supabase-db}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-postgres}"
DB_USER="${DB_USER:-supabase_admin}"
DB_PASSWORD="${POSTGRES_PASSWORD:-postgres}"

export PGPASSWORD="$DB_PASSWORD"

echo "Waiting for Supabase roles to exist..."
attempts=0
until psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tAc "SELECT COUNT(*) FROM pg_roles WHERE rolname IN ('supabase_auth_admin','authenticator');" | grep -q "2"; do
  attempts=$((attempts + 1))
  if [ "$attempts" -ge 60 ]; then
    echo "Timed out waiting for required roles"
    exit 1
  fi
  sleep 1
done

echo "Configuring role passwords and auth function ownership..."
ESCAPED_DB_PASSWORD=$(printf "%s" "$DB_PASSWORD" | sed "s/'/''/g")

psql \
  -h "$DB_HOST" \
  -p "$DB_PORT" \
  -U "$DB_USER" \
  -d "$DB_NAME" \
  -v ON_ERROR_STOP=1 \
  -c "ALTER ROLE supabase_auth_admin LOGIN PASSWORD '${ESCAPED_DB_PASSWORD}';"

psql \
  -h "$DB_HOST" \
  -p "$DB_PORT" \
  -U "$DB_USER" \
  -d "$DB_NAME" \
  -v ON_ERROR_STOP=1 \
  -c "ALTER ROLE authenticator LOGIN PASSWORD '${ESCAPED_DB_PASSWORD}';"

psql \
  -h "$DB_HOST" \
  -p "$DB_PORT" \
  -U "$DB_USER" \
  -d "$DB_NAME" \
  -v ON_ERROR_STOP=1 <<'SQL'
DO $$
DECLARE
  function_signature text;
BEGIN
  FOR function_signature IN
    SELECT p.oid::regprocedure::text
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'auth'
  LOOP
    EXECUTE format('ALTER FUNCTION %s OWNER TO supabase_auth_admin', function_signature);
  END LOOP;
END
$$;
SQL

echo "Supabase DB role bootstrap finished"