from functools import lru_cache

from app.core.settings import get_settings
from app.integrations.government.service import LiveAgricultureDataService


@lru_cache(maxsize=1)
def get_live_data_service() -> LiveAgricultureDataService:
    return LiveAgricultureDataService(get_settings())


__all__ = ["LiveAgricultureDataService", "get_live_data_service"]
