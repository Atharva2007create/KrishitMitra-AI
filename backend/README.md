# Core backend

Phase 2 FastAPI service with Alembic-managed PostgreSQL/pgvector schema, Cognito JWT verification, FARMER/ADMIN authorization, ownership-isolated farmer APIs, admin source metadata access, audit logs, and automated tests.

Run locally from the repository root with `docker compose up --build`. The container applies migrations before starting. API documentation is available at `/docs`; process and database checks are `/health` and `/api/v1/ready`.

Quality gates from this directory are `ruff check .`, `ruff format --check .`, `mypy app`, and `pytest`. Seed trusted source metadata with `python -m scripts.seed_government_sources`. Add an existing Cognito user to the trusted admin group with `python -m scripts.bootstrap_admin --username <username>`; the script never creates or stores a password.
