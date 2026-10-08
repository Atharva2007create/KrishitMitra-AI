from datetime import datetime

from pydantic import BaseModel, Field

from app.integrations.government.models import (
    MarketPriceRecord,
    PesticideRegulatoryRecord,
    SourceCapability,
    WeatherObservation,
)


class WeatherResponse(BaseModel):
    status: str
    state: str
    district: str
    observations: list[WeatherObservation]
    retrieved_at: datetime


class MarketPriceResponse(BaseModel):
    status: str
    commodity: str
    prices: list[MarketPriceRecord]
    retrieved_at: datetime


class RegulatoryValidationRequest(BaseModel):
    product_name: str = Field(min_length=2, max_length=200)
    crop: str = Field(default="PIGEONPEA", min_length=2, max_length=80)
    target: str | None = Field(default=None, max_length=160)


class RegulatoryValidationResponse(BaseModel):
    status: str
    records: list[PesticideRegulatoryRecord]
    validated_at: datetime
    warning: str


class SourceCapabilityResponse(BaseModel):
    sources: list[SourceCapability]
