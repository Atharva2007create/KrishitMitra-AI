#!/usr/bin/env bash
set -euo pipefail

: "${DATABASE_ENDPOINT:?DATABASE_ENDPOINT is required}"
: "${DATABASE_SECRET_ARN:?DATABASE_SECRET_ARN is required}"
: "${DOCUMENTS_BUCKET:?DOCUMENTS_BUCKET is required}"
: "${IMAGES_BUCKET:?IMAGES_BUCKET is required}"

dnf install -y postgresql15 >/dev/null
secret_json="$(aws secretsmanager get-secret-value --secret-id "$DATABASE_SECRET_ARN" --query SecretString --output text)"
db_user="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["username"])' "$secret_json")"
db_password="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["password"])' "$secret_json")"
unset secret_json

PGPASSWORD="$db_password" psql "host=$DATABASE_ENDPOINT port=5432 dbname=krishimitra user=$db_user sslmode=require" \
  -v ON_ERROR_STOP=1 \
  -c "SELECT version();" \
  -c "CREATE EXTENSION IF NOT EXISTS vector;" \
  -c "SELECT extversion FROM pg_extension WHERE extname = 'vector';"
unset db_password

for bucket in "$DOCUMENTS_BUCKET" "$IMAGES_BUCKET"; do
  key="connectivity/phase1-$(date +%s).txt"
  printf 'KrishiMitra Phase 1 connectivity check' | aws s3 cp - "s3://$bucket/$key" --only-show-errors
  aws s3api head-object --bucket "$bucket" --key "$key" --query '{Encrypted:ServerSideEncryption,Bytes:ContentLength}' --output json
  aws s3api delete-object --bucket "$bucket" --key "$key" >/dev/null
done

curl --fail --silent http://localhost:8000/health
docker --version
