# Phase 4 multilingual and safety behavior

English (`en`), Hindi (`hi`), and Marathi (`mr`) are supported for category metadata, FAQ content, safe fallback messages, and personalized answers. Explicit request language wins; otherwise the farmer profile preference and then session language are used. Citations always point to the original official source.

Deterministic gates run before retrieval/generation:

| Request | Status |
|---|---|
| Current weather or market value | `REQUIRES_LIVE_DATA` |
| Exact pesticide dosage/concentration/waiting interval | `REQUIRES_REGULATORY_VALIDATION` |
| Photo/camera analysis request | `REQUIRES_IMAGE_ANALYSIS` |
| Unsupported crop or missing official evidence | `INSUFFICIENT` |

Prompt-injection markers are recorded as a safety flag and never change the grounding policy. Complete-word matching prevents `rice` from matching the word `price`. Personalized generation has a per-user in-memory prototype rate limit and a 2,000-character configured maximum.
