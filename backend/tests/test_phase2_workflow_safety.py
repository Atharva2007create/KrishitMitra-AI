from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from app.api.v1 import images
from app.core.settings import Settings
from app.models.enums import AttachmentStatus, RecordStatus


class FakeSession:
    def __init__(self) -> None:
        self.commits = 0
        self.refreshes = 0

    async def commit(self) -> None:
        self.commits += 1

    async def refresh(self, _: object) -> None:
        self.refreshes += 1


async def test_stale_image_analysis_reaches_terminal_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analysis = SimpleNamespace(
        created_at=datetime.now(UTC) - timedelta(seconds=31),
        status=RecordStatus.PROCESSING,
        error_code=None,
        processed_at=None,
    )
    attachment = SimpleNamespace(status=AttachmentStatus.PROCESSING)
    session = FakeSession()
    monkeypatch.setattr(
        images,
        "get_settings",
        lambda: Settings(app_env="test", image_analysis_timeout_seconds=30),
    )

    result = await images._timeout_if_stale(  # type: ignore[arg-type]
        analysis, attachment, session
    )

    assert result.status == RecordStatus.FAILED
    assert result.error_code == "ANALYSIS_TIMEOUT"
    assert attachment.status == AttachmentStatus.FAILED
    assert session.commits == 1
    assert session.refreshes == 1
