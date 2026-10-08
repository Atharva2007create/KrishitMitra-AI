# Phase 4 evaluation and verification

Normal CI uses a pgvector PostgreSQL service and mocked embeddings/Gemini. It checks migrations upgrade/downgrade/upgrade, lint, formatting, strict typing, Phase 2/3 regression, category/FAQ localization and citation chains, grounded assistance, category mismatch, multilingual output, live-data/pesticide/image gates, prompt injection, ownership, attachment validation, and numeric fidelity. Live Gemini is separate so CI does not require billing or secrets.

The versioned evaluation set contains 80 English/Hindi/Marathi cases across FAQ-style, personalized, mismatch, follow-up, no-evidence, live-data, pesticide, and image-boundary classes. Expected outputs are status/intent classes rather than invented agricultural answers. Grounded-answer correctness must be judged against the current Phase 3 corpus and deterministic citations.

Before release, apply the migration from an empty database, validate all active FAQ citation chains, run the full backend suite, scan for secrets, and perform controlled live Gemini smoke tests in all three languages. Deployment evidence and actual FAQ counts must be reported separately from mocked CI results.

## Verified development deployment — 2026-10-08

- Backend checks: Ruff format/check passed, strict MyPy passed for 70 source files, and 50 tests passed. The sole warning is an upstream Starlette TestClient deprecation.
- Migration audit: downgrade to an empty database and upgrade through `20261008_0003` passed. The live RDS database reports `20261008_0003 (head)`.
- Runtime: `krishimitra-backend:phase4-final` returns healthy and database-ready responses and emits an `X-Request-ID` response header.
- Categories: 14 active localized V1 categories are present in configured display order.
- FAQs: 8 active FAQs, all with English, Hindi, and Marathi content. Counts are Sowing & Seeds 2; Soil & Land 1; Irrigation & Drainage 1; Pests 1; Diseases 1; Weeds 1; Post-Harvest 1.
- FAQ audit: zero missing translations and zero invalid active citation chains. Seven categories intentionally have evidence-supported FAQs; categories without sufficient Phase 3 coverage remain at zero rather than receiving invented content.
- Gemini: live structured multilingual generation passed with the stable Flash family. Temporary `503 high demand` responses from the newest models were handled safely with bounded retry/fallback; controlled curation used an available stable Flash model and activated output only after numeric and citation validation.
- Infrastructure: both CloudFormation templates validate, the compute stack is `UPDATE_COMPLETE`, and the attachment-prefix S3 permissions are deployed.
- Scope boundary: no live weather/market integration and no Lambda or Gemini image diagnosis were added; those remain Phase 5 work.

The GitHub-hosted CI run occurs after the commit is pushed. The same backend checks and migration cycle required by CI passed in the isolated AWS audit environment before this report was written.
