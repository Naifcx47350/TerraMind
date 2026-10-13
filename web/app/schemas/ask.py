from pydantic import BaseModel, ConfigDict, Field
from typing import List, Literal, Optional

# Request size limits. The UI sends at most 20 history messages and downscales
# photos before upload; these bounds stop oversized requests from eating memory.
MAX_HISTORY_MESSAGES = 40
MAX_MESSAGE_CHARS = 20_000
MAX_IMAGE_BASE64_CHARS = 8_000_000  # ~6 MB image
IMAGE_MIME_PATTERN = r"^image/(jpeg|png|webp|gif)$"


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=MAX_MESSAGE_CHARS)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    model: Optional[str] = Field(
        default="auto_rag",
        max_length=40,
        description="auto_rag | product_rag | general_rag | base_llm",
    )
    crop_type: Optional[str] = Field(default="all", max_length=40)
    question_type: Optional[str] = Field(default="all", max_length=40)
    image_base64: Optional[str] = Field(default=None, max_length=MAX_IMAGE_BASE64_CHARS)
    image_mime: Optional[str] = Field(default=None, pattern=IMAGE_MIME_PATTERN)
    history: List[ChatMessage] = Field(default_factory=list, max_length=MAX_HISTORY_MESSAGES)
    # Demo session: sample answers, no OpenAI key needed.
    demo: bool = False


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
    model_config = ConfigDict(protected_namespaces=())

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
