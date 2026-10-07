# Implementation roadmap

Each phase begins only after the previous phase's contracts and exit gate are accepted. Phase 0 does not authorize later work.

## Phase 0 — Architecture and requirements freeze

Outputs: this documentation set and secrets-free environment catalog. Gate: all acceptance items reviewed; contradictions resolved; no feature implementation.

## Phase 1 — Project foundation and AWS setup

Depends on Phase 0. Establish monorepo/application structure, developer tooling, CI baseline, environment strategy, AWS account/environment design, secure networking/IAM foundations, and non-production service configuration. Do not advance without reproducible setup and secret handling.

## Phase 2 — Database, authentication, core backend

Depends on foundation. Implement reviewed migrations, Cognito/JWT/role enforcement, user/profile/farm/crop-cycle/chat foundations, API envelopes, ownership, audit baseline, and tests.

## Phase 3 — Government data and RAG knowledge system

Depends on database/storage and verified source access. Implement source registry, versioned ingestion, S3 originals, extraction/validation/chunking, embeddings, pgvector/text retrieval, and provenance. Start with verified ICAR/IIPR Tur material.

## Phase 4 — Gemini AI and multilingual farmer assistant

Depends on evaluated retrieval and citation model. Select current stable model identifiers, implement constrained grounding/output, mr/hi/en behavior, refusals, citation validation, and evaluation harness.

## Phase 5 — Live government data and Lambda image analysis

Depends on verified integration methods and safety gates. Integrate authorized weather/market/regulatory/soil/state sources as available; implement timestamp/staleness behavior and the asynchronous S3→Lambda→visual observations→official retrieval→grounded result flow.

## Phase 6 — Complete web and mobile applications

Depends on stable APIs. Build responsive Next.js farmer UX and React Native/Expo app with native camera, localization, accessibility, failure states, and shared contracts.

## Phase 7 — Admin system and full integration

Depends on ingestion/monitoring contracts. Build protected admin workflows, source/document/job controls, feedback/flags, safe system summaries, and complete cross-module integration.

## Phase 8 — Testing, AWS production deployment, finalization

Depends on all prior gates. Execute security/privacy/agronomy reviews, 100–150-question evaluation, E2E/load/failure/recovery tests, backup restore, observability and cost checks, then deploy through an approved production process. Report measured results only.

## Cross-phase change control

Changes to evidence-before-generation, source/citation invariants, Tur-only V1 scope, common backend, fixed stack, safety gates, or privacy baseline require an explicit architecture decision update and impact review.
