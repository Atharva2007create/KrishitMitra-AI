# Phase 3 — Administrator Access, Security Boundaries, and Final Closure

## Status

Phase 3 repository fixes are complete, but final operational verification is **blocked/partial**. Admin role revocation and safe sign-in errors were corrected, and available frontend/build/configuration checks pass. No controlled administrator identity, isolated database backend test environment, local CloudFormation validator, or reachable deployed-site browser was available. The backend origin remains publicly modeled and is not claimed secure.

## Baseline and handoffs

- Starting branch: `main`
- Starting commit: `fdde30a` (`fix: complete phase 2 farmer workflows`)
- Starting worktree: clean
- Reviewed `docs/remediation/phase-1-core-stability-login.md` and `docs/remediation/phase-2-farmer-workflows.md`.
- No reset, branch switch, deployment, push, or live mutation was performed.

## Findings and disposition

### Verified and fixed

- Existing database users retained their stored role even when the current verified Cognito token no longer carried the `administrators` group. Removing a user from that group therefore did not reliably revoke backend admin access. The backend now derives and synchronizes the role from every verified token: only the configured `administrators` group maps to `ADMIN`; absent or unsupported groups map to `FARMER`.
- The admin login component swallowed Cognito sign-in failures that occurred before server authorization, leaving no visible response. It now displays a generic retryable sign-in failure without echoing an email, password, token, or provider detail.
- Focused tests now explicitly cover unauthenticated denial, farmer denial across every admin route, server-side dependencies on every admin endpoint, admin allowance, current-group upgrades/downgrades, unsupported groups, and recursive operational-metadata redaction.

### Already correct / not reproduced

- The exact backend role enum is `ADMIN`/`FARMER`; the configured Cognito group is `administrators`.
- Cognito tokens are signature-, issuer-, client/audience-, expiry-, issued-at-, and token-use validated before groups are trusted.
- Every `/api/v1/admin/*` endpoint uses the server-side `require_admin` dependency. Frontend verification is additional UX gating, not the authorization boundary.
- The admin console verifies `/admin/health` before storing a separate admin token, clears state on logout or `401`/`403`, and exposes read-only operational views supported by the backend.
- Admin routes do not expose `cognito_sub`, S3 keys, bucket names, raw stored images, or credential-like nested metadata. Existing metadata redaction covers secret/token/password/credential/API-key names recursively.
- Existing ownership tests cover farmer records, farms, crop cycles, chat sessions, attachments, and analyses. Changing a URL or client state does not bypass backend ownership/admin dependencies.
- Admin endpoints currently provide operational reads only; no unsupported mutating admin action was invented.

### Controlled administrator workflow — blocked

- No explicitly authorized isolated administrator identity or local Cognito configuration was present. No account was created or modified.
- Consequently, real Cognito password challenge completion, live JWT group claims, dashboard/table loading, invalid/expired live credentials, and deployed admin logout are not claimed passed.
- Automated web checks are source/contract checks. Backend authorization tests are mocked/isolated test code but could not execute locally because pytest is unavailable.

## Backend-origin security

The exposure is verified in repository templates:

- `compute-database.yml` assigns the backend a public IP and permits TCP port 8000 from `0.0.0.0/0`.
- `compute.yml` and `compute-database.yml` output a public `http://<public-ip>:8000/health` origin.
- `api.yml` uses an API Gateway HTTP proxy with a caller-supplied `BackendOriginUrl`; the repository's modeled origin is public plain HTTP. Authorization headers can therefore traverse the public origin path without origin TLS.
- No private backend subnets, internal ALB/NLB, listener/certificate, API Gateway VPC Link/private integration, or source security-group design exists in the repository.

Infrastructure was intentionally left unchanged. Restricting the security group alone would break API Gateway's public HTTP integration, while adding guessed subnets, load balancers, certificates, IDs, or VPC links would not be safely deployable or verifiable.

### Required architecture/operator sequence

1. Choose a supported private encrypted origin: for example, API Gateway VPC Link to an internal load balancer, with backend instances in private subnets and TLS appropriate to the chosen integration.
2. Define the load balancer/listener, certificate/DNS ownership, private subnet routing, health checks, and security-group-to-security-group rules in an approved environment design.
3. Point API Gateway to the private integration, validate authorization-header forwarding and backend health through the gateway, then close public port 8000 and remove the public backend IP/origin outputs.
4. Verify the direct origin is unreachable, gateway-to-origin transport meets the chosen TLS/private-network guarantee, health/readiness work, and farmer/admin JWT behavior is unchanged.
5. Retain the previous stack parameters/template revision for rollback. If validation fails, restore the prior integration before removing replacement resources; do not reopen unrestricted port 8000 as the permanent rollback state.

The origin must not be reported secured until those changes are deployed and direct-origin/gateway transport behavior is verified.

## Changed files

- `backend/app/security/dependencies.py`: synchronizes persisted user role from current verified Cognito groups.
- `backend/tests/test_phase7_security_unit.py`: adds current-group role upgrade, revocation, and unsupported-group coverage.
- `backend/tests/test_phase7_admin.py`: adds unauthenticated denial across every admin route.
- `apps/web/src/components/AdminApp.tsx`: displays a generic safe Cognito sign-in failure.
- `apps/web/tests/phase7-admin.test.mjs`: covers visible safe sign-in failure behavior.
- `docs/remediation/phase-3-admin-security-closure.md`: records Phase 3 evidence, blockers, origin risk, and closure actions.

## Checks and results

### Baseline

- `npm --prefix apps/web test` — passed, 12 tests.
- Focused backend pytest command — blocked, pytest unavailable.
- Repository template inspection — confirmed public port/public IP/plain-HTTP proxy design.

### After changes

- `npm --prefix apps/web test` — passed, 13 tests.
- `npm --prefix apps/web run lint` — passed.
- `npm --prefix apps/web run typecheck` — passed.
- `npm --prefix apps/web run build` — passed; `/`, `/_not-found`, and `/admin` generated.
- `npm --prefix apps/mobile test` — passed, 7 tests.
- `npm --prefix apps/mobile run lint` — passed.
- `npm --prefix apps/mobile run typecheck` — passed.
- `EXPO_NO_TELEMETRY=1 npx --no-install expo config --type public` from `apps/mobile` — passed; public iOS/Android configuration resolved.
- `npm audit --omit=dev --audit-level=critical --offline` for web and mobile — passed, 0 vulnerabilities reported in both lockfiles.
- `python -m compileall -q backend/app backend/tests` — passed.
- Focused backend pytest and Ruff — blocked because the modules are not installed in the local interpreter.
- CloudFormation local validation — blocked because `cfn-lint` is unavailable. AWS CLI validation was not used because it is a remote AWS call, not local validation.
- Read-only checks of the known Amplify root and `/admin` URLs — blocked because the browsing environment could not access the site. No form or authenticated request was attempted.
- `git diff --check` — passed; line-ending notices only.

No mocked result is represented as a live administrator or deployed-site pass.

## Remaining operator actions and risks

1. Provision or identify one authorized administrator in an isolated Cognito environment, add only that identity to the existing `administrators` group, and test sign-in, server verification, all read-only admin modules, logout, invalid/expired credentials, and group-removal revocation.
2. Run backend pytest/Ruff/mypy and migrations in the repository CI/supported isolated PostgreSQL environment.
3. Approve and implement the private encrypted backend-origin architecture described above, validate it before closing the old path, and confirm direct-origin access fails afterward.
4. Install/use `cfn-lint` and run template validation before any change-set review. Apply infrastructure only through an approved reviewed change set with rollback monitoring.
5. Repeat the deployed root/admin availability checks from an authorized network without submitting forms or using personal data.

## Deferred work

- Multi-user OTP beyond the single approved prototype recipient.
- Unverified external weather/market integrations.
- Scaling, Multi-AZ, load, and disaster-recovery testing.
- EAS/app-store release.
- Live production deployment or production data changes.

## Safety confirmation

No deployment, push, Git remote change, live AWS/Cognito/security-group/database mutation, real credential/OTP use, destructive test, production data access, or additional remediation phase occurred.
