from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.schemas.ask import AskCompareResponse, AskRequest, AskResponse
from app.services.rag_service import (
    call_rag,
    call_rag_advisory,
    call_rag_compare,
    stream_rag,
    stream_rag_advisory,
)
from app.routers.history import add_to_history

router = APIRouter()


@router.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    response = await call_rag(request)
    add_to_history(request.question, response)
    return response


@router.post("/ask/stream")
async def ask_stream(request: AskRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    return StreamingResponse(
        stream_rag(request),
        media_type="application/x-ndjson",
    )


@router.post("/ask/advisory", response_model=AskResponse)
async def ask_advisory(request: AskRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    response = await call_rag_advisory(request)
    add_to_history(request.question, response)
    return response


@router.post("/ask/advisory/stream")
async def ask_advisory_stream(request: AskRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    return StreamingResponse(
        stream_rag_advisory(request),
        media_type="application/x-ndjson",
    )


@router.post("/ask/compare", response_model=AskCompareResponse)
async def ask_compare(request: AskRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    return await call_rag_compare(request)
