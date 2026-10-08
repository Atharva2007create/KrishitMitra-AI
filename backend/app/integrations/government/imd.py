from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from app.integrations.government.http import GovernmentSourceError, SafeGovernmentHttpClient
from app.integrations.government.models import SourceProvenance, WeatherObservation
from app.models.enums import SourceAccessMode


def _decimal(value: Any) -> Decimal | None:
    try:
        return Decimal(str(value)) if value not in (None, "", "NA", "N/A") else None
    except InvalidOperation:
        return None


def _observed_at(row: dict[str, Any]) -> datetime:
    raw_date = row.get("DATE") or row.get("Date of Observation") or row.get("date")
    raw_time = row.get("TIME") or row.get("Time of Observation") or "00:00:00"
    if raw_date:
        for value in (f"{raw_date}T{raw_time}", str(raw_date)):
            try:
                parsed = datetime.fromisoformat(value)
                return parsed.replace(tzinfo=parsed.tzinfo or UTC)
            except ValueError:
                continue
    return datetime.now(UTC)


class ImdWeatherAdapter:
    source_url = "https://api.imd.gov.in/public/api_reference.html"

    def __init__(
        self,
        client: SafeGovernmentHttpClient,
        base_url: str,
        auth_header: str,
        auth_value: str,
    ) -> None:
        self.client = client
        self.base_url = base_url.rstrip("/")
        if auth_header not in {"Authorization", "X-API-Key", "api-key"}:
            raise ValueError("Unsupported IMD authentication header")
        self.auth_header = auth_header
        self.auth_value = auth_value

    async def observations(self, state: str, district: str) -> list[WeatherObservation]:
        if not self.auth_value:
            raise GovernmentSourceError(
                "SOURCE_AUTHENTICATION_REQUIRED",
                "IMD API portal credentials are not configured",
            )
        payload = await self.client.get_json(
            f"{self.base_url}/aws_data",
            headers={self.auth_header: self.auth_value},
        )
        rows = payload.get("data", payload) if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            raise GovernmentSourceError("SOURCE_SCHEMA_INVALID", "IMD response schema changed")
        now = datetime.now(UTC)
        records: list[WeatherObservation] = []
        for value in rows:
            if not isinstance(value, dict):
                continue
            row = {str(key): item for key, item in value.items()}
            row_state = str(row.get("STATE") or row.get("State") or "")
            row_district = str(row.get("DISTRICT") or row.get("District") or "")
            if state.casefold() not in row_state.casefold():
                continue
            if district.casefold() not in row_district.casefold():
                continue
            observed_at = _observed_at(row)
            records.append(
                WeatherObservation(
                    station_id=str(row.get("ID") or row.get("Station Id") or "") or None,
                    station_name=str(row.get("STATION") or row.get("Station") or district),
                    district=row_district or district,
                    state=row_state or state,
                    observed_at=observed_at,
                    temperature_c=_decimal(row.get("CURR_TEMP") or row.get("Temperature")),
                    relative_humidity_percent=_decimal(row.get("RH") or row.get("Humidity")),
                    rainfall_24h_mm=_decimal(
                        row.get("Last 24 hrs Rainfall") or row.get("RAINFALL")
                    ),
                    wind_speed_kmph=_decimal(row.get("WIND_SPEED") or row.get("Wind Speed")),
                    weather_code=str(row.get("WEATHER_CODE") or "") or None,
                    provenance=SourceProvenance(
                        source_name="IMD AWS/ARG Data",
                        organization="India Meteorological Department",
                        source_url=self.source_url,
                        access_mode=SourceAccessMode.LIVE_API,
                        retrieved_at=now,
                        data_timestamp=observed_at,
                        freshness_seconds=max(0, int((now - observed_at).total_seconds())),
                    ),
                )
            )
        if not records:
            raise GovernmentSourceError(
                "LIVE_DATA_UNAVAILABLE", "IMD returned no matching district observations"
            )
        return records
