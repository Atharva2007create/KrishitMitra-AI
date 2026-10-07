# Testing strategy

No product tests or accuracy benchmarks exist in Phase 0. This document defines future verification.

## Test layers

- Unit: validators, routing, metadata filters, safety gates, citation mapper, localization utilities.
- Database: constraints, ownership, transactions, vector/text queries, disabled-version exclusion, migrations later.
- API: schemas, status/errors, pagination, idempotency, timeouts, dependency failures.
- Authentication/authorization: JWT validation, expired/wrong audience tokens, farmer/admin separation, object-level access.
- RAG: retrieval relevance, metadata applicability, insufficient-evidence behavior, conflict/staleness handling.
- Citations: every displayed citation resolves to supplied chunk/document version; no invented references.
- Multilingual: intent/retrieval across Marathi/Hindi/English, terminology, script rendering, citation preservation.
- Image: file validation, state transitions, poor/ambiguous images, observation-vs-diagnosis, regulatory gating.
- External-source failure: unavailable, malformed, stale, rate-limited, partial and changed-schema inputs.
- Security: injection, prompt injection, upload abuse, rate limiting, CORS, broken ownership/role controls, secret/PII logging.
- End-to-end web: farmer and admin critical journeys, responsive/accessibility coverage.
- End-to-end mobile: OTP journey, camera/gallery permissions, background/network interruption, localized UI.
- Operational: backup restore, alerting, deployment rollback, load/latency/cost measurement before production.

## RAG evaluation set

Create approximately 100–150 expert-validated Tur questions with expected evidence, acceptable answer facts, prohibited claims, language variants, region/stage metadata, and freshness requirements. Cover varieties, soil, sowing, seed treatment, fertilizer, irrigation, drainage, pests, disease, harvesting, post-harvest, weather, market, pesticide safety, and soil/nutrient context.

Include answerable, ambiguous, multi-domain, adversarial/prompt-injection, conflicting-source, stale-source, and deliberately unanswerable cases. Prevent evaluation-set leakage into prompt tuning.

## Metrics to establish—not claim

Retrieval recall@k/precision@k, citation precision and coverage, grounded factual support, refusal correctness, applicability/freshness errors, multilingual semantic equivalence, harmful pesticide recommendation rate, image observation schema validity, latency, availability, and cost. Release thresholds require agronomy/product/security review after baselines are measured.

## Release gates

Automated tests, source-contract checks, manual agronomy review of high-risk cases, security review, privacy/retention approval, backup/restore evidence, and production-like end-to-end tests. No accuracy percentage is valid until the dataset, rubric, reviewers, model/config, and results are versioned.
