"""Local phrase gate for fictional coursework input, not a risk assessment."""
import re
import unicodedata

MESSAGE = "This reflection will not be sent to the model. You can open Crisis Support using the always-available Crisis Support button."
CODE = "reflection_support"
PHRASES = (
    "kill myself", "end my life", "take my own life", "hurt myself",
    "harm myself", "suicide", "suicidal", "self harm", "selfharm",
    "kill yourself", "end their life", "kill themselves", "hurt themselves",
)


def matches(text: str) -> bool:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    words = re.sub(r"[^\w]+|_+", " ", normalized)
    words = " " + " ".join(words.split()) + " "
    return any(" " + phrase + " " in words for phrase in PHRASES)
