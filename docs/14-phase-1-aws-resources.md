# Phase 1 AWS development resources

Primary region: `ap-south-1` (Asia Pacific — Mumbai). Inventory verified on 2026-10-07. Resource names are identifiers, not credentials.

## Identity preflight

- Authenticated principal: IAM user `Atharva`, not root
- AWS account: `756829762972`
- Project/environment tags: `KrishiMitra-AI` / `development`

## Inventory

| Service | Resource | Region | Environment | Purpose | Cost | Status |
|---|---|---|---|---|---|---|
| S3 | `krishimitra-dev-foundation-documentsbucket-scmqkzjtgvrf` | ap-south-1 | development | Private, encrypted, versioned official-source originals | Storage/requests may cost | Created and verified |
| S3 | `krishimitra-dev-foundation-imagesbucket-6u8bvoyzwbb5` | ap-south-1 | development | Private, encrypted, versioned crop images; lifecycle enabled | Storage/requests may cost | Created and verified |
| Cognito | `krishimitra-dev-users` / `ap-south-1_vMA5dFymW` | ap-south-1 | development | Development identity foundation | Usage/SMS may cost | Created; OTP flow deferred |
| Lambda | `krishimitra-dev-image-foundation` | ap-south-1 | development | Health-only future image-workflow foundation | Invocations/logs may cost | Invocation passed |
| CloudWatch | `/aws/lambda/krishimitra-dev-image-foundation`, `/krishimitra/dev/ec2` | ap-south-1 | development | Logs with 14-day retention | Ingestion/storage may cost | Created |
| RDS | `krishimitra-dev-db` (`db.t4g.micro`) | ap-south-1 | development | PostgreSQL 17.11 with pgvector 0.8.2 | **Ongoing charge while provisioned** | Private; connectivity passed |
| EC2 | `i-09e183b76df0f2546` (`t3.micro`) | ap-south-1 | development | Minimal FastAPI development host through SSM | **Ongoing charge while running** | Health passed |
| API Gateway | `krishimitra-dev-api` | ap-south-1 | development | Managed HTTPS facade for the development health API | Requests may cost | Created and verified |
| Amplify | `krishimitra-dev-web` / `d32qjrxuwdvdbd` | ap-south-1 | development | Next.js development hosting | Build/hosting may cost | Manual deployment job 3 passed |

CloudFormation stacks `krishimitra-dev-foundation`, `krishimitra-dev-database`, `krishimitra-dev-compute`, and `krishimitra-dev-api` are healthy (`CREATE_COMPLETE` or `UPDATE_COMPLETE`).

- Web: `https://main.d32qjrxuwdvdbd.amplifyapp.com`
- HTTPS API: `https://vruyoz5jo4.execute-api.ap-south-1.amazonaws.com`

## Security validation

Both buckets have all public access blocked, AES-256 server-side encryption, and versioning. RDS reports `PubliclyAccessible=false`; TCP 5432 is allowed only from the backend security group. EC2 uses SSM, has no SSH ingress, and requires IMDSv2. EC2-to-RDS and EC2-to-S3 checks passed. Temporary browser-test ingress, containers, files, and S3 archives were removed after validation.

## Secrets strategy

RDS credentials are generated and held in Secrets Manager. Runtime roles provide AWS access. No credential is committed. Phone auto-verification/custom OTP is deliberately deferred; Phase 2 must define SMS delivery, spending controls, and the reviewed farmer flow before enabling it.

## Deployment method

GitHub OAuth was unavailable in the automation session, so the Phase 1 static export was deployed directly through Amplify's manual deployment API. Deployment and verification passed. GitHub Actions independently validates every pushed commit; repository-connected Amplify deployments can be enabled later without changing the Phase 1 application architecture.
