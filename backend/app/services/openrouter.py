"""Basic chat transport only; no database access or retrieval."""

import httpx

from app.config import get_openrouter_api_key, get_openrouter_model


class ChatConfigurationError(RuntimeError):
    """Required backend configuration is absent."""


class ChatProviderError(RuntimeError):
    """Provider failed to return usable assistant text."""


def complete_message(message: str) -> str:
    return complete_messages([{"role": "user", "content": message}])


def complete_messages(messages: list[dict[str, str]]) -> str:
    key, model = get_openrouter_api_key(), get_openrouter_model()
    if not key or not model:
        raise ChatConfigurationError("Chat is not configured.")
    request = httpx.Request(
        "POST", "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": model, "messages": messages},
        extensions={"timeout": httpx.Timeout(30.0).as_dict()},
    )
    try:
        # No redirects or retries; never log provider bodies or headers.
        with httpx.HTTPTransport(retries=0) as transport:
            response = transport.handle_request(request)
            try:
                response.read()
                if not 200 <= response.status_code < 300:
                    raise ChatProviderError("Chat service is unavailable. Please retry later.")
                payload = response.json()
            finally:
                response.close()
        answer = payload["choices"][0]["message"]
        text = answer["content"]
        if answer.get("role") != "assistant" or not isinstance(text, str) or not text.strip() or key in text:
            raise ValueError("Invalid assistant text")
        return text.strip()
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError, AttributeError):
        raise ChatProviderError("Chat service returned no usable answer. Please retry later.") from None
