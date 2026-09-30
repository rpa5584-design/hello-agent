"""Backend configuration loaded once when the process starts."""

import os
from pathlib import Path

from dotenv import load_dotenv


ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=ENV_PATH, encoding="utf-8-sig")


def geoapify_key_is_configured() -> bool:
    return get_geoapify_api_key() is not None


def get_geoapify_api_key() -> str | None:
    """Return the backend-only credential, or None when not configured."""
    return os.getenv("GEOAPIFY_API_KEY", "").strip() or None
