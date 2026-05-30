from pydantic import BaseModel, Field
from typing import List, Optional


class ChatMessage(BaseModel):
    role: str
    content: str


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    crop_type: Optional[str] = "all"
    question_type: Optional[str] = "all"
    image_base64: Optional[str] = None
    image_mime: Optional[str] = None
    history: List[ChatMessage] = []


class SourceDoc(BaseModel):
    title: str
    source: str
    section: Optional[str] = None


class AskResponse(BaseModel):
    answer: str
    sources: List[SourceDoc]
    confidence: str
    retrieved_chunks: int
    latency_ms: int
    system: str = "rag"
    detected_language: str = "en"
    image_analysis: Optional[str] = None
