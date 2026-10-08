# Phase 5 deployment and operations

Apply migration `20261008_0004`. It adds verified-upload metadata, image-analysis linkage, structured visual results, idempotency fields, timestamps and the `IMAGE_INSUFFICIENT`/`LIVE_DATA_UNAVAILABLE` states.

The reproducible Lambda deployment entry point is:

```powershell
.\infrastructure\scripts\deploy-phase5-image-analysis.ps1 `
  -ImagesBucketName <private-images-bucket> `
  -CodeBucketName <private-deployment-bucket> `
  -GeminiSecretArn <gemini-secret-arn> `
  -Region ap-south-1
```

The script packages the dependency-free handler, uploads it privately, deploys `phase5-image-analysis.yml`, preserves unrelated S3 notifications and installs `.jpg`, `.jpeg`, `.png` and `.webp` S3 event filters under `farmer-uploads/`.

CloudFormation provisions least-privilege S3/Secrets Manager/logging permissions, 14-day logs and an error alarm. Account-level Lambda concurrency limits remain available for shared development workloads. The checked-in compute templates grant the backend only the needed Lambda invocation and private upload/result access.

Monitor Lambda errors, duration, throttles and structured error codes. Backend logs include source error code, endpoint latency, evidence status and analysis state. Repeated source-authentication errors are configuration incidents, never silent fallback signals.
