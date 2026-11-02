# KrishiMitra AI audit remediation report

Date: 2026-10-16  
Repository baseline: `main` at `afe989d`  
Scope: repository-only remediation; no deployment, push, live AWS mutation, real SMS, Gemini request, or production-data operation.

## Outcome

This pass fixed the repository-verifiable authentication, agricultural-safety, reliability, ingestion, browser-hardening, onboarding, pagination, reproducibility, and CI issues listed below. Findings that require a cloud operator, verified external data, a production identity, or an architectural decision remain explicitly blocked. The application must not be described as production-ready until those actions and the blocked end-to-end checks are completed.

## Findings and disposition

| Finding | Disposition | Evidence or remediation |
| --- | --- | --- |
| API Gateway forwards to a public HTTP EC2 origin and port 8000 is publicly modeled | **Verified; operator/architecture action required** | `infrastructure/cloudformation/api.yml` accepts an arbitrary HTTP origin and `compute-database.yml` gives the instance a public IP. The repository does not define the private subnets/load balancer/VPC Link/certificate needed for a safe testable replacement, so no invented IaC was added. See operator actions below. |
| Browser security headers absent | **Fixed in repository** | Added Amplify-compatible `customHttp.yml` with HSTS, CSP, frame denial, MIME sniffing protection, referrer policy, and permissions policy. |
| Web tokens stored in local storage; no refresh/revocation | **Verified; architectural follow-up required** | Headers reduce XSS/clickjacking exposure. Moving tokens to server-set HttpOnly cookies, adding refresh rotation, and Cognito global sign-out require a deliberate auth/BFF design and were not improvised. Tokens are not logged or placed in URLs. |
| Mobile Cognito challenge uses `SMS_OTP` response key | **Fixed** | Mobile now submits `SMS_OTP_CODE`, checks the returned challenge, normalizes Indian numbers strictly, supports resend/change-number, and does not hardcode an OTP length. |
| Web phone normalization silently accepts malformed values | **Fixed** | Both clients accept only valid 10-digit Indian mobile numbers or normalized `91` format and reject double-prefix/invalid input. |
| OTP recovery absent | **Fixed for farmer flow** | Web and mobile now support resend and change-number recovery and replace the incorrect six-digit placeholder with a code-length-neutral prompt. Cognito expiry errors are surfaced without bypassing the challenge. |
| Admin NEW_PASSWORD_REQUIRED/MFA/reset challenges absent | **Verified; not changed** | No isolated Cognito admin fixture or challenge contract is present. Server-side ADMIN authorization remains intact. Implementing account recovery/challenge policy requires the authorized Cognito operator and test identity; no live admin was created. |
| `last_login_at` written on every authenticated request and before inactive rejection | **Fixed** | Inactive users are rejected before mutation. Cognito `auth_time`/`iat` is recorded only when a newer authenticated session is observed, avoiding writes for every API request. |
| JWT/JWKS verifier recreated per request | **Fixed** | The verifier is process-scoped with `lru_cache`, preserving PyJWKClient caching. |
| Live weather/market cache recreated per request | **Fixed** | A shared process-scoped live-data service is used by both API routes and assistance. It remains correctly documented as per-process, not distributed. |
| Rate limiter has an intra-process race | **Fixed locally; distributed limit still required** | Added an async lock around each process's limiter. Multiple replicas still require an approved distributed store/API gateway policy. |
| Readiness catches too few database failures | **Fixed** | Fresh connection failures represented by `SQLAlchemyError`, including authentication/DBAPI errors, now produce the existing unavailable response path without leaking details. |
| Running deployment may have a stale RDS password | **Unable to verify/change in this repository-only pass** | No production secret was read. Operator must rotate/reload the managed secret, redeploy/restart, and test a fresh connection as described below. |
| Live AI answers do not enforce numeric fidelity | **Fixed** | Live generated answers are checked against retrieved evidence. Unsupported quantities/units fail safely with `INSUFFICIENT` and `UNSUPPORTED_NUMERIC_CLAIM`; no value is fabricated. |
| Pesticide wording can bypass controls | **Fixed defensively** | Expanded pesticide/dose phrasing and Indic-language gates. Retrieved chunks marked `requires_regulatory_validation` now force a safe regulatory-validation state before Gemini generation. |
| Runtime regulatory adapter has no verified records | **Verified; external data required** | It remains empty by default. Pesticide-specific advice fails safely rather than pretending validation succeeded. An approved PPQS/CIBRC dataset is required. |
| Profile/farm/crop-cycle creation missing from clients | **Fixed** | Added minimum sequential onboarding in web and mobile using the existing POST contracts: profile, farm, then active Tur crop cycle. No schema or design-system rewrite was made. |
| Chat/message lists unbounded | **Fixed compatibly** | Added optional bounded `limit`/`offset` query parameters with existing list response shapes and defaults. Existing clients remain compatible. Admin endpoints retain their existing hard caps; a cursor/envelope design remains future work. |
| Ingestion follows redirects before allowlist validation | **Fixed** | Redirects are followed manually, with HTTPS/official-host validation on every hop, a five-redirect cap, timeout, MIME allowlist, declared and streaming 20 MiB limits, and rejection of unapproved/internal destinations. |
| Image Lambda can perform duplicate concurrent Gemini work | **Fixed in repository** | Added an atomic S3 `If-None-Match` claim keyed by model/content hash. Competing invocations reuse the result or return processing instead of calling Gemini twice. Claim cleanup supports retry. |
| Unexpected image failures can remain non-terminal | **Fixed** | Unexpected exceptions now write a generic terminal `FAILED` result when object identity is available, without exposing internals. |
| Image polling has no timeout state | **Fixed** | Web/mobile show an explicit long-running state instead of silently stopping. A later analyze action remains available; no fake success is shown. |
| Current GitHub backend CI is red | **Historical remote run verified; local Ruff issue not reproduced** | Current checkout passes Ruff check and format after remediation. No push was allowed, so GitHub remains unchanged until an authorized user pushes. |
| JavaScript manifests use `latest` | **Fixed** | Web/mobile manifests and lock roots are pinned to the already-installed lockfile versions; no broad dependency upgrade was performed. |
| Dependency audit absent from CI | **Fixed** | Web/mobile CI now runs production dependency audits at critical severity. Known non-critical Expo advisories are not hidden and require a controlled SDK-compatible upgrade. |
| Mobile production dependency advisories | **Verified; not upgraded here** | Current audit reports 22 advisories (15 high, 7 moderate) in Expo/Metro/React Native transitive dependencies. The offered forced fix downgrades to Expo 44 and is breaking. Exact versions are pinned; a controlled Expo SDK migration and real-device testing remain required. |
| RAG evaluation is 27/60 with 33 failures | **Verified from versioned documentation; not re-run** | `docs/25-phase-3-rag-evaluation.md` and `docs/26-phase-3-verification.md` record the result. The database-backed evaluator could not be run in this local environment. Expected answers were not changed. |
| Hindi/Marathi retrieval quality unproven; lexical query is English | **Verified limitation** | No measured Indic evaluation dataset/result exists. The PostgreSQL query still uses the English configuration; changing indexing/search configuration requires measured migration work. |
| IMD, AGMARKNET, eNAM, PPQS/CIBRC, Maharashtra Agriculture, and Soil Health Card gaps | **Verified capability states / external blockers** | Existing capability reporting remains honest (`BLOCKED`/`PARTIAL`). No credentials, records, endpoints, forecasts, or market history were invented. |
| M-01–M-15 and D-01–D-14 visual acceptance | **Not re-verified in this pass** | No claim of exhaustive PPT comparison is made. This remediation preserved the design and added only compact onboarding/recovery controls. |

## Files changed

- Authentication and session behavior: `backend/app/security/cognito.py`, `backend/app/security/dependencies.py`, `apps/web/src/lib/api.ts`, `apps/web/src/components/FarmerApp.tsx`, `apps/mobile/App.tsx`.
- Farmer onboarding: `apps/web/src/app/page.tsx`, `apps/web/src/components/FarmerApp.tsx`, `apps/web/src/lib/api.ts`, `apps/web/src/app/globals.css`, `apps/mobile/App.tsx`.
- Agricultural safety and caching: `backend/app/services/assistance.py`, `backend/app/services/retrieval.py`, `backend/app/integrations/government/__init__.py`, `backend/app/api/v1/live_data.py`.
- Reliability/security: `backend/app/db/connection.py`, `backend/app/api/v1/chat.py`, `backend/app/ingestion/acquisition.py`, `infrastructure/lambda/image_foundation/handler.py`, the least-privilege claim cleanup permission in `infrastructure/cloudformation/phase5-image-analysis.yml`, and `customHttp.yml`.
- Tests and CI: backend Phase 3/4/5 tests, mobile Phase 6 contract test, `.github/workflows/ci.yml`.
- Reproducibility: web/mobile `package.json` and lock roots now contain exact versions. `.gitignore` excludes only the local package-install scratch directory used during validation.

## Validation actually run

| Command | Result |
| --- | --- |
| `ruff check . --no-cache` | **PASS** |
| `ruff format --check . --no-cache` | **PASS** (100 files) |
| Python 3.13 `compileall` over backend app/tests and Lambda handler | **PASS** |
| Web `npm test` | **PASS**, 9/9 |
| Web `npm run lint` | **PASS** |
| Web `npm run typecheck` | **PASS** |
| Web `npm run build` | **PASS**, static `/`, `/_not-found`, `/admin` |
| Web `npm audit --omit=dev --audit-level=critical` | **PASS**, 0 vulnerabilities |
| Mobile `npm test` | **PASS**, 4/4 including corrected OTP contract |
| Mobile `npm run lint` | **PASS** |
| Mobile `npm run typecheck` | **PASS** |
| Mobile `npm audit --omit=dev --audit-level=critical` | **PASS at configured critical gate**; 22 non-critical-gate advisories remain (15 high, 7 moderate) |
| `EXPO_NO_TELEMETRY=1 npx expo config --type public` | **PASS** |
| Backend pytest/mypy | **BLOCKED locally**: bundled Python targets were incomplete/incompatible; installing declared dependencies was aborted because the sandbox package download was extremely slow. No AWS/database fallback was used. CI remains the authoritative isolated PostgreSQL run after an authorized push. |

The new backend tests cover redirect allowlisting, streaming download limits, unsupported numeric claims, expanded pesticide phrasing, and atomic image-analysis claims. They are syntax/Ruff clean but were not falsely reported as executed.

## Required operator actions

1. **Private encrypted origin:** place the backend behind an internal HTTPS ALB/NLB or an API Gateway private integration/VPC Link; use private subnets and security-group-to-security-group ingress; close EC2 port 8000 from the internet; remove the public origin; verify direct-origin access fails and API Gateway-to-origin TLS succeeds.
2. **Database credentials:** rotate or retrieve the current managed RDS secret through the approved deployment mechanism, replace the backend task/container environment, restart, and verify `/api/v1/ready` opens a fresh connection. Never paste the secret into a command log.
3. **Cognito:** provision an isolated administrator, exercise new-password/MFA/reset flows, decide the supported policy, and test server-side role rejection. Request SNS production access/SMS sandbox exit only when multi-user rollout is approved.
4. **Regulatory data:** approve and version current PPQS/CIBRC records before enabling pesticide validation. Until then the safe unavailable response must remain.
5. **Government providers:** obtain documented IMD/data.gov.in credentials and approved endpoints; keep blocked/partial states until a live contract test passes.
6. **Operations:** approve Multi-AZ, longer backup retention, deletion protection, restore/failover drills, load tests, monitoring, provenance, and rollback procedures.
7. **Mobile dependencies/release:** perform an Expo-compatible SDK upgrade, rerun audit/build tests, create an EAS binary, and complete a real-device OTP/onboarding/upload smoke test. Do not apply a blanket audit fix.

## Remaining risks and limitations

- Local-storage tokens and absent refresh/revocation remain an explicit browser-auth architecture risk.
- Rate limiting and live-data caches are safe only within one process, not distributed across replicas.
- Admin list APIs use bounded hard caps rather than a complete cursor-pagination envelope.
- Live admin E2E, real farmer OTP E2E, backend JWT integration, database migrations/tests, RAG evaluation, image-Lambda integration, real-device mobile verification, exhaustive PPT comparison, load/failover/restore tests, and live security-header verification remain unexecuted in this repository-only pass.
- The remote GitHub workflow remains unchanged until an authorized user reviews, commits, and pushes these files. No commit or push was performed.

## Safety confirmation

No live AWS resource, Cognito user/group, database record, secret, security group, deployment, Git branch, remote, or GitHub state was modified. No real SMS or Gemini request was sent. No secret value, token, password, connection string, phone number, or private farmer record was printed or added. All source changes are limited to verified remediation, supporting tests, CI, and this report.
