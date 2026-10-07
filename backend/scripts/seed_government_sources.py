import asyncio

from sqlalchemy import select

from app.db.connection import SessionFactory
from app.models.entities import GovernmentSource
from app.models.enums import TrustStatus

SOURCES = [
    ("ICAR / ICAR-IIPR", "Indian Council of Agricultural Research"),
    ("IMD", "India Meteorological Department"),
    ("AGMARKNET / eNAM", "Government agricultural market information services"),
    ("Government Pesticide Regulatory Source", "Government of India"),
    ("Maharashtra Agriculture Department", "Government of Maharashtra"),
    ("Soil Health Card", "Government of India"),
]


async def main() -> None:
    async with SessionFactory() as session:
        for name, organization in SOURCES:
            if await session.scalar(
                select(GovernmentSource.id).where(GovernmentSource.name == name)
            ):
                continue
            session.add(
                GovernmentSource(
                    name=name,
                    organization=organization,
                    source_type="OFFICIAL_GOVERNMENT_SOURCE",
                    trust_status=TrustStatus.APPROVED,
                    is_active=True,
                )
            )
        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())
