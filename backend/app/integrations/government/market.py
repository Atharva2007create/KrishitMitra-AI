from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from app.integrations.government.http import GovernmentSourceError, SafeGovernmentHttpClient
from app.integrations.government.models import MarketPriceRecord, SourceProvenance
from app.models.enums import SourceAccessMode


def _money(value: Any) -> Decimal | None:
    try:
        return Decimal(str(value)) if value not in (None, "", "NA") else None
    except InvalidOperation:
        return None


class AgmarknetMarketAdapter:
    catalog_url = (
        "https://www.data.gov.in/resource/"
        "current-daily-price-various-commodities-various-markets-mandi"
    )

    def __init__(
        self,
        client: SafeGovernmentHttpClient,
        base_url: str,
        resource_id: str,
        api_key: str,
    ) -> None:
        self.client = client
        self.base_url = base_url.rstrip("/")
        self.resource_id = resource_id
        self.api_key = api_key

    async def prices(
        self, state: str, district: str | None, market: str | None, commodity: str
    ) -> list[MarketPriceRecord]:
        if not self.api_key:
            raise GovernmentSourceError(
                "SOURCE_AUTHENTICATION_REQUIRED",
                "data.gov.in API key is not configured",
            )
        params = {
            "api-key": self.api_key,
            "format": "json",
            "limit": "100",
            "filters[state]": state,
            "filters[commodity]": commodity,
        }
        if district:
            params["filters[district]"] = district
        if market:
            params["filters[market]"] = market
        payload = await self.client.get_json(
            f"{self.base_url}/{self.resource_id}", params=params
        )
        rows = payload.get("records", []) if isinstance(payload, dict) else []
        if not isinstance(rows, list):
            raise GovernmentSourceError("SOURCE_SCHEMA_INVALID", "OGD response schema changed")
        now = datetime.now(UTC)
        result: list[MarketPriceRecord] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            raw_date = str(row.get("arrival_date") or row.get("Arrival_Date") or "")
            parsed_date: datetime | None = None
            for pattern in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
                try:
                    parsed_date = datetime.strptime(raw_date, pattern).replace(tzinfo=UTC)
                    break
                except ValueError:
                    continue
            if parsed_date is None:
                continue
            result.append(
                MarketPriceRecord(
                    state=str(row.get("state") or row.get("State") or state),
                    district=str(row.get("district") or row.get("District") or district or ""),
                    market=str(row.get("market") or row.get("Market") or market or ""),
                    commodity=str(row.get("commodity") or row.get("Commodity") or commodity),
                    variety=str(row.get("variety") or row.get("Variety") or "") or None,
                    arrival_date=parsed_date,
                    minimum_price=_money(row.get("min_price") or row.get("Min_Price")),
                    maximum_price=_money(row.get("max_price") or row.get("Max_Price")),
                    modal_price=_money(row.get("modal_price") or row.get("Modal_Price")),
                    provenance=SourceProvenance(
                        source_name="AGMARKNET daily mandi prices",
                        organization="Directorate of Marketing and Inspection",
                        source_url=self.catalog_url,
                        access_mode=SourceAccessMode.LIVE_API,
                        retrieved_at=now,
                        data_timestamp=parsed_date,
                        freshness_seconds=max(0, int((now - parsed_date).total_seconds())),
                    ),
                )
            )
        if not result:
            raise GovernmentSourceError(
                "LIVE_DATA_UNAVAILABLE", "AGMARKNET returned no matching market records"
            )
        return result
