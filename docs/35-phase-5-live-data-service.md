# Phase 5 live agriculture data service

`LiveAgricultureDataService` is the single backend boundary for official live data. It owns source-specific adapters and normalized `WeatherObservation`, `WeatherForecast`, `MarketPriceRecord`, `PesticideRegulatoryRecord`, `RegionalAdvisory`, and `SoilHealthRecord` contracts.

The HTTP boundary accepts HTTPS only, uses an exact official-host allow-list, disables redirects, bounds response size and time, retries only transient failures, verifies JSON content type and rejects schema drift. A short process-local TTL cache reduces repeated official-source requests without hiding source or data timestamps. IMD observations older than `WEATHER_MAX_AGE_SECONDS` (six hours by default) are rejected as `STALE_LIVE_DATA`; AGMARKNET records retain their actual arrival dates and are sorted newest first without being relabelled as today's price.

Phase 5 endpoints:

- `GET /api/v1/live/sources`
- `GET /api/v1/live/weather?state=...&district=...`
- `GET /api/v1/live/markets?state=...&district=...&commodity=...`
- `POST /api/v1/live/regulatory/validate`

All endpoints require an authenticated farmer. Weather and market questions in guided assistance route through this service. A source failure is isolated from RAG and other adapters, persisted as a safe response, and never replaced by an LLM guess.

Runtime credentials are `IMD_API_AUTH_HEADER`/`IMD_API_AUTH_VALUE` and `DATA_GOV_API_KEY`. The IMD header name/value must match the access method issued by its portal; the code does not assume an undocumented bearer format. No credential belongs in Git, database rows, logs, API responses or client bundles.
