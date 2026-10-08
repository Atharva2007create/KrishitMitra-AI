from datetime import UTC, datetime

from app.integrations.government.http import GovernmentSourceError
from app.integrations.government.models import PesticideRegulatoryRecord


class PesticideRegulatoryAdapter:
    """Validated imported records only; official PDFs are never treated as a live API."""

    def __init__(self, records: tuple[PesticideRegulatoryRecord, ...] = ()) -> None:
        self.records = records

    async def validate(
        self, product_name: str, crop: str = "PIGEONPEA", target: str | None = None
    ) -> list[PesticideRegulatoryRecord]:
        now = datetime.now(UTC)
        matches = [
            record
            for record in self.records
            if product_name.casefold() in record.product_name.casefold()
            and crop.casefold() in record.crop.casefold()
            and (
                target is None
                or not record.target
                or target.casefold() in record.target.casefold()
            )
            and (record.valid_from is None or record.valid_from <= now)
            and (record.valid_until is None or record.valid_until >= now)
        ]
        if not matches:
            raise GovernmentSourceError(
                "REGULATORY_VALIDATION_UNAVAILABLE",
                "No current imported official label record matches this product and crop",
            )
        return matches
