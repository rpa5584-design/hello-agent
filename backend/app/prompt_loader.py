"""Load the local hotel-assistant instructions without provider or database access."""

from pathlib import Path


HOTEL_ASSISTANT_PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "hotel-assistant.md"


class PromptConfigurationError(RuntimeError):
    """Required local prompt cannot be loaded."""


def load_hotel_assistant_prompt(path: Path | None = None) -> str:
    prompt_path = path if path is not None else HOTEL_ASSISTANT_PROMPT_PATH
    try:
        text = prompt_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        raise PromptConfigurationError(
            "Cannot load prompts/hotel-assistant.md; ensure the readable UTF-8 prompt file exists."
        ) from None
    if not text.strip():
        raise PromptConfigurationError("prompts/hotel-assistant.md must not be empty.")
    return text
