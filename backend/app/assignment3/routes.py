"""Thin Assignment 3 session and optional reflection routes."""
import sqlite3
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, Request
from . import controller, conversation_controller, reflection_service
from .models import Session, SessionStart, SessionEnd, ReflectionRequest, ConversationMessage
from . import reflection_safety

router = APIRouter(prefix="/api/assignment3", tags=["assignment3"])


def storage(operation, *args):
    try:
        return operation(*args)
    except sqlite3.Error:
        raise HTTPException(503, "Session storage is unavailable.") from None
    except controller.ConflictError:
        raise HTTPException(409, "Session update conflicts with the saved record.") from None
    except conversation_controller.ConversationError as error:
        raise HTTPException(error.status, error.message) from None


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "application": "assignment3"}


@router.post("/sessions", response_model=Session)
def start_session(body: SessionStart, request: Request) -> dict:
    return storage(controller.create, request.app.state.database_path, body)


@router.get("/sessions", response_model=list[Session])
def history(request: Request, limit: int = Query(100, ge=1, le=100), offset: int = Query(0, ge=0)) -> list[dict]:
    return storage(controller.list_sessions, request.app.state.database_path, limit, offset)


@router.get("/sessions/{session_id}", response_model=Session)
def session(session_id: UUID, request: Request) -> dict:
    result = storage(controller.get, request.app.state.database_path, session_id)
    if result is None:
        raise HTTPException(404, "Session not found.")
    return result


@router.patch("/sessions/{session_id}", response_model=Session)
def end_session(session_id: UUID, body: SessionEnd, request: Request) -> dict:
    result = storage(controller.finish, request.app.state.database_path, session_id, body)
    if result is None:
        raise HTTPException(404, "Session not found.")
    return result


@router.get("/sessions/{session_id}/conversation", response_model=list[ConversationMessage])
def conversation(session_id: UUID, request: Request) -> list[dict]:
    return storage(conversation_controller.load, request.app.state.database_path, str(session_id))


@router.post("/sessions/{session_id}/reflection", response_model=list[ConversationMessage])
async def reflection(session_id: UUID, body: ReflectionRequest, request: Request) -> list[dict]:
    try:
        return await reflection_service.reflect(request.app.state.database_path, str(session_id), body.reflection)
    except conversation_controller.ConversationError as error:
        if error.status == 400 and error.message == reflection_safety.MESSAGE:
            raise HTTPException(400, {"code": reflection_safety.CODE, "message": reflection_safety.MESSAGE}) from None
        raise HTTPException(error.status, error.message) from None
    except sqlite3.Error:
        raise HTTPException(503, "Reflection storage is unavailable. Reload Saved History before retrying.") from None
