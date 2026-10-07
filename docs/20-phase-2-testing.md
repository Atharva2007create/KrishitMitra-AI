# Phase 2 testing and verification

The automated suite covers migration/schema presence, pgvector availability, JWT signature and claim validation, missing authentication, farmer/admin role enforcement, CRUD validation, ownership isolation, protected deletion, and source metadata seeding. CI provisions pgvector PostgreSQL, performs upgrade/downgrade/upgrade, then runs formatting, lint, strict type checking, and tests.

Required commands:

```bash
ruff check .
ruff format --check .
mypy app
pytest
alembic downgrade base
alembic upgrade head
```

Deployment acceptance additionally checks the RDS Alembic revision and table count, Cognito pool/client/group configuration, public HTTPS health/readiness, OpenAPI availability, and a 401 response for a protected endpoint without a token. Secrets are checked for accidental tracking and temporary migration/test artifacts are removed.

Phase boundary: these checks do not validate Gemini, RAG, embeddings, document ingestion, image diagnosis, weather, market prices, or agronomic answer quality. Those capabilities are not implemented in Phase 2.

Verified development results on 2026-10-07: 12 automated tests passed; Ruff and formatting passed; strict MyPy passed for 35 application/script files; the local migration completed downgrade/upgrade with 11 tables, six source rows and pgvector; RDS reported revision `20261007_0001`, 11 core tables and six source rows; HTTPS health/readiness and OpenAPI returned 200; an unauthenticated protected request returned 401; and a POST CORS preflight returned 200.
