"""Thin adapters for SQL proposals and checked two-stage hotel answers."""

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from app.models import RagAnswerRequest, RagAnswerResponse, ConversationId, RagQuestion, SqlProposalResponse
from app.controllers import conversation_history
from app.prompt_loader import PromptConfigurationError
from app.controllers.rag_retrieval import RetrievalError
from app.services import openrouter, rag_answer, rag_stage1
from app.services.sql_validation import SqlValidationError

router = APIRouter(prefix="/api/rag", tags=["rag"])


@router.post("/answer", response_model=RagAnswerResponse)
def answer(body: RagAnswerRequest, request: Request):
    conversation_id = body.conversation_id or str(uuid4())
    prompt = getattr(request.app.state, "hotel_assistant_prompt", None)
    try:
        return rag_answer.answer_question(body.question, prompt, conversation_id)
    except SqlValidationError:
        status, message = 422, "Model proposal was rejected by backend SQL validation."
    except RetrievalError:
        status, message = 503, "Read-only hotel retrieval failed. Please retry later."
    except openrouter.ChatConfigurationError:
        status, message = 503, "Model configuration is missing."
    except openrouter.ChatProviderError:
        status, message = 502, "Model service is unavailable or returned an invalid response."
    except PromptConfigurationError:
        status, message = 503, "Hotel assistant prompt is not loaded."
    except conversation_history.HistoryError:
        status, message = 503, "Conversation history is unavailable; the RAG request could not be completed."
    except Exception:
        status, message = 500, "RAG request failed."
    return JSONResponse(status_code=status, content={"detail": message, "conversation_id": conversation_id})


@router.get("/conversations/{conversation_id}")
def history(conversation_id: ConversationId, after_message_id: int = Query(0, ge=0)):
    try:
        messages = conversation_history.load(conversation_id, after_message_id)
    except conversation_history.HistoryError:
        raise HTTPException(503, "Conversation history is unavailable.") from None
    return {"conversation_id": conversation_id, "messages": messages,
            "next_after_message_id": messages[-1]["message_id"] if messages else after_message_id}


@router.post("/propose-sql", response_model=SqlProposalResponse)
def propose_sql(body: RagQuestion, request: Request) -> SqlProposalResponse:
    prompt = getattr(request.app.state, "hotel_assistant_prompt", None)
    if not isinstance(prompt, str) or not prompt.strip():
        raise HTTPException(503, "Hotel assistant prompt is not loaded.")
    try:
        proposal = rag_stage1.propose_sql(body.question, prompt)
        return SqlProposalResponse(sql=proposal.sql, tables=list(proposal.tables))
    except SqlValidationError:
        raise HTTPException(422, "Model proposal was rejected by backend SQL validation.") from None
    except openrouter.ChatConfigurationError:
        raise HTTPException(503, "Model configuration is missing.") from None
    except openrouter.ChatProviderError:
        raise HTTPException(502, "Model service is unavailable or returned an invalid response.") from None
