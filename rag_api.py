"""
TerraMind unified model API — routes questions to product RAG, general RAG, or base LLM.

Run from repo root:
    uvicorn rag_api:app --reload --port 8001

FrontPage .env:
    USE_MOCK=false
    RAG_SERVICE_URL=http://localhost:8001/query
"""

import asyncio
import time

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

load_dotenv()

from models import (
    DEFAULT_MODEL_ID,
    all_model_ids,
    list_models,
    model_display_name,
    resolve_image_analysis,
    run_model,
)

app = FastAPI(title="TerraMind Model API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    model: str = Field(default=DEFAULT_MODEL_ID, description="product_rag | general_rag | base_llm")
    language: str | None = None
    history: list[dict] = []
    crop_type: str | None = None
    image_analysis: str | None = None
    image_base64: str | None = None
    image_mime: str | None = None


class SourceOut(BaseModel):
    title: str
    source: str
    section: str | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceOut]
    confidence: str
    retrieved_chunks: int
    system: str
    model: str


class ModelCompareResult(BaseModel):
    model: str
    model_name: str
    answer: str
    sources: list[SourceOut]
    confidence: str
    retrieved_chunks: int
    latency_ms: int
    error: str | None = None


class CompareResponse(BaseModel):
    question: str
    results: list[ModelCompareResult]
    latency_ms: int


@app.get("/models")
def get_models():
    return {"models": list_models(), "default": DEFAULT_MODEL_ID}


@app.get("/health")
def health():
    status = {"status": "ok", "service": "terramind-models", "models": list_models()}
    try:
        from Rag_Pc import get_product_db
        status["product_vectors"] = get_product_db()._collection.count()
    except Exception as e:
        status["product_vectors"] = f"error: {e}"
    try:
        from Rag_Gen import get_general_db
        status["general_vectors"] = get_general_db()._collection.count()
    except Exception as e:
        status["general_vectors"] = f"error: {e}"
    return status


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="question is required")

    question = request.question.strip()
    start = time.time()
    try:
        analysis = None
        if request.image_base64 and request.image_mime:
            analysis = resolve_image_analysis(
                question,
                request.image_analysis,
                request.image_base64,
                request.image_mime,
                request.language,
            )
        elif request.image_analysis:
            analysis = request.image_analysis.strip()

        result = await asyncio.to_thread(
            run_model,
            request.model,
            question,
            request.history,
            analysis,
            None,
            None,
            request.language,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model failed: {e}") from e

    elapsed_ms = int((time.time() - start) * 1000)
    print(f"[rag_api] {request.model} answered in {elapsed_ms}ms")

    return QueryResponse(
        answer=result["answer"],
        sources=[SourceOut(**s) for s in result.get("sources", [])],
        confidence=result.get("confidence", "medium"),
        retrieved_chunks=result.get("retrieved_chunks", 0),
        system=result.get("system", request.model),
        model=request.model,
    )


@app.post("/query/compare", response_model=CompareResponse)
async def query_compare(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="question is required")

    question = request.question.strip()
    history = request.history
    start = time.time()

    shared_analysis = None
    if request.image_base64 and request.image_mime:
        try:
            shared_analysis = resolve_image_analysis(
                question,
                request.image_analysis,
                request.image_base64,
                request.image_mime,
                request.language,
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Image analysis failed: {e}") from e
    elif request.image_analysis:
        shared_analysis = request.image_analysis.strip()

    async def run_one(model_id: str) -> ModelCompareResult:
        t0 = time.time()
        try:
            result = await asyncio.to_thread(
                run_model,
                model_id,
                question,
                history,
                shared_analysis,
                None,
                None,
                request.language,
            )
            return ModelCompareResult(
                model=model_id,
                model_name=model_display_name(model_id),
                answer=result.get("answer", "") or "",
                sources=[SourceOut(**s) for s in result.get("sources", [])],
                confidence=result.get("confidence", "medium"),
                retrieved_chunks=result.get("retrieved_chunks", 0),
                latency_ms=int((time.time() - t0) * 1000),
            )
        except Exception as e:
            return ModelCompareResult(
                model=model_id,
                model_name=model_display_name(model_id),
                answer="",
                sources=[],
                confidence="low",
                retrieved_chunks=0,
                latency_ms=int((time.time() - t0) * 1000),
                error=str(e),
            )

    results = await asyncio.gather(*[run_one(mid) for mid in all_model_ids()])
    elapsed_ms = int((time.time() - start) * 1000)
    print(f"[rag_api] compare answered in {elapsed_ms}ms")

    return CompareResponse(question=question, results=list(results), latency_ms=elapsed_ms)
