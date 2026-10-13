from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse
from app.config import settings
from app.schemas.ask import AskCompareResponse, AskRequest, AskResponse
from app.services.openai_config import validate_openai_key
from app.services.rag_service import (
    call_rag,
    call_rag_advisory,
    call_rag_compare,
    stream_rag,
    stream_rag_advisory,
)
from app.routers.history import add_to_history

router = APIRouter()


def _visitor_key(request: AskRequest, x_openai_key: Optional[str]) -> Optional[str]:
    """
    The visitor's own OpenAI key, or None for a demo session.

    There is no server-side key: without a key the only option is the demo.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    if settings.use_mock or request.demo:
        return None
    if not x_openai_key:
        raise HTTPException(
            status_code=401,
            detail="Add your OpenAI API key in TerraMind, or start a demo session.",
        )
    try:
        return validate_openai_key(x_openai_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest, x_openai_key: Optional[str] = Header(default=None)):
    api_key = _visitor_key(request, x_openai_key)
    response = await call_rag(request, api_key)
    add_to_history(request.question, response)
    return response


@router.post("/ask/stream")
async def ask_stream(request: AskRequest, x_openai_key: Optional[str] = Header(default=None)):
    api_key = _visitor_key(request, x_openai_key)
    return StreamingResponse(
        stream_rag(request, api_key),
        media_type="application/x-ndjson",
    )


@router.post("/ask/advisory", response_model=AskResponse)
async def ask_advisory(request: AskRequest, x_openai_key: Optional[str] = Header(default=None)):
    api_key = _visitor_key(request, x_openai_key)
    response = await call_rag_advisory(request, api_key)
    add_to_history(request.question, response)
    return response


@router.post("/ask/advisory/stream")
async def ask_advisory_stream(request: AskRequest, x_openai_key: Optional[str] = Header(default=None)):
    api_key = _visitor_key(request, x_openai_key)
    return StreamingResponse(
        stream_rag_advisory(request, api_key),
        media_type="application/x-ndjson",
    )


@router.post("/ask/compare", response_model=AskCompareResponse)
async def ask_compare(request: AskRequest, x_openai_key: Optional[str] = Header(default=None)):
    api_key = _visitor_key(request, x_openai_key)
    return await call_rag_compare(request, api_key)
