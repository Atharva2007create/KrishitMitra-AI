# Phase 8 finalization and deployment

Date: 2026-10-09

## Final architecture

KrishiMitra AI is a modular FastAPI application deployed in Docker on EC2, backed by private RDS PostgreSQL with pgvector. The static Next.js farmer application and admin console are hosted by Amplify. Cognito issues farmer SMS-OTP and administrator password tokens; FastAPI validates the JWT and enforces persisted FARMER/ADMIN authorization. Official-source documents and farmer images use private S3 buckets. The image pipeline uses S3 events, Lambda, a Secrets Manager Gemini credential, structured visual observations and RAG grounding. CloudWatch retains operational logs and alarms.

The deployed prototype endpoints are:

- Farmer web: `https://main.d32qjrxuwdvdbd.amplifyapp.com`
- Admin web: `https://main.d32qjrxuwdvdbd.amplifyapp.com/admin`
- API documentation: `https://vruyoz5jo4.execute-api.ap-south-1.amazonaws.com/docs`
- API readiness: `https://vruyoz5jo4.execute-api.ap-south-1.amazonaws.com/api/v1/ready`

The live resources retain their existing `development` names/tags. They form the approved production-style prototype environment, not a separately isolated commercial production account.

## Final verification

- Backend: Ruff lint and formatting passed; strict mypy passed for `app` and `scripts`; 77 tests passed against a disposable PostgreSQL 17/pgvector database.
- Migrations: empty-database upgrade, downgrade to base and re-upgrade passed. Deployed RDS reports `20261008_0004 (head)`.
- Web: lint, TypeScript, eight contract tests and the production static build passed. `/` and `/admin` were deployed in Amplify job 4 with the live API URL, region and public Cognito client ID.
- Mobile: lint, TypeScript and three contract tests passed. Expo public configuration resolves the image-picker camera/gallery permission text and suppresses unnecessary microphone permission. An EAS distributable was not produced because no Expo/EAS account was configured.
- AWS: EC2 instance/system checks, RDS availability, API health/readiness, Amplify deployment, Cognito auth-flow acceptance, Lambda state, S3 event wiring, private bucket public-access blocks and the image-analysis CloudWatch alarm were verified.
- Security: unauthenticated farmer and admin endpoints return 401; every admin route retains the server-side admin dependency; the Amplify-to-API CORS preflight returns 200; RDS is not public; both S3 buckets have all four public-access blocks enabled; no static AWS/Gemini credentials are required by browser bundles.

## Deployment and configuration

Required backend variables are catalogued in `.env.example`. On EC2, keep values in a root-readable runtime environment file or equivalent managed delivery mechanism and use the instance role for AWS access. Required values include the RDS URL, Cognito pool/client, private bucket names, Gemini secret ARN, image Lambda name, region and the exact Amplify CORS origin. Never put AWS keys, database passwords, Gemini keys, JWTs or OTPs in Git or client-side variables.

The backend release procedure is:

1. Build the checked-in `backend/Dockerfile` runtime target.
2. Run `alembic upgrade head` using the deployment environment.
3. Start the replacement container with host networking and `--restart unless-stopped`.
4. Require `/health`, `/api/v1/ready` and the expected OpenAPI routes to pass; retain the previous image/container for rollback until acceptance is complete.

For Amplify, build `apps/web` with `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_AWS_REGION` and `NEXT_PUBLIC_COGNITO_CLIENT_ID`, then deploy the contents of `out/`. These identifiers are public configuration; secrets must never use `NEXT_PUBLIC_*`.

For local development, follow the root README. CI provisions a disposable pgvector PostgreSQL service, validates the complete migration cycle, and runs backend, web and mobile quality gates. Web and mobile CI include their contract-test commands.

## Authentication acceptance boundary

The Cognito pool permits `PASSWORD` and `SMS_OTP` first factors, and its public client accepts the `USER_AUTH` choice-based flow. A safe nonexistent-user request confirmed that the configured password challenge is accepted without disclosing whether an account exists. Real farmer SMS delivery and authenticated farmer/admin journey testing require controlled test identities and access to their phone/password; those credentials were not available during finalization, so no SMS was sent and those smoke tests remain blocked.

## Residual limitations

- Phase 5 external government providers retain their documented credential, licensing and public-access limitations. The application represents unavailable, stale, partial and blocked states without fabricated data.
- Exhaustive authenticated screenshot comparison remains blocked by the earlier browser environment. Static builds and responsive implementation checks passed.
- Authenticated production farmer/admin smoke journeys are blocked until controlled Cognito test credentials are supplied.
- Source and ingestion administration remains read-only where no pre-existing safe mutation workflow exists.
- The latest remote GitHub Actions run predates these Phase 8 fixes and failed only at Ruff formatting. The repository formatting and CI workflow are corrected locally; a new remote result requires an explicit commit and push.
- A separate production AWS account/environment, custom domain, backup-restore drill, load test and EAS binary are outside the verified college-prototype deployment.

No Phase 9 is planned.
