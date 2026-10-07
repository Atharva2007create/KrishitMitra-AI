# Phase 1 AWS development resources

Primary region: `ap-south-1` (Asia Pacific — Mumbai). Inventory verified on 2026-10-07. Resource names are identifiers, not credentials.

## Identity preflight

- Authenticated principal: IAM user `Atharva`, not root
- AWS account: `756829762972`
- Project/environment tags: `KrishiMitra-AI` / `development`

## Inventory

| Service | Resource | Purpose | Cost | Status |
|---|---|---|---|---|
| S3 | `krishimitra-dev-foundation-documentsbucket-scmqkzjtgvrf` | Private, encrypted, versioned official-source originals | Storage/requests may cost | Created and verified |
| S3 | `krishimitra-dev-foundation-imagesbucket-6u8bvoyzwbb5` | Private, encrypted, versioned crop images; lifecycle enabled | Storage/requests may cost | Created and verified |
| Cognito | `krishimitra-dev-users` / `ap-south-1_vMA5dFymW` | Development identity foundation | Usage/SMS may cost | Created; OTP flow deferred |
| Lambda | `krishimitra-dev-image-foundation` | Health-only future image-workflow foundation | Invocations/logs may cost | Invocation passed |
| CloudWatch | `/aws/lambda/krishimitra-dev-image-foundation`, `/krishimitra/dev/ec2` | Logs with 14-day retention | Ingestion/storage may cost | Created |
| RDS | `krishimitra-dev-db` (`db.t4g.micro`) | PostgreSQL 17.11 with pgvector 0.8.2 | **Ongoing charge while provisioned** | Private; connectivity passed |
| EC2 | `i-09e183b76df0f2546` (`t3.micro`) | Minimal FastAPI development host through SSM | **Ongoing charge while running** | Health passed |
| Amplify | `krishimitra-dev-web` / `d32qjrxuwdvdbd` | Next.js development hosting | Build/hosting may cost | App/branch created; repo connection blocked |

CloudFormation stacks `krishimitra-dev-foundation`, `krishimitra-dev-database`, and `krishimitra-dev-compute` reached `CREATE_COMPLETE`.

## Security validation

Both buckets have all public access blocked, AES-256 server-side encryption, and versioning. RDS reports `PubliclyAccessible=false`; TCP 5432 is allowed only from the backend security group. EC2 uses SSM, has no SSH ingress, and requires IMDSv2. EC2-to-RDS and EC2-to-S3 checks passed. Temporary browser-test ingress, containers, files, and S3 archives were removed after validation.

## Secrets strategy

RDS credentials are generated and held in Secrets Manager. Runtime roles provide AWS access. No credential is committed. Phone auto-verification/custom OTP is deliberately deferred; Phase 2 must define SMS delivery, spending controls, and the reviewed farmer flow before enabling it.

## Known deployment blocker

The Amplify app exists, but repository connection requires interactive GitHub OAuth authorization unavailable to the CLI session. No deployment is claimed. After pushing the Phase 1 commit, connect `main` in Amplify and configure an HTTPS API endpoint; an HTTPS page must not call the current plain-HTTP development endpoint.
