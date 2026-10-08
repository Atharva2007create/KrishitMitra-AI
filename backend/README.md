# Core backend

FastAPI service with the Phase 2 authenticated core, Phase 3 official-document RAG, and Phase 4 problem-first multilingual guided assistance. Gemini explains retrieved evidence; citations remain backend-controlled.

Run locally from the repository root with `docker compose up --build`. The container applies migrations before starting. API documentation is available at `/docs`; process and database checks are `/health` and `/api/v1/ready`.

Quality gates from this directory are `ruff check .`, `ruff format --check .`, `mypy app`, and `pytest`. Seed trusted source metadata with `python -m scripts.seed_government_sources`. Add an existing Cognito user to the trusted admin group with `python -m scripts.bootstrap_admin --username <username>`; the script never creates or stores a password.

Validate the Phase 3 inventory with `python -m app.ingestion.cli --inventory ../data/sources/phase3-icar-pigeonpea.json --dry-run`. Live ingestion additionally requires an untracked `GEMINI_API_KEY` and `AWS_S3_BUCKET_DOCUMENTS`.

Curate Phase 4 FAQs with `python -m app.faq.cli generate --category sowing-seeds`; add `--activate` only after reviewing grounding and translations. Personalized assistance also requires the untracked Gemini credential. Attachment initiation requires private document/image bucket names and never performs Phase 5 analysis.
