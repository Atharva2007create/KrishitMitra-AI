from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import SourceAccessMode


class SourceProvenance(BaseModel):
    source_name: str
    organization: str
    source_url: str
    access_mode: SourceAccessMode
    retrieved_at: datetime
    data_timestamp: datetime | None = None
    freshness_seconds: int | None = None


class WeatherObservation(BaseModel):
    station_id: str | None = None
    station_name: str
    district: str | None = None
    state: str | None = None
    observed_at: datetime
    temperature_c: Decimal | None = None
    relative_humidity_percent: Decimal | None = None
    rainfall_24h_mm: Decimal | None = None
    wind_speed_kmph: Decimal | None = None
    weather_code: str | None = None
    provenance: SourceProvenance


class WeatherForecast(BaseModel):
    location_name: str
    forecast_date: datetime
    minimum_temperature_c: Decimal | None = None
    maximum_temperature_c: Decimal | None = None
    summary: str | None = None
    warning: str | None = None
    provenance: SourceProvenance


class MarketPriceRecord(BaseModel):
    state: str
    district: str
    market: str
    commodity: str
    variety: str | None = None
    arrival_date: datetime
    minimum_price: Decimal | None = None
    maximum_price: Decimal | None = None
    modal_price: Decimal | None = None
    unit: str = "INR/quintal"
    provenance: SourceProvenance


class PesticideRegulatoryRecord(BaseModel):
    product_name: str
    active_ingredient: str | None = None
    crop: str
    target: str | None = None
    registration_status: str
    label_claim: str | None = None
    dose: str | None = None
    waiting_period: str | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    provenance: SourceProvenance


class RegionalAdvisory(BaseModel):
    title: str
    state: str
    district: str | None = None
    crop: str | None = None
    advisory_text: str
    published_at: datetime | None = None
    provenance: SourceProvenance


class SoilHealthRecord(BaseModel):
    sample_id: str
    sampled_at: datetime | None = None
    ph: Decimal | None = None
    electrical_conductivity: Decimal | None = None
    organic_carbon: Decimal | None = None
    nutrients: dict[str, Decimal | str] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)
    provenance: SourceProvenance


class SourceCapability(BaseModel):
    code: str
    name: str
    organization: str
    official_url: str
    access_mode: SourceAccessMode
    status: str
    reason: str
    requires_credentials: bool = False
    last_verified_at: datetime
