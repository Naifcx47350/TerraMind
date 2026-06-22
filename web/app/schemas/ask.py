from pydantic import BaseModel, Field
from typing import List, Optional


class ChatMessage(BaseModel):
    role: str
    content: str


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    model: Optional[str] = Field(
        default="auto_rag",
        description="auto_rag | product_rag | general_rag | base_llm",
    )
    crop_type: Optional[str] = "all"
    question_type: Optional[str] = "all"
    image_base64: Optional[str] = None
    image_mime: Optional[str] = None
    history: List[ChatMessage] = []


class SourceDoc(BaseModel):
    title: str
    source: str
    section: Optional[str] = None
    relevance_score: Optional[float] = None
    chunk_count: Optional[int] = None


class AskResponse(BaseModel):
    answer: str
    sources: List[SourceDoc]
    confidence: str
    retrieval_score: Optional[float] = None
    retrieved_chunks: int
    latency_ms: int
    system: str = "rag"
    model: str = "auto_rag"
    routed_to: Optional[str] = None
    router_reason: Optional[str] = None
    detected_language: str = "en"
    image_analysis: Optional[str] = None


class ModelCompareResult(BaseModel):
    model: str
    model_name: str
    answer: str
    sources: List[SourceDoc] = []
    confidence: str = "medium"
    retrieval_score: Optional[float] = None
    retrieved_chunks: int = 0
    latency_ms: int = 0
    error: Optional[str] = None


class AskCompareResponse(BaseModel):
    question: str
    results: List[ModelCompareResult]
    latency_ms: int
    detected_language: str = "en"
    image_analysis: Optional[str] = None
