# Project documentation index

| Document | Purpose |
|---|---|
| [00 Project scope](00-project-scope.md) | Frozen V1 boundary, roles, goals, assumptions, non-goals |
| [01 Requirements](01-requirements.md) | Functional and non-functional requirements |
| [02 System architecture](02-system-architecture.md) | Logical architecture, flows, routing, decisions |
| [03 Database design](03-database-design.md) | Conceptual relational schema, constraints, retention, indexes |
| [04 API contract plan](04-api-contract-plan.md) | Proposed REST resources and authorization |
| [05 RAG and data ingestion](05-rag-and-data-ingestion.md) | Ingestion, retrieval, grounding, provenance |
| [06 Government source strategy](06-government-source-strategy.md) | Six source groups and verification requirements |
| [07 Auth, security, privacy](07-auth-security-privacy.md) | Cognito, authorization, security and retention baseline |
| [08 Web/mobile IA](08-web-mobile-information-architecture.md) | Screen map and client responsibilities |
| [09 Image analysis](09-image-analysis-design.md) | Safe observation-to-grounded-guidance workflow |
| [10 AWS deployment](10-aws-deployment-architecture.md) | Intended AWS responsibilities and networking |
| [11 Testing strategy](11-testing-strategy.md) | Future verification and RAG evaluation plan |
| [12 Roadmap](12-implementation-roadmap.md) | Phase dependencies and gates |
| [13 Architecture decisions](13-architecture-decisions.md) | Compact ADR set for fixed choices |
| [13 Phase 1 development setup](13-phase-1-development-setup.md) | Executable foundation and connectivity model |
| [14 Phase 1 AWS resources](14-phase-1-aws-resources.md) | Live inventory, cost and security status |
| [15 Local development guide](15-local-development-guide.md) | Startup, validation and phase boundaries |
| [16 Phase 1 verification report](16-phase-1-verification-report.md) | Executed checks, exceptions and deployment blockers |
| [17 Phase 2 database](17-phase-2-database.md) | Implemented schema, migrations, constraints and RDS procedure |
| [18 Phase 2 authentication](18-phase-2-authentication.md) | Cognito JWT validation, role mapping and admin bootstrap |
| [19 Phase 2 core API](19-phase-2-core-api.md) | Implemented endpoints, ownership rules and rate-limit strategy |
| [20 Phase 2 testing](20-phase-2-testing.md) | Quality gates, security tests and deployment verification |
| [21 Phase 3 government data](21-phase-3-government-data.md) | Verified ICAR/ICAR-IIPR inventory, storage and version policy |
| [22 Phase 3 ingestion pipeline](22-phase-3-ingestion-pipeline.md) | Acquisition, extraction, chunking, embedding and CLI |
| [23 Phase 3 RAG retrieval](23-phase-3-rag-retrieval.md) | Hybrid search, filters, APIs and Phase 4 boundary |
| [24 Phase 3 source provenance](24-phase-3-source-provenance.md) | Citation chain and safety controls |
| [25 Phase 3 RAG evaluation](25-phase-3-rag-evaluation.md) | 60-question dataset and quality gates |
| [26 Phase 3 verification](26-phase-3-verification.md) | Executed checks, deployment evidence and remaining blockers |
| [27 Phase 4 guided assistance](27-phase-4-guided-assistance.md) | Problem-first flow and orchestration architecture |
| [28 Phase 4 problem categories](28-phase-4-problem-categories.md) | V1 categories, translations and RAG mappings |
| [29 Phase 4 FAQ system](29-phase-4-faq-system.md) | Controlled grounded FAQ lifecycle and APIs |
| [30 Phase 4 Gemini grounding](30-phase-4-gemini-grounding.md) | Provider boundary, structured output and retrieval-first policy |
| [31 Phase 4 multilingual and safety](31-phase-4-multilingual-safety.md) | Languages, evidence statuses and deterministic gates |
| [32 Phase 4 attachment foundation](32-phase-4-attachment-foundation.md) | Secure upload contract and explicit Phase 5 boundary |
| [33 Phase 4 evaluation](33-phase-4-evaluation.md) | Evaluation set, tests and verification gates |
| [34 Phase 5 source access matrix](34-phase-5-source-access-matrix.md) | Verified official access modes, credentials and honest source status |
| [35 Phase 5 live data service](35-phase-5-live-data-service.md) | Normalized adapters, endpoints, freshness and failure isolation |
| [36 Phase 5 image analysis](36-phase-5-image-analysis.md) | Private upload, Lambda observation, idempotency and RAG handoff |
| [37 Phase 5 deployment and operations](37-phase-5-deployment-and-operations.md) | Migration, CloudFormation, S3 event wiring and monitoring |
| [38 Phase 5 testing](38-phase-5-testing.md) | Automated and cloud acceptance gates |

## Status vocabulary

- **Confirmed:** frozen by the Phase 0 brief.
- **Assumption:** working design choice to validate during implementation.
- **External verification required:** availability, terms, format, freshness, or access must be checked against the authoritative source before integration.

Implementation claims in Phase 2 documents are backed by the verification record in document 20.
