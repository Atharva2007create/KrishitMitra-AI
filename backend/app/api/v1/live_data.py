from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.settings import get_settings
from app.integrations.government import LiveAgricultureDataService
from app.integrations.government.http import GovernmentSourceError
from app.schemas.live_data import (
    MarketPriceResponse,
    RegulatoryValidationRequest,
    RegulatoryValidationResponse,
    SourceCapabilityResponse,
    WeatherResponse,
)
from app.security.dependencies import FarmerUser

router = APIRouter(prefix="/live", tags=["official live agriculture data"])


def get_live_data_service() -> LiveAgricultureDataService:
    return LiveAgricultureDataService(get_settings())


LiveData = Annotated[LiveAgricultureDataService, Depends(get_live_data_service)]


def _unavailable(exc: GovernmentSourceError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={"code": exc.code, "message": str(exc)},
    )


@router.get("/sources", response_model=SourceCapabilityResponse)
async def source_capabilities(_: FarmerUser, service: LiveData) -> SourceCapabilityResponse:
    return SourceCapabilityResponse(sources=service.capabilities())


@router.get("/weather", response_model=WeatherResponse)
async def weather(
    _: FarmerUser,
    service: LiveData,
    state_name: Annotated[str, Query(alias="state", min_length=2, max_length=100)],
    district: Annotated[str, Query(min_length=2, max_length=100)],
) -> WeatherResponse:
    try:
        values = await service.weather(state_name, district)
    except GovernmentSourceError as exc:
        raise _unavailable(exc) from exc
    return WeatherResponse(
        status="LIVE",
        state=state_name,
        district=district,
        observations=values,
        retrieved_at=datetime.now(UTC),
    )


@router.get("/markets", response_model=MarketPriceResponse)
async def markets(
    _: FarmerUser,
    service: LiveData,
    state_name: Annotated[str, Query(alias="state", min_length=2, max_length=100)],
    district: Annotated[str | None, Query(max_length=100)] = None,
    market: Annotated[str | None, Query(max_length=160)] = None,
    commodity: Annotated[str, Query(min_length=2, max_length=160)] = "Pigeon Pea (Arhar Fali)",
) -> MarketPriceResponse:
    try:
        values = await service.market_prices(state_name, district, market, commodity)
    except GovernmentSourceError as exc:
        raise _unavailable(exc) from exc
    return MarketPriceResponse(
        status="LIVE", commodity=commodity, prices=values, retrieved_at=datetime.now(UTC)
    )


@router.post("/regulatory/validate", response_model=RegulatoryValidationResponse)
async def validate_regulatory_record(
    payload: RegulatoryValidationRequest, _: FarmerUser, service: LiveData
) -> RegulatoryValidationResponse:
    try:
        values = await service.validate_pesticide(
            payload.product_name, payload.crop, payload.target
        )
    except GovernmentSourceError as exc:
        raise _unavailable(exc) from exc
    return RegulatoryValidationResponse(
        status="VALIDATED",
        records=values,
        validated_at=datetime.now(UTC),
        warning="Follow the current product label and local agricultural authority guidance.",
    )
