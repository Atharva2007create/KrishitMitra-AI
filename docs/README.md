# Phase 0 documentation index

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

## Status vocabulary

- **Confirmed:** frozen by the Phase 0 brief.
- **Assumption:** working design choice to validate during implementation.
- **External verification required:** availability, terms, format, freshness, or access must be checked against the authoritative source before integration.

No document in this directory is evidence that an integration or deployed feature exists.
