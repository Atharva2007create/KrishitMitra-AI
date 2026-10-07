# REST API contract plan

Base path: `/api/v1`. JSON unless upload negotiation requires otherwise. Cognito bearer JWT is required except health and explicitly designated authentication-bootstrap routes. Error bodies use a stable `{code, message, request_id, details?}` envelope. Pagination uses opaque cursors. This is a contract plan, not implemented endpoints.

## User, profile, farm, crop cycle

| Method and route | Purpose | Auth/role | High-level request → response |
|---|---|---|---|
| `GET /me` | Current application identity | any user | — → user, role, language, setup state |
| `PATCH /me/preferences` | Language/settings | any user | allowed preferences → updated preferences |
| `GET/PATCH /farmer-profile` | Read/update farmer profile | farmer | profile fields → profile |
| `GET/POST /farms` | List/create owned farms | farmer | farm details → farm/list |
| `GET/PATCH/DELETE /farms/{farm_id}` | Manage owned farm | farmer owner | changes → farm/status; delete semantics finalized later |
| `GET/POST /farms/{farm_id}/crop-cycles` | List/create Tur cycles | farmer owner | cycle fields → cycle/list |
| `GET/PATCH /crop-cycles/{cycle_id}` | Read/update owned cycle | farmer owner | changes → cycle |

Cognito sign-in/OTP happens through supported Cognito client flows; the API does not receive passwords or OTP secrets. Any bootstrap endpoint added later must not duplicate Cognito identity storage.

## Chat and feedback

| Method and route | Purpose | Auth/role | Request → response |
|---|---|---|---|
| `POST /chat/sessions` | Create session | farmer | language/title/context refs → session |
| `GET /chat/sessions` | List own sessions | farmer | cursor → page |
| `GET /chat/sessions/{id}` | Session and messages | owner/admin-limited | cursor → session page |
| `POST /chat/sessions/{id}/messages` | Submit query | farmer owner | text, language, optional farm/cycle → grounded response, citations, limitations |
| `GET /messages/{id}/citations` | Structured citations | message owner/admin-limited | — → citation list |
| `POST /feedback` | Submit feedback | farmer | target, rating/category/comments → feedback receipt |

## Image analysis

| Method and route | Purpose | Auth/role | Request → response |
|---|---|---|---|
| `POST /image-analyses/uploads` | Initiate restricted presigned upload | farmer | filename/type/size/checksum → upload target + expiry + analysis ID |
| `POST /image-analyses/{id}/submit` | Confirm upload/start asynchronous job | owner | S3 object version + crop context → accepted/status URL |
| `GET /image-analyses/{id}` | Status and final structured result | owner/admin-limited | — → status, observations, interpretation, guidance, citations, limitations |

## Weather, market, sources

| Method and route | Purpose | Auth/role | Request → response |
|---|---|---|---|
| `GET /weather` | Location-aware weather/advisory lookup | farmer | state/district/taluka/date window → timestamped data/advisory/source |
| `GET /markets/tur` | Tur mandi information | farmer | region/mandi/date/cursor → timestamped prices/source |
| `GET /sources` | Public-to-user approved source metadata | authenticated | filters → enabled sources |
| `GET /sources/documents/{id}` | Citation document detail | citation-authorized user | — → title, organization, date, reference, relevant location |

## Administration

| Method and route | Purpose | Auth/role | Request → response |
|---|---|---|---|
| `GET/PATCH /admin/sources` | Inspect/update approved source metadata/status | admin | filters or status change → source(s) |
| `GET/PATCH /admin/documents/{id}` | Inspect/disable document version | admin | status/reason → document |
| `GET /admin/ingestion-jobs` | List jobs/failures | admin | filters/cursor → jobs |
| `POST /admin/ingestion-jobs` | Request a supported ingestion run later | admin | source/document + idempotency key → accepted job |
| `POST /admin/ingestion-jobs/{id}/retry` | Retry eligible failed job | admin | reason/idempotency key → accepted job |
| `GET /admin/feedback` | Review feedback | admin | filters/cursor → feedback |
| `GET/PATCH /admin/response-flags/{id}` | Review/resolve flag | admin | status/notes → flag |
| `GET /admin/users` | Minimal authorized user overview | admin | filters/cursor → minimized user summaries |
| `GET /admin/health-summary` | Non-secret service summary | admin | — → component status/recency |

## Contract rules

- Every object is ownership-checked server-side; client-provided user IDs are not trusted.
- Create/retry/upload operations support idempotency keys.
- Weather and market responses include source, observation/publication time, retrieval time, and staleness state.
- AI endpoints return structured `answer`, `language`, `citations`, `limitations`, `safety_notices`, and `request_id` fields.
- Exact schemas, status codes, limits, and OpenAPI examples are finalized during Phases 2–5 without changing these domain boundaries casually.
