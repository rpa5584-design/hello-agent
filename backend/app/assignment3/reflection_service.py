"""Optional bounded reflection, separate from all exercise and safety controls."""
import asyncio
import logging
import json
from pathlib import Path
from . import conversation_controller as history
from . import reflection_provider as provider
from . import reflection_safety as safety

ERROR_MESSAGE = "That reflection response is unavailable. Your exercise record is unchanged. You can skip this or retry."
logger = logging.getLogger(__name__)


async def reflect(path: Path, session_id: str, reflection: str) -> list[dict]:
    # Before reserve: matched raw text creates no conversation or request records.
    if safety.matches(reflection):
        raise history.ConversationError(400, safety.MESSAGE)
    context, token = history.reserve(path, session_id, reflection)
    if token is None:
        return history.load(path, session_id)
    try:
        answer = provider.checked_answer(await asyncio.wait_for(provider.complete(context), timeout=15))
    except (provider.ProviderError, TimeoutError) as error:
        # No raw exception/body/context: only explicitly sanitized upstream fields.
        if isinstance(error, provider.ProviderError):
            logger.warning("Assignment3 reflection failed reason=%s status=%s finish_reason=%s",
                           error.reason.value, error.status, error.finish_reason)
            if error.diagnostic is not None:
                logger.warning("Assignment3 upstream diagnostic=%s", json.dumps(error.diagnostic, ensure_ascii=True))
        else:
            logger.warning("Assignment3 reflection failed reason=overall_timeout deadline_seconds=15")
        history.finish(path, session_id, token, ERROR_MESSAGE, False)
        raise history.ConversationError(502, ERROR_MESSAGE) from None
    history.finish(path, session_id, token, answer, True)
    return history.load(path, session_id)
