# Phase 3 source provenance and safety

Every result must resolve this chain:

`government_sources → source_documents → knowledge_chunks`

The source row records organization, official base URL, trust status and verification time. The document row records exact title, original and canonical public URLs, S3 evidence key, MIME type, retrieval time, SHA-256, source version, activation state and page count. The chunk row records exact preserved text, its own hash, page/section, topic, embedding identity, ingestion version and activation state.

## Safety controls

- HTTPS host allowlist is enforced before and after redirects.
- HTML scripts and active elements are removed; document text is treated only as data.
- AWS credentials and Gemini keys are runtime-only and excluded from logs/API schemas.
- Originals use new version-aware object keys and are never overwritten or deleted by retry logic.
- Pesticide-related evidence is retained verbatim but flagged `requires_regulatory_validation`; Phase 3 does not create a new pesticide recommendation.
- Source APIs omit S3 keys, ingestion errors and internal diagnostics.
- Database constraints prevent empty chunks, negative indexes and non-768-dimensional metadata.

## Citation checks

Automated tests require each returned chunk to join an approved active government source and completed active document with a public URL. PDF chunks retain page ranges; HTML chunks retain the closest detected heading. Unknown publication dates stay null.
