"""Thin adapter for the basic chat wiring checkpoint."""

from fastapi import APIRouter, HTTPException

from app.models import ChatRequest, ChatResponse
from app.services import openrouter

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        return ChatResponse(reply=openrouter.complete_message(request.message))
    except openrouter.ChatConfigurationError:
        raise HTTPException(503, "Chat is not configured. Please contact the demo operator.") from None
    except openrouter.ChatProviderError:
        raise HTTPException(502, "Chat service is unavailable or returned an invalid answer. Please retry later.") from None
