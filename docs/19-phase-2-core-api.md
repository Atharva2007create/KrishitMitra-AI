# Phase 2 core API

All application endpoints are versioned under `/api/v1`. `/health` is public process health and `/api/v1/ready` checks database connectivity.

| Area | Endpoints | Access rule |
|---|---|---|
| Identity | `GET /me` | Authenticated user |
| Profile | `GET`, `POST`, `PATCH /farmer/profile` | FARMER, own profile |
| Farms | `GET`, `POST /farms`; `GET`, `PATCH`, `DELETE /farms/{id}` | FARMER, own records |
| Crop cycles | `GET`, `POST /crop-cycles`; `GET`, `PATCH /crop-cycles/{id}` | FARMER, through owned farm |
| Chat foundation | create/list/get/update sessions; create/list user messages | FARMER, own sessions/cycles |
| Feedback | `POST /feedback` | FARMER, owned target only |
| Administration | `GET /admin/health`, `GET /admin/sources` | ADMIN only; audited |

Cross-user lookups intentionally return 404 so record existence is not disclosed. Farm deletion returns 409 while dependent crop cycles exist. Chat messages in this phase are user-authored storage only—there is no generated assistant response, retrieval, or agricultural guidance.

API Gateway applies a small development-stage burst/rate limit. A production rollout should add per-identity quotas at the edge, stricter limits for mutation endpoints, `Retry-After` responses, monitoring, and abuse alarms after representative traffic testing. Application-level throttling is intentionally not duplicated in Phase 2.
