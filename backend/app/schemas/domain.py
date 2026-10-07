from datetime import date, datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.models.enums import AreaUnit, CropCycleStatus, Language, SenderType, UserRole

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
Location = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserSummary(ORMModel):
    id: UUID
    role: UserRole
    phone_number: str | None
    email: str | None
    is_active: bool


class MeResponse(UserSummary):
    profile: "FarmerProfileResponse | None" = None


class FarmerProfileFields(BaseModel):
    full_name: Name
    preferred_language: Language
    state: Location
    district: Location
    taluka: Location
    village: Location | None = None


class FarmerProfileCreate(FarmerProfileFields):
    pass


class FarmerProfileUpdate(BaseModel):
    full_name: Name | None = None
    preferred_language: Language | None = None
    state: Location | None = None
    district: Location | None = None
    taluka: Location | None = None
    village: Location | None = None


class FarmerProfileResponse(FarmerProfileFields, ORMModel):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime


class FarmFields(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)] | None = None
    area_value: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    area_unit: AreaUnit
    state: Location
    district: Location
    taluka: Location
    village: Location | None = None
    soil_type: Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)] | None = (
        None
    )
    irrigation_type: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)] | None
    ) = None


class FarmCreate(FarmFields):
    pass


class FarmUpdate(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)] | None = None
    area_value: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=3)
    area_unit: AreaUnit | None = None
    state: Location | None = None
    district: Location | None = None
    taluka: Location | None = None
    village: Location | None = None
    soil_type: Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)] | None = (
        None
    )
    irrigation_type: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)] | None
    ) = None


class FarmResponse(FarmFields, ORMModel):
    id: UUID
    farmer_profile_id: UUID
    created_at: datetime
    updated_at: datetime


class CropCycleFields(BaseModel):
    farm_id: UUID
    crop_name: str = "TUR"
    crop_variety: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)] | None
    ) = None
    sowing_date: date
    expected_harvest_date: date | None = None
    actual_harvest_date: date | None = None
    status: CropCycleStatus = CropCycleStatus.PLANNED
    estimated_crop_stage: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)] | None
    ) = None
    notes: Annotated[str, StringConstraints(strip_whitespace=True, max_length=4000)] | None = None

    @model_validator(mode="after")
    def validate_crop_and_dates(self) -> "CropCycleFields":
        normalized = self.crop_name.strip().upper().replace(" ", "")
        if normalized not in {"TUR", "PIGEONPEA"}:
            raise ValueError("Phase 2 supports only Tur/Pigeonpea")
        self.crop_name = "PIGEONPEA" if normalized.startswith("PIGEON") else "TUR"
        for value in (self.expected_harvest_date, self.actual_harvest_date):
            if value is not None and value < self.sowing_date:
                raise ValueError("Harvest date cannot precede sowing date")
        if self.status == CropCycleStatus.HARVESTED and self.actual_harvest_date is None:
            raise ValueError("HARVESTED requires actual_harvest_date")
        return self


class CropCycleCreate(CropCycleFields):
    pass


class CropCycleUpdate(BaseModel):
    crop_variety: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)] | None
    ) = None
    expected_harvest_date: date | None = None
    actual_harvest_date: date | None = None
    status: CropCycleStatus | None = None
    estimated_crop_stage: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)] | None
    ) = None
    notes: Annotated[str, StringConstraints(strip_whitespace=True, max_length=4000)] | None = None


class CropCycleResponse(CropCycleFields, ORMModel):
    id: UUID
    created_at: datetime
    updated_at: datetime


class ChatSessionCreate(BaseModel):
    crop_cycle_id: UUID | None = None
    title: Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)] | None = None
    language: Language = Language.EN


class ChatSessionUpdate(BaseModel):
    title: Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)] | None = None
    language: Language | None = None
    is_archived: bool | None = None


class ChatSessionResponse(ChatSessionCreate, ORMModel):
    id: UUID
    user_id: UUID
    last_message_at: datetime | None
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class MessageCreate(BaseModel):
    content: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=8000)]


class MessageResponse(ORMModel):
    id: UUID
    chat_session_id: UUID
    sender_type: SenderType
    content: str
    created_at: datetime


class FeedbackCreate(BaseModel):
    message_id: UUID | None = None
    image_analysis_id: UUID | None = None
    rating: int | None = Field(default=None, ge=1, le=5)
    is_helpful: bool | None = None
    comment: Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)] | None = None

    @model_validator(mode="after")
    def require_content(self) -> "FeedbackCreate":
        if not any((self.message_id, self.image_analysis_id, self.comment)):
            raise ValueError("Feedback requires a target or comment")
        return self


class FeedbackResponse(FeedbackCreate, ORMModel):
    id: UUID
    user_id: UUID
    created_at: datetime


class GovernmentSourceResponse(ORMModel):
    id: UUID
    name: str
    organization: str
    base_url: str | None
    source_type: str
    is_active: bool
    trust_status: str


class AdminHealthResponse(BaseModel):
    status: str
    role: UserRole


MeResponse.model_rebuild()
