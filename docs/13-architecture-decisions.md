# Architecture decision record

Status: accepted for V1 by the Phase 0 brief. Revisit only for critical incompatibility supported by evidence.

| Decision | Rationale | Consequence |
|---|---|---|
| PostgreSQL rather than document-only DB | Relational ownership, conversations, source versions, citations, audits, and transactions dominate; JSONB still supports bounded flexible metadata. | One consistent transactional model; schema discipline required. |
| pgvector rather than separate vector DB | Keeps V1 embeddings beside provenance and metadata, reduces infrastructure, and supports hybrid SQL filtering. | Reassess only if measured corpus/latency/scale exceeds it. |
| FastAPI backend | Python AI/data ecosystem, typed validation, OpenAPI, async support, and testability fit the API/RAG workload. | Shared modular monolith serves web/mobile. |
| Next.js web | Supports responsive farmer/admin UI, TypeScript, and Amplify hosting. | Web contract shares types/schema with API where practical. |
| React Native + Expo mobile | Cross-platform TypeScript delivery with camera/gallery support and shared frontend skills. | Native-specific permission and secure-storage testing remains necessary. |
| Amazon Cognito | Managed identity, OTP-capable farmer flow, admin credentials/groups, JWT integration with AWS. | SMS/access configuration and costs must be verified. |
| S3 originals | Durable restricted object storage, versioning/lifecycle, and event integration for documents/images. | Metadata/checksums remain in PostgreSQL; buckets are private. |
| EC2 for FastAPI | Matches the fixed stack and offers straightforward Docker hosting/control for V1. | Team owns patching, scaling, TLS/ingress, deployment, and operations. |
| Lambda only for image workflow | Event-driven bounded orchestration suits asynchronous S3 image work without splitting all backend domains. | Timeouts, retries, idempotency, and callback state must be explicit. |
| Gemini Flash family | Fixed generation/multimodal family prioritizing speed/cost; exact stable model chosen at implementation. | Model/config versions are recorded; no obsolete identifier is frozen now. |
| Official sources as factual layer | Traceability and safety require evidence to precede factual agricultural generation. | Insufficient evidence produces limitation/refusal; citations are structured records. |
| Tur-only initial crop | Enables a coherent corpus, evaluation set, safety review, and achievable V1. | Other crops require separate evidence, metadata, evaluation, and approval. |

## Repository inspection record

On 2026-10-07, the specified public GitHub repository `Atharva2007create/KrishitMitra-AI` displayed “This repository is empty.” The local Phase 0 baseline was therefore created without overwriting or deleting existing project material. Command-line cloning could not authenticate on the host, so this local checkout was initialized with `main` and the supplied repository URL as `origin`; nothing was pushed.
