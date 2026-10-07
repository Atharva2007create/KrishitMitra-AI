from app.core.settings import Settings


def test_cors_origins_are_parsed() -> None:
    settings = Settings(cors_allowed_origins="http://localhost:3000, http://127.0.0.1:3000")
    assert settings.cors_origins == ["http://localhost:3000", "http://127.0.0.1:3000"]
