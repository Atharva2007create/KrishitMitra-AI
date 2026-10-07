# Local development guide

## First run

1. Install the prerequisites listed in the root README.
2. Copy `.env.example` to ignored `.env` and choose a local-only PostgreSQL password.
3. Run `docker compose up --build -d`.
4. Verify `/health`, `/api/v1/ready`, PostgreSQL, and the vector extension.
5. Install/start `apps/web`; confirm the backend status becomes connected.
6. Install/validate `apps/mobile`; use a reachable host address for physical-device testing.

## Quality gate

Backend: Ruff lint/format, mypy, pytest. Web: ESLint, TypeScript, Next production build. Mobile: ESLint, TypeScript, Expo public-config validation. Root: Compose config/start/health, secret scan, and clean Git status.

## Safe reset

`docker compose down` stops containers without deleting the named database volume. Deleting volumes is intentionally omitted because it is destructive. No application tables should exist in Phase 1; only the `vector` extension is initialized.

## Boundaries

Do not add domain entities, Cognito flow code, dashboards, chat, RAG, embeddings, Gemini, image analysis, weather/market features, or government data in this phase.
