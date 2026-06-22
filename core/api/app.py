"""
TerraMind unified model API — routes questions to product RAG, general RAG, or base LLM.

Run from repo root:
    uvicorn core.api.app:app --reload --port 8001
    # or: uvicorn core.api.app:app --reload --port 8001
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

load_dotenv()

from core.models import (
    DEFAULT_MODEL_ID,
    all_model_ids,
    list_models,
    model_display_name,
    resolve_image_analysis,
    run_advisory,
    run_model,
)

_log = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Warm product retrieval (BM25 + reranker) so the first chat request is not multi-minute."""
    try:
        from core.rag.product.pipeline import warm_product_rag

        await asyncio.to_thread(warm_product_rag)
        _log.info("Product RAG warmup finished")
    except Exception as exc:
        _log.warning("Product RAG warmup skipped (lazy load on first query): %s", exc)
    yield


app = FastAPI(title="TerraMind Model API", version="2.1.0", lifespan=_lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    model: str = Field(
        default=DEFAULT_MODEL_ID,
        description="auto_rag | product_rag | general_rag | base_llm",
    )
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
    relevance_score: float | None = None
    chunk_count: int | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceOut]
    confidence: str
    retrieval_score: float | None = None
    retrieved_chunks: int
    system: str
    model: str
    routed_to: str | None = None
    router_reason: str | None = None


class ModelCompareResult(BaseModel):
    model: str
    model_name: str
    answer: str
    sources: list[SourceOut]
    confidence: str
    retrieval_score: float | None = None
    retrieved_chunks: int
    latency_ms: int
    error: str | None = None


class CompareResponse(BaseModel):
    question: str
    results: list[ModelCompareResult]
    latency_ms: int


class AdvisoryPart(BaseModel):
    answer: str
    sources: list[SourceOut]
    confidence: str
    retrieval_score: float | None = None
    retrieved_chunks: int
    system: str


class AdvisoryResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceOut]
    confidence: str
    retrieval_score: float | None = None
    retrieved_chunks: int
    system: str = "advisory"
    general: AdvisoryPart
    product: AdvisoryPart
    latency_ms: int


@app.get("/models")
def get_models():
    return {"models": list_models(), "default": DEFAULT_MODEL_ID}


@app.get("/health")
def health():
    """Lightweight liveness check — do not load Chroma or rebuild indexes here."""
    from core.rag.general.config import CHROMA_PATH as GENERAL_CHROMA
    from core.rag.product.config import CHROMA_PATH as PRODUCT_CHROMA

    def index_status(path) -> str:
        sqlite = path / "chroma.sqlite3"
        if sqlite.exists():
            return "indexed"
        return "missing"

    return {
        "status": "ok",
        "service": "terramind-models",
        "models": list_models(),
        "general_vectors": index_status(GENERAL_CHROMA),
        "product_vectors": index_status(PRODUCT_CHROMA),
    }


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
    print(f"[core.api] {request.model} answered in {elapsed_ms}ms")

    return QueryResponse(
        answer=result["answer"],
        sources=[SourceOut(**s) for s in result.get("sources", [])],
        confidence=result.get("confidence", "medium"),
        retrieval_score=result.get("retrieval_score"),
        retrieved_chunks=result.get("retrieved_chunks", 0),
        system=result.get("system", request.model),
        model=request.model,
        routed_to=result.get("routed_to"),
        router_reason=result.get("router_reason"),
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
                retrieval_score=result.get("retrieval_score"),
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
    print(f"[core.api] compare answered in {elapsed_ms}ms")

    return CompareResponse(question=question, results=list(results), latency_ms=elapsed_ms)


@app.post("/query/advisory", response_model=AdvisoryResponse)
async def query_advisory(request: QueryRequest):
    """General agriculture guidance + product catalog in one flow (single vision call)."""
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
            run_advisory,
            question,
            request.history,
            analysis,
            None,
            None,
            request.language,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Advisory failed: {e}") from e

    elapsed_ms = int((time.time() - start) * 1000)
    print(f"[core.api] advisory answered in {elapsed_ms}ms")

    def _part(payload: dict, label: str) -> AdvisoryPart:
        return AdvisoryPart(
            answer=payload.get("answer", "") or "",
            sources=[SourceOut(**s) for s in payload.get("sources", [])],
            confidence=payload.get("confidence", "medium"),
            retrieval_score=payload.get("retrieval_score"),
            retrieved_chunks=payload.get("retrieved_chunks", 0),
            system=payload.get("system", label),
        )

    general = result.get("general") or {}
    product = result.get("product") or {}

    return AdvisoryResponse(
        question=question,
        answer=result.get("answer", "") or "",
        sources=[SourceOut(**s) for s in result.get("sources", [])],
        confidence=result.get("confidence", "medium"),
        retrieval_score=result.get("retrieval_score"),
        retrieved_chunks=result.get("retrieved_chunks", 0),
        general=_part(general, "general_rag"),
        product=_part(product, "product_rag"),
        latency_ms=elapsed_ms,
    )


def _stream_query(request: QueryRequest):
    from core.models.streaming import stream_model_events

    def generate():
        try:
            yield from stream_model_events(
                request.model,
                request.question.strip(),
                request.history,
                request.image_analysis,
                request.image_base64,
                request.image_mime,
                request.language,
            )
        except ValueError as e:
            import json

            yield json.dumps({"event": "error", "message": str(e)}) + "\n"
        except Exception as e:
            import json

            yield json.dumps({"event": "error", "message": f"Model failed: {e}"}) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")


@app.post("/query/stream")
async def query_stream(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="question is required")
    return _stream_query(request)


@app.post("/query/advisory/stream")
async def query_advisory_stream(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="question is required")

    def generate():
        from core.models.streaming import stream_advisory_events

        try:
            yield from stream_advisory_events(
                request.question.strip(),
                request.history,
                request.image_analysis,
                request.image_base64,
                request.image_mime,
                request.language,
            )
        except Exception as e:
            import json

            yield json.dumps({"event": "error", "message": f"Advisory failed: {e}"}) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")


class OpenAIKeyIn(BaseModel):
    api_key: str = Field(..., min_length=20, max_length=512)


@app.get("/config/openai-status")
def openai_status():
    import os

    key = os.getenv("OPENAI_API_KEY", "").strip()
    return {"openai_configured": bool(key)}


@app.post("/internal/openai-key")
def set_openai_key(body: OpenAIKeyIn):
    """Local dev: apply key for this Model API process (called by web BFF)."""
    import os

    key = body.api_key.strip()
    if not key.startswith(("sk-", "sk-proj-")):
        raise HTTPException(status_code=400, detail="Invalid OpenAI API key format")
    os.environ["OPENAI_API_KEY"] = key
    return {"ok": True, "openai_configured": True}
