from fastapi import APIRouter, HTTPException
from app.schemas.ask import AskCompareResponse, AskRequest, AskResponse
from app.services.rag_service import call_rag, call_rag_compare
from app.routers.history import add_to_history

router = APIRouter()


@router.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    response = await call_rag(request)
    add_to_history(request.question, response)
    return response


@router.post("/ask/compare", response_model=AskCompareResponse)
async def ask_compare(request: AskRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    return await call_rag_compare(request)
