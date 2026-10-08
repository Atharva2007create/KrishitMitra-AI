# Phase 3 verification record

Verified on 2026-10-07 in the development environment. This record distinguishes implemented and tested capabilities from live-corpus acceptance criteria.

## Status

**PASS — the Phase 3 retrieval foundation, deployment, live official-corpus ingestion and required evaluation baseline are complete.**

The official source audit also identified two source-specific limitations: the direct ICAR page has an expired official TLS certificate, and the ICAR-IIPR field guide requires reviewed OCR. Neither control was bypassed. Four official ICAR-IIPR HTML sources remain ready for ingestion.

## Executed verification

| Check | Result | Evidence |
|---|---|---|
| Phase 2 regression | PASS | 12 pre-Phase-3 tests passed before modification |
| Full backend suite | PASS | 36 tests passed; one third-party deprecation warning |
| Ruff lint and formatting | PASS | source and test tree clean |
| Strict mypy | PASS | 56 source files checked |
| Clean-database migration | PASS | migrations applied on a temporary pgvector PostgreSQL database |
| Migration downgrade/upgrade | PASS | `20261007_0002` downgraded to `20261007_0001` and upgraded to head |
| Development RDS migration | PASS | 13 core tables; `vector(768)` column present |
| Vector/text indexes | PASS | HNSW cosine and GIN text indexes present |
| Development S3 permission probe | PASS | encrypted test object uploaded, read and removed |
| CloudFormation role update | PASS | least-privilege `government/*` and `processed/*` object access deployed |
| Deployed API health/readiness | PASS | both endpoints returned HTTP 200 |
| Protected Phase 3 routes | PASS | OpenAPI exposes knowledge/source routes; anonymous requests return HTTP 401 |
| Live official ingestion | PASS | 4 documents, 23 chunks and 23 real 768-dimensional embeddings |
| Live ingestion repeat | PASS | all four documents returned `duplicate: true` |
| Live 60-query evaluation | PARTIAL | 27 passed and 33 failed; weak/blocked evidence areas retained honestly |

## Live corpus counts

- Verified-ready official documents: 4
- Blocked/review-required official documents: 2
- Dry-run candidate chunks: 23
- Active source documents in the Phase 3 corpus: 4
- Active knowledge chunks with real embeddings: 23
- Live evaluation questions executed: 60 of 60 (27 passed, 33 failed)
- Configured embedding model: `gemini-embedding-2`
- Configured and database vector dimension: 768

## Agricultural coverage

Based on the active corpus: soil, varieties, spacing, irrigation, weeds, pests, diseases and processing/milling are `PARTIAL`; seed treatment, fertilizer, drainage, harvest and post-harvest are `MISSING`. Source coverage is not inflated beyond the ingested evidence.

## Known limitations

1. Resolve the expired TLS certificate on the direct ICAR page externally or re-audit it later without bypassing TLS.
2. Add reviewed OCR for the scanned ICAR-IIPR field guide before activating its pest/disease evidence.
3. Improve ranking and expand verified evidence for the 33 failed evaluation cases.

Phase 4 answer generation, weather, markets and image analysis remain unimplemented by design.
