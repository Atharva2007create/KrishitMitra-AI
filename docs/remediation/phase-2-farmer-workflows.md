# Phase 2 — Farmer Features and Core User Workflows

## Status

Phase 2 repository work is complete, but live/integration verification is **partially blocked**. The verified code defects were fixed and available web/mobile checks pass. Backend pytest, an isolated database run, live AWS image processing, paid-model behavior, official live-data credentials, and an authenticated visual comparison were unavailable, so those flows are not claimed as live-passed.

## Baseline and Phase 1 handoff

- Starting branch: `main`
- Starting commit: `6fa97e4` (`fix: stabilize phase 1 login and readiness`)
- Starting worktree: clean
- Phase 1 handoff: `docs/remediation/phase-1-core-stability-login.md`
- Phase 1's live OTP, fresh-database, and backend-toolchain blockers were preserved and not re-investigated.

## Findings and disposition

### Verified and fixed

- Web and mobile could create profile, farm, and crop-cycle records but offered no update path after onboarding. Minimal edit forms now use the existing PATCH contracts and reload saved data.
- Web chat archive did not refresh the list; mobile exposed no archive action. Both now call the existing archive contract, refresh state, and clear an open archived conversation.
- FAQ request errors were swallowed and shown as a misleading evidence-empty state. Both clients now distinguish load failure from a genuine empty result and provide Retry.
- After an image polling timeout, both clients created a new upload when the user retried. They now retain the attachment/analysis identifiers and retry the same logical upload.
- Mobile accepted assets with unsupported/unknown MIME or unknown/oversized file size until the backend rejected them. It now applies the backend's JPEG/PNG/WebP and 10 MB limits before upload.
- Repeated API analysis requests could invoke Lambda more than once because the attachment remained pending. The endpoint now row-locks the attachment, transitions it to processing, and returns the existing analysis for concurrent/repeated processing requests. The Lambda's existing atomic content-hash claim remains the second idempotency layer for API/S3-event overlap.
- Lambda invocation errors previously left the logical upload pending. They now persist a terminal failure with a non-sensitive error code and return a controlled `503`.
- A missing result object could leave analysis pending/processing indefinitely. Stale analysis now reaches `FAILED` with `ANALYSIS_TIMEOUT`; retry resets the processing window.

### Already correct / not reproduced

- Backend profile, farm, and crop-cycle ownership, validation, creation, update, and transition contracts already existed.
- Root web/mobile state reloads profile, farms, cycles, categories, and chat history after onboarding changes and session restoration.
- FAQ and assistance responses carry evidence status and real citation fields from stored retrieved chunks; empty retrieval fails closed.
- Live Gemini answers already run numeric-fidelity validation. Unsupported generated numbers produce `INSUFFICIENT` with `UNSUPPORTED_NUMERIC_CLAIM`.
- Retrieved `requires_regulatory_validation` metadata is checked before model generation. Pesticide/dose/concentration terms fail closed with `REQUIRES_REGULATORY_VALIDATION`; an empty regulatory adapter returns unavailable rather than confirmed advice.
- The image Lambda already validates object identity, size, MIME signature and metadata; uses an atomic S3 claim; rejects treatment instructions; writes terminal expected/unexpected failure results; and does not log image bytes or secrets.
- Weather and market adapters already fail closed when credentials/data are unavailable, reject stale weather, and use an application-scoped cached service. The clients show unavailable states without invented live values. Seven-day forecast and historical trend remain explicitly unavailable under the current contract.
- Major approved farmer destinations remain present on web and mobile. No notification data or unsupported live panels were fabricated.

### Partial or blocked

- The backend exposes archive but no pin contract. Archive was completed on both platforms; pinning was not invented.
- Backend pytest could not run because this machine has Python 3.14 rather than the project's Python 3.12 environment and lacks pytest. New backend safety tests compile but are not reported as executed.
- No isolated PostgreSQL/pgvector fixture was available; CRUD, retrieval, citation, and history integration tests were not executed here.
- No live AWS/S3/Lambda/Gemini call was made. Image behavior was reviewed against the implementation and covered by existing/new mocked test code only.
- No official IMD/AGMARKNET credentials were available. Only the existing fail-closed implementation and tests were inspected.
- No authenticated rendered app session was available, so no fresh screenshot/PPT visual comparison was claimed. Existing design/CSS was preserved; changes were limited to controls and states within current components.
- No English/Hindi/Marathi agricultural answer-quality claim is made; only routing and existing localization behavior were inspected.

## Changed files

- `backend/app/core/settings.py`: adds a bounded image-analysis timeout.
- `.env.example`: documents the non-secret image-analysis timeout setting.
- `backend/app/api/v1/attachments.py`: adds row-locked analysis claiming, retry, processing transitions, and terminal invocation failures.
- `backend/app/api/v1/images.py`: converts stale pending/processing analyses to terminal failures.
- `backend/tests/test_phase2_workflow_safety.py`: adds focused stale-analysis terminal-state coverage.
- `apps/web/src/lib/api.ts`: exposes existing farm/crop-cycle PATCH contracts.
- `apps/web/src/components/FarmerApp.tsx`: adds onboarding edits, reliable archive refresh, FAQ failure/retry, and same-upload image retry.
- `apps/web/tests/phase6-contracts.test.mjs`: adds Phase 2 farmer-workflow contract coverage.
- `apps/mobile/App.tsx`: adds onboarding edits, archive, FAQ failure/retry, image validation, and same-upload retry.
- `apps/mobile/tests/phase6-contracts.test.mjs`: adds Phase 2 farmer-workflow contract coverage.

## Commands and results

### Baseline

- `npm --prefix apps/web test` — passed, 11 tests.
- `npm --prefix apps/mobile test` — passed, 6 tests.
- `python -m pytest backend/tests/test_phase4_guided_assistance.py backend/tests/test_phase5_live_data_images.py -q` — blocked, pytest unavailable.
- `python -m compileall -q backend/app infrastructure/lambda/image_foundation backend/tests` — passed.

### After changes

- `npm --prefix apps/web test` — passed, 12 tests.
- `npm --prefix apps/web run lint` — passed.
- `npm --prefix apps/web run typecheck` — passed.
- `npm --prefix apps/web run build` — passed; `/`, `/_not-found`, and `/admin` generated.
- `npm --prefix apps/mobile test` — passed, 7 tests.
- `npm --prefix apps/mobile run lint` — passed.
- `npm --prefix apps/mobile run typecheck` — passed.
- Focused backend pytest command including `test_phase2_workflow_safety.py` — blocked, pytest unavailable.
- `python -m compileall -q backend/app backend/tests infrastructure/lambda/image_foundation` — passed.
- `git diff --check` — passed; line-ending notices only.

Frontend tests use local source/runtime checks and no external services. Existing backend tests use mocks/isolated fixtures by design, but they were not executable in this environment. No real approved test environment was exercised.

## Remaining operator actions

1. Run the focused Phase 2 backend tests in the supported Python 3.12 environment against a confirmed isolated PostgreSQL/pgvector fixture.
2. In an approved non-production AWS environment, verify one image through upload, processing, terminal result, retry, invocation failure, and timeout without exposing content or secrets.
3. With approved official credentials, smoke-test supported live weather/market responses and retain the current unavailable behavior when sources fail.
4. Once an authenticated local/test login is available, render the affected onboarding, FAQ, chat-history, upload, weather, market, and profile screens at mobile and desktop sizes and compare them with the authoritative UI reference.

## Safety confirmation

No deployment, push, Git remote change, production database mutation, live AWS change, real SMS, paid AI call, real farmer data use, secret exposure, fabricated source/data, admin work, or Phase 3 work occurred.
