# Phase 5 official-source access matrix

Verified on 2026-10-08. `READY` means the adapter is implemented and becomes live when its documented credential is configured. `PARTIAL` means an official source exists, but no stable documented public API was verified. `BLOCKED` means the official integration requires credentials or onboarding absent from this environment. The application never converts a blocked source into an estimated value.

| Source | Official location | Access classification | Current state | Freshness/provenance behavior |
|---|---|---|---|---|
| ICAR/IIPR | `https://www.icar-iipr.org.in/` and Phase 3 approved documents | `OFFICIAL_DOCUMENT` | `PASS` for the existing RAG corpus | Document title, URL, page/section, publication metadata and retrieval time |
| IMD | `https://api.imd.gov.in/public/api_reference.html` | `LIVE_API` | `BLOCKED` until an IMD portal token is configured; direct requests returned HTTP 401 | Observation time, retrieval time and computed age; bounded cache TTL |
| AGMARKNET / OGD India | `https://www.data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi` | `LIVE_API` | `BLOCKED` until an OGD API key is configured; resource id `9ef84268-d588-465a-a308-a864a43d0070` is verified | Arrival date, retrieval time, market, commodity, variety and INR/quintal unit |
| eNAM | `https://www.enam.gov.in/web/dashboard/dashboard/live_price` | `OFFICIAL_HTML` | `PARTIAL`; no documented public API was verified, so no screen scraping is used | Link-only capability record |
| PPQS / CIBRC | `https://ppqs.gov.in/divisions/cib-rc/registered-products` | `OFFICIAL_DOCUMENT` / `MANUAL_IMPORT` | `PARTIAL`; runtime validation fails closed unless a controlled current official-label import exists | Product/crop/target, registration status, validity and exact source document required |
| Maharashtra Agriculture Department | `https://krishi.maharashtra.gov.in/` | `OFFICIAL_HTML` / `OFFICIAL_DOCUMENT` | `PARTIAL`; official content is discoverable but no stable public API is verified | Controlled document ingestion only |
| Soil Health Card | `https://soilhealth.dac.gov.in/files/SHC_API_Integration_Guidelines.pdf` | `LIVE_API` | `BLOCKED`; the official guidance requires registered authenticated access | No farmer record is fetched without authorized integration and ownership checks |

Authentication, timeout, schema, content-type, redirect, host allow-list and size failures return explicit `LIVE_DATA_UNAVAILABLE`/503 responses. No mirror or LLM estimate substitutes for an official value. Pesticide dose, concentration, waiting period or frequency is never emitted without a matching current official label record for the product, crop and target.
