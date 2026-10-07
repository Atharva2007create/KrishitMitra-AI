from enum import StrEnum


class UserRole(StrEnum):
    FARMER = "FARMER"
    ADMIN = "ADMIN"


class Language(StrEnum):
    EN = "en"
    HI = "hi"
    MR = "mr"


class AreaUnit(StrEnum):
    ACRE = "ACRE"
    HECTARE = "HECTARE"
    GUNTHA = "GUNTHA"


class CropCycleStatus(StrEnum):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    HARVESTED = "HARVESTED"
    CANCELLED = "CANCELLED"


class SenderType(StrEnum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"


class TrustStatus(StrEnum):
    APPROVED = "APPROVED"
    PENDING = "PENDING"
    DISABLED = "DISABLED"


class RecordStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
