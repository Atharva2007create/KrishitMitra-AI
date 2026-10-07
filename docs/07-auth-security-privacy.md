# Authentication, security, and privacy

## Authentication and authorization

- Amazon Cognito is the identity provider.
- Farmer flow prefers verified mobile-number OTP; administrator flow uses email/password and protected administrator group/claim.
- FastAPI validates issuer, audience/client, signature, expiry, token use, and required claims against cached Cognito JWKS.
- PostgreSQL stores Cognito `sub`, application role/status, and profile data—not passwords, OTPs, raw JWTs, or refresh tokens.
- Route dependencies enforce roles; resource ownership is checked in queries/services. Admin UI visibility is not authorization.
- High-impact admin changes emit audit events with actor, reason, request ID, target, outcome, and timestamp.

## Security baseline

- HTTPS only outside local development; secure headers and controlled CORS allowlist.
- IAM least privilege with EC2/Lambda task roles; no root credentials or static AWS keys in Git.
- Secrets use an AWS-compatible secret/environment strategy and are redacted from logs/errors.
- RDS is private/restricted and reachable only on required paths; parameterized ORM/database access is mandatory.
- S3 blocks public access, encrypts data, separates document/image purposes, and uses short-lived narrowly scoped presigned operations.
- Uploads enforce allowed image formats, byte/pixel limits, checksum, safe generated object keys, content inspection/decoding, and quarantine on failure. Client MIME/name is not trusted.
- API validation includes schemas, length/range constraints, ownership checks, idempotency, timeouts, request-size limits, and rate limits by identity/IP with abuse monitoring.
- Logs omit message/image bodies, tokens, secrets, and unnecessary PII by default; correlation IDs support investigation.
- Dependencies/images receive automated vulnerability and secret scanning in later phases.
- Backups, restore tests, alerting, incident procedures, and key rotation are required before production.

## AI/RAG controls

- Retrieve only enabled, validated document versions from an allowlisted official-source registry.
- Treat query, uploaded image, extracted text, and retrieved documents as untrusted input.
- Separate system policy from evidence; instruct the model not to obey commands embedded in evidence.
- Supply bounded evidence and identifiers; validate cited IDs against that evidence.
- Refuse/qualify insufficient evidence; flag suspicious output.
- Require current applicable regulatory support for pesticide specifics.
- Record model/config version, retrieval time, evidence IDs, and safety outcome.

## High-risk areas and mitigations

| Risk | Baseline mitigation |
|---|---|
| Pesticide advice | Regulatory evidence gate, applicability/date checks, no unsupported dose/rate/waiting period, safety notice/review path |
| Image interpretation | Observation vs diagnosis separation, uncertainty, additional-context prompts, evidence grounding |
| Stale sources | published/updated/retrieved timestamps, expiry/status, disable/supersede workflow |
| Weather/market recency | visible observation time and staleness state; graceful unavailable response |
| Hallucinated sources | citations generated from stored evidence records only |
| Prompt injection | source allowlist, content isolation, constrained context/output, output validation |
| Malicious upload | restricted direct upload, size/type/decode checks, quarantine, no executable processing |

## Privacy and preliminary retention

Collect only name, account phone identifier, preferred language, general administrative location, optional village, farm acreage, Tur variety/cycle, sowing date, irrigation type, and relevant soil information. Precise GPS is optional and prohibited by default unless a later documented use case and consent justify it.

| Category | Preliminary rule |
|---|---|
| Account/profile/farm | Retain while account is active; define deletion/anonymization and backup expiry before production |
| Chats/citations | Configurable history; user deletion semantics and audit exception must be documented before launch |
| Uploaded images | Shortest practical configurable lifetime; disclose it; delete binary independently when possible |
| Analysis results | Retain only for user value/audit under disclosed policy; do not imply image certainty |
| Operational logs | Rolling minimum needed for security/reliability; minimize/redact PII |
| Audit logs | Longer controlled retention appropriate to security/provenance; exact period requires review |
| Feedback | Retain until resolved plus a defined analysis window; anonymize for aggregate use where possible |

Exact durations, consent copy, user export/deletion flows, and applicable legal obligations require formal review. This document makes no compliance certification.
