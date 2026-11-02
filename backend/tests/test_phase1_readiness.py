from contextlib import AbstractAsyncContextManager

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app import main as main_module
from app.api.v1 import router as router_module
from app.db import connection


class FakeConnection:
    async def scalar(self, _: object) -> int:
        return 1


class ConnectionContext(AbstractAsyncContextManager[FakeConnection]):
    async def __aenter__(self) -> FakeConnection:
        return FakeConnection()

    async def __aexit__(self, *args: object) -> None:
        return None


class FakeEngine:
    def __init__(self) -> None:
        self.connect_count = 0

    def connect(self) -> ConnectionContext:
        self.connect_count += 1
        return ConnectionContext()


class FailingContext(AbstractAsyncContextManager[FakeConnection]):
    async def __aenter__(self) -> FakeConnection:
        raise SQLAlchemyError("database unavailable")

    async def __aexit__(self, *args: object) -> None:
        return None


class FailingEngine:
    def connect(self) -> FailingContext:
        return FailingContext()


async def test_database_check_uses_a_fresh_connection_each_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = FakeEngine()
    monkeypatch.setattr(connection, "engine", engine)

    assert await connection.check_database() is True
    assert await connection.check_database() is True
    assert engine.connect_count == 2


async def test_database_check_returns_false_when_connection_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(connection, "engine", FailingEngine())
    assert await connection.check_database() is False


async def test_readiness_returns_503_when_database_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def unavailable() -> bool:
        return False

    monkeypatch.setattr(router_module, "check_database", unavailable)
    with pytest.raises(HTTPException) as raised:
        await router_module.readiness()
    assert raised.value.status_code == 503


async def test_application_shutdown_disposes_database_pool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class DisposableEngine:
        disposed = False

        async def dispose(self) -> None:
            self.disposed = True

    engine = DisposableEngine()
    monkeypatch.setattr(main_module, "engine", engine)

    async with main_module.lifespan(main_module.app):
        assert engine.disposed is False

    assert engine.disposed is True
