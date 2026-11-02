# Phase 1 — Core Stability and Login

## Status

Phase 1 is **incomplete / blocked**. The repository defects found in this pass were fixed and the available frontend checks passed, but this environment cannot prove real SMS delivery, a complete Cognito-to-dashboard session, fresh database connectivity, or execute the focused backend pytest suite. No claim of full Phase 1 completion is made.

## Baseline

- Starting branch: `main`
- Starting commit: `277f2d8e28ff7b509c385535da3da6ff34472755`
- Baseline working tree: clean
- The roadmap baseline commit `277f2d8` is the checked-out `HEAD`; no reset or branch switch was performed.

## Findings and disposition

### Verified and fixed in the repository

- Web and mobile already used the Cognito `SMS_OTP` challenge and supplied the response as `SMS_OTP_CODE`; the previously reported mobile challenge mismatch was already fixed.
- Web and mobile already normalized valid Indian input to E.164 and rejected malformed or duplicate-prefix input. Runtime tests were added for both implementations.
- Both clients could remain visually signed in when an API request other than the initial dashboard load returned `401`. A shared unauthorized callback now clears farmer data/session state and returns the user to login on every backend `401`.
- JWKS lookup failures from an unknown or malformed JWT could escape the verifier's authentication-error mapping. `PyJWKClientError` is now mapped to the same safe authentication failure as other invalid tokens.
- The FastAPI lifespan did not explicitly dispose the SQLAlchemy engine. Graceful shutdown now disposes the connection pool.
- Focused tests now cover verifier reuse, inactive-account rejection without writes, no repeated `last_login_at` write for the same authentication event, a fresh readiness connection per check, database-unavailable behavior, readiness `503`, and shutdown disposal.

### Already correct / not reproduced

- The backend verifier checks RS256 signature, issuer, expiry, issued-at time, token use, ID-token audience, and access-token client ID.
- The verifier dependency is cached across requests.
- Missing authentication already returns `401`; farmer/admin role checks remain server-side.
- `last_login_at` already changes only when the token's authentication time is newer, not on every request.
- Readiness already opens `engine.connect()` for each check and returns a controlled `503` when the check fails.
- Login errors, including Cognito invalid/expired-code responses and network failures, are caught by the existing web/mobile login UI without exposing an OTP or token.
- Web logout removes the stored token; mobile logout clears its in-memory token.
- Tokens are sent through the `Authorization: Bearer` header and are not placed in request URLs or application logs by the inspected Phase 1 code.

### Blocked or unable to verify

- **Real OTP and authenticated dashboard:** no local Cognito configuration file is present, and this run did not mutate or query live AWS. SMS delivery, interactive OTP entry, returned JWT acceptance by the deployed backend, and the live farmer dashboard remain unverified.
- **Fresh database connectivity:** no local environment file is present and `localhost:5432` was unreachable. No isolated database was confirmed, so database integration tests were intentionally not run against an unknown URL.
- **Backend pytest/ruff/mypy:** the available interpreter is Python 3.14 while the project requires Python 3.12, and `pytest` and `ruff` are not installed. Installing a new toolchain was outside this bounded pass. Source compilation succeeded, but that is not a substitute for the blocked tests.
- **Mobile production build:** the mobile package defines no production build script. Tests, lint, and TypeScript checks were run; no app-store/native build was attempted.

## Changes made

- `backend/app/security/cognito.py`: safely maps JWKS client errors to `AuthenticationError`.
- `backend/app/main.py`: disposes the SQLAlchemy engine during graceful shutdown.
- `backend/tests/test_authentication.py`: adds unknown-JWKS-key rejection coverage.
- `backend/tests/test_phase1_auth_stability.py`: adds focused verifier lifecycle, inactive-user, and login-write tests.
- `backend/tests/test_phase1_readiness.py`: adds fresh-connection, unavailable-database, readiness-503, and shutdown-disposal tests.
- `apps/web/src/lib/api.ts` and `apps/web/src/app/page.tsx`: clear farmer session/data on any API `401`.
- `apps/mobile/App.tsx`: preserves response status and clears farmer session/data on any API `401`.
- Web/mobile Phase 6 contract test files: add executable phone-normalization tests and session-expiry recovery checks.

## Commands and results

### Before changes

- `npm --prefix apps/web test` — **passed**, 9 tests.
- `npm --prefix apps/mobile test` — **passed**, 4 tests.
- `python -m pytest backend/tests/test_authentication.py backend/tests/test_health.py -q` — **blocked**, `pytest` not installed.

### After changes

- `npm --prefix apps/web test` — **passed**, 11 tests.
- `npm --prefix apps/web run lint` — **passed**.
- `npm --prefix apps/web run typecheck` — **passed**.
- `npm --prefix apps/web run build` — **passed**; `/`, `/_not-found`, and `/admin` were statically generated.
- `npm --prefix apps/mobile test` — **passed**, 6 tests.
- `npm --prefix apps/mobile run lint` — **passed**.
- `npm --prefix apps/mobile run typecheck` — **passed**.
- `python -m compileall -q backend/app backend/tests` — **passed**.
- `python -m ruff check ...` — **blocked**, `ruff` not installed.
- Configuration-presence check — root and backend `.env` files absent; values were not printed.
- Local database reachability check — **blocked/unavailable**, `localhost:5432` not reachable.

## Required operator follow-up

1. In an environment with the existing approved Cognito configuration, use the normal UI to request the real OTP for the approved test recipient and enter it there. Do not paste the OTP into logs or source.
2. Confirm the returned token opens the farmer dashboard and that the deployed backend accepts it; then verify invalid and expired codes remain rejected.
3. Provision or identify an isolated test PostgreSQL/pgvector database, configure it without exposing the URL, run migrations, and execute only the focused backend files:
   - `backend/tests/test_authentication.py`
   - `backend/tests/test_phase1_auth_stability.py`
   - `backend/tests/test_phase1_readiness.py`
   - the existing missing-token/dashboard tests that depend on the safe fixture
4. Run backend Ruff and mypy in the repository's supported Python 3.12 development environment.
5. If deployed database credentials are stale, rotate them through the existing secret-management path and restart/redeploy the backend through the existing operational process. No credentials were rotated here.

## Safety confirmation

No deployment, push, live AWS mutation, Cognito user/group change, production database change, secret disclosure, or unrelated Phase 2/3 work occurred.
