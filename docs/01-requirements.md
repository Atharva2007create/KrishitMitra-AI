# Requirements

## Functional requirements

| ID | Requirement |
|---|---|
| FR-01 | Cognito authenticates farmers by preferred phone/OTP flow and administrators by email/password; the API verifies JWTs and roles. |
| FR-02 | Farmers manage preferred language, general region, farms, and a current Tur crop cycle without requiring precise GPS. |
| FR-03 | Web and mobile use one versioned FastAPI REST API. |
| FR-04 | Chat accepts a farmer query, validates it, routes intent, retrieves approved evidence, and only then asks Gemini to generate a multilingual answer. |
| FR-05 | Every factual grounded response retains structured citations to documents and chunks; citations are separately displayable. |
| FR-06 | If evidence is insufficient, the service states the limitation and does not invent a recommendation. |
| FR-07 | The mobile client supports camera capture; both clients support valid image upload and asynchronous analysis status. |
| FR-08 | Image analysis separates visual observations from possible interpretations and grounds final guidance in approved evidence. |
| FR-09 | Weather and market results display source and observation/update timestamps. |
| FR-10 | Pesticide name, dose, rate, waiting period, and regulatory status require applicable official regulatory evidence. |
| FR-11 | Farmers can list sessions, review messages/citations, and submit feedback. |
| FR-12 | Administrators can inspect sources, documents, ingestion jobs/failures, feedback, flags, audit metadata, and health summaries. |
| FR-13 | Admins can disable superseded or unsafe source-document versions without deleting provenance. |

## Non-functional requirements

- Security: HTTPS, least-privilege IAM, private/restricted RDS, restricted S3, secrets outside Git, validated inputs, safe logging, and rate limiting.
- Reliability: explicit timeouts, retries with bounds, idempotent ingestion, asynchronous image status, and graceful dependency failure.
- Traceability: request/correlation ID, model/config version, retrieval timestamp, evidence identifiers, and audit events.
- Accessibility: responsive layouts, semantic controls, readable contrast, keyboard support on web, and localized text expansion.
- Localization: UI resources and model output support `mr`, `hi`, and `en`; citations preserve original titles/references.
- Freshness: time-sensitive data exposes observed/published/retrieved timestamps and must not be presented as current when stale.
- Maintainability: typed client contracts, versioned API, modular monolith backend, automated tests, and Docker-compatible runtime.
- Privacy: data minimization, purpose-limited collection, configurable retention, deletion workflow defined before production.
- Performance and availability targets remain **TBD until measured**; no unsupported benchmark is claimed.

## Query routing

- Cultivation → ICAR/ICAR-IIPR
- Weather → IMD
- Market → AGMARKNET/eNAM
- Pesticide → ICAR context plus applicable official pesticide regulatory evidence
- Maharashtra-specific → Maharashtra Agriculture Department plus relevant primary source
- Soil/fertilizer personalization → Soil Health Card context where accessible plus ICAR
- Multi-domain → merge evidence from the applicable approved routes while retaining source-specific provenance
