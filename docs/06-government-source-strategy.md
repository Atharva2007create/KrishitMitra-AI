# Government source strategy

No source or API is integrated in Phase 0. The classifications below are **proposed**, may be multiple per group, and require authoritative verification before Phase 5. No endpoint is invented.

| Source group | Intended purpose | Proposed integration classification | Verification required |
|---|---|---|---|
| ICAR / ICAR-IIPR | Tur varieties, soil, sowing, treatment, water/drainage, nutrients, pests/diseases, harvest/post-harvest | Official document ingestion; downloadable structured data if officially offered; periodic ingestion | Canonical publications, reuse terms, document versions, update cadence, languages, geographic applicability, and machine-readable availability |
| IMD | Forecasts, observations, agrometeorological advisories | Live API candidate plus periodic advisory/document ingestion | Official access method, credentials/terms, spatial coverage, timestamps, rate limits, attribution, forecast freshness, and redistribution rights |
| AGMARKNET / eNAM | Tur mandi arrivals/prices and market context | Live API candidate or downloadable structured data; periodic ingestion fallback | Official access/export mechanism, field definitions, commodity/variety codes, mandi identifiers, update cadence, missing/corrected records, licensing/attribution |
| Government pesticide regulatory source (e.g. applicable PPQS/CIBRC material) | Registration status, approved crop/pest use, dose/rate, waiting/safety information | Official document ingestion and periodic ingestion; manual/authorized integration verification | Authoritative current register, amendment/supersession handling, exact legal applicability, labels, dates, crop/pest combinations, reuse terms; human safety review |
| Maharashtra Agriculture Department | State/district advisories and regional cultivation context | Official document ingestion and periodic ingestion; live feed only if officially supported | Canonical portal/publications, Marathi/English formats, district metadata, update cadence, archive/version access, attribution/reuse terms |
| Soil Health Card system | Farmer-authorized soil/nutrient context and general official recommendations where available | Requires manual/authorized integration verification; official documents for general guidance | Whether programmatic farmer-level access exists, consent/identity requirements, permitted fields/use, privacy/security obligations, availability, and terms |

## Source onboarding gate

Before a source is enabled, record owner/organization, canonical reference, integration method, authorization and reuse terms, expected schema/format, freshness SLA, geographic/crop scope, validation method, failure behavior, attribution, and an accountable reviewer. A failed or stale feed must display its timestamp and must not be silently presented as current.

## Routing

- ICAR/IIPR is the primary cultivation corpus.
- IMD is the weather route.
- AGMARKNET/eNAM is the market route.
- Pesticide requests require both cultivation context and current applicable regulatory evidence.
- Maharashtra requests add state evidence.
- Soil/fertilizer personalization uses authorized Soil Health Card context where possible plus ICAR guidance.

When sources conflict, the response must expose the conflict, dates, and applicability rather than blending them into false certainty. Regulatory/current official evidence takes precedence within its legal scope; escalation rules are finalized with domain reviewers.
