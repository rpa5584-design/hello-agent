import asyncio

import pytest

from app.main import app, lifespan
from app import prompt_loader


def test_real_prompt_loads_from_project_root(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    text = prompt_loader.load_hotel_assistant_prompt()
    for table in ("saved_hotels", "saved_hotel_zips", "demo_hotel_nights"):
        assert table in text
    for relationship in (
        "saved_hotels.hotel_id = saved_hotel_zips.hotel_id",
        "saved_hotels.hotel_id = demo_hotel_nights.hotel_id",
    ):
        assert relationship in text
    assert prompt_loader.HOTEL_ASSISTANT_PROMPT_PATH.name == "hotel-assistant.md"


def test_startup_loads_prompt_without_database_or_provider(monkeypatch):
    monkeypatch.setattr("app.main.initialize_database", lambda: None)

    async def check():
        async with lifespan(app):
            assert app.state.hotel_assistant_prompt == prompt_loader.load_hotel_assistant_prompt()
    asyncio.run(check())


def test_missing_prompt_fails_startup_before_database(monkeypatch, tmp_path):
    monkeypatch.setattr(prompt_loader, "HOTEL_ASSISTANT_PROMPT_PATH", tmp_path / "missing.md")
    def forbidden_database():
        pytest.fail("Database must not be accessed when prompt loading fails")
    monkeypatch.setattr("app.main.initialize_database", forbidden_database)

    async def check():
        async with lifespan(app):
            pytest.fail("Missing prompt must prevent startup")
    with pytest.raises(prompt_loader.PromptConfigurationError, match="Cannot load prompts/hotel-assistant.md"):
        asyncio.run(check())


def test_empty_prompt_is_configuration_error(tmp_path):
    path = tmp_path / "empty.md"
    path.write_text(" \n", encoding="utf-8")
    with pytest.raises(prompt_loader.PromptConfigurationError, match="must not be empty"):
        prompt_loader.load_hotel_assistant_prompt(path)
