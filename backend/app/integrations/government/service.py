from datetime import UTC, datetime, timedelta
from typing import cast

from app.core.settings import Settings
from app.integrations.government.http import GovernmentSourceError, SafeGovernmentHttpClient
from app.integrations.government.imd import ImdWeatherAdapter
from app.integrations.government.market import AgmarknetMarketAdapter
from app.integrations.government.models import (
    MarketPriceRecord,
    PesticideRegulatoryRecord,
    SourceCapability,
    WeatherObservation,
)
from app.integrations.government.regulatory import PesticideRegulatoryAdapter
from app.models.enums import SourceAccessMode


class LiveAgricultureDataService:
    def __init__(
        self,
        settings: Settings,
        regulatory_records: tuple[PesticideRegulatoryRecord, ...] = (),
    ) -> None:
        client = SafeGovernmentHttpClient(
            {"api.imd.gov.in", "api.data.gov.in"},
            settings.government_http_timeout_seconds,
            settings.government_http_max_retries,
            settings.government_http_max_response_bytes,
        )
        self.weather_adapter = ImdWeatherAdapter(
            client,
            settings.imd_api_base_url,
            settings.imd_api_auth_header,
            settings.imd_api_auth_value,
        )
        self.market_adapter = AgmarknetMarketAdapter(
            client,
            settings.data_gov_api_base_url,
            settings.agmarknet_resource_id,
            settings.data_gov_api_key,
        )
        self.regulatory_adapter = PesticideRegulatoryAdapter(regulatory_records)
        self.settings = settings
        self._cache: dict[str, tuple[datetime, object]] = {}

    def _cached(self, key: str) -> object | None:
        item = self._cache.get(key)
        if item is None:
            return None
        created_at, value = item
        if datetime.now(UTC) - created_at > timedelta(
            seconds=self.settings.live_data_cache_seconds
        ):
            self._cache.pop(key, None)
            return None
        return value

    def _remember(self, key: str, value: object) -> None:
        self._cache[key] = (datetime.now(UTC), value)

    async def weather(self, state: str, district: str) -> list[WeatherObservation]:
        key = f"weather:{state.casefold()}:{district.casefold()}"
        cached = self._cached(key)
        if cached is not None:
            return cast(list[WeatherObservation], cached)
        value = await self.weather_adapter.observations(state, district)
        fresh = [
            item
            for item in value
            if item.provenance.freshness_seconds is not None
            and item.provenance.freshness_seconds <= self.settings.weather_max_age_seconds
        ]
        if not fresh:
            raise GovernmentSourceError(
                "STALE_LIVE_DATA",
                "IMD returned observations older than the configured freshness limit",
            )
        fresh.sort(key=lambda item: item.observed_at, reverse=True)
        self._remember(key, fresh)
        return fresh

    async def market_prices(
        self,
        state: str,
        district: str | None = None,
        market: str | None = None,
        commodity: str = "Pigeon Pea (Arhar Fali)",
    ) -> list[MarketPriceRecord]:
        key = ":".join(
            (
                "market",
                state.casefold(),
                (district or "").casefold(),
                (market or "").casefold(),
                commodity.casefold(),
            )
        )
        cached = self._cached(key)
        if cached is not None:
            return cast(list[MarketPriceRecord], cached)
        value = await self.market_adapter.prices(state, district, market, commodity)
        value.sort(key=lambda item: item.arrival_date, reverse=True)
        self._remember(key, value)
        return value

    async def validate_pesticide(
        self, product_name: str, crop: str = "PIGEONPEA", target: str | None = None
    ) -> list[PesticideRegulatoryRecord]:
        return await self.regulatory_adapter.validate(product_name, crop, target)

    def capabilities(self) -> list[SourceCapability]:
        now = datetime.now(UTC)
        return [
            SourceCapability(
                code="IMD",
                name="IMD weather services",
                organization="India Meteorological Department",
                official_url="https://api.imd.gov.in/public/api_reference.html",
                access_mode=SourceAccessMode.LIVE_API,
                status="READY" if self.settings.imd_api_auth_value else "BLOCKED",
                reason=(
                    "Configured official API credential"
                    if self.settings.imd_api_auth_value
                    else "Official endpoint verified; API portal credential required"
                ),
                requires_credentials=True,
                last_verified_at=now,
            ),
            SourceCapability(
                code="AGMARKNET",
                name="AGMARKNET mandi prices via OGD India",
                organization="Directorate of Marketing and Inspection",
                official_url=(
                    "https://www.data.gov.in/resource/"
                    "current-daily-price-various-commodities-various-markets-mandi"
                ),
                access_mode=SourceAccessMode.LIVE_API,
                status="READY" if self.settings.data_gov_api_key else "BLOCKED",
                reason=(
                    "Configured OGD API key"
                    if self.settings.data_gov_api_key
                    else "Official resource verified; OGD API key required"
                ),
                requires_credentials=True,
                last_verified_at=now,
            ),
            SourceCapability(
                code="ENAM",
                name="eNAM live price dashboard",
                organization="Small Farmers Agribusiness Consortium",
                official_url="https://www.enam.gov.in/web/dashboard/dashboard/live_price",
                access_mode=SourceAccessMode.OFFICIAL_HTML,
                status="PARTIAL",
                reason="Official dashboard verified; no documented public backend API",
                last_verified_at=now,
            ),
            SourceCapability(
                code="PPQS_CIBRC",
                name="Registered pesticide products",
                organization="Directorate of Plant Protection, Quarantine & Storage",
                official_url="https://ppqs.gov.in/divisions/cib-rc/registered-products",
                access_mode=SourceAccessMode.OFFICIAL_DOCUMENT,
                status="PARTIAL",
                reason="Official registers are documents and require controlled validated import",
                last_verified_at=now,
            ),
            SourceCapability(
                code="MAHARASHTRA_AGRICULTURE",
                name="Maharashtra Agriculture advisories",
                organization="Maharashtra Department of Agriculture",
                official_url="https://krishi.maharashtra.gov.in/",
                access_mode=SourceAccessMode.OFFICIAL_HTML,
                status="PARTIAL",
                reason="Official pages are available; no stable documented public API verified",
                last_verified_at=now,
            ),
            SourceCapability(
                code="SOIL_HEALTH_CARD",
                name="Soil Health Card",
                organization="Department of Agriculture and Farmers Welfare",
                official_url=(
                    "https://soilhealth.dac.gov.in/files/SHC_API_Integration_Guidelines.pdf"
                ),
                access_mode=SourceAccessMode.LIVE_API,
                status="BLOCKED",
                reason="Official API guidance requires registered authenticated integration",
                requires_credentials=True,
                last_verified_at=now,
            ),
        ]
