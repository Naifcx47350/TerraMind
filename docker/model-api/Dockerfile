# =============================================================================
# Model API — TerraMind RAG + LLM backend (port 8001)
# =============================================================================
# Build context: repo root (..)
#   docker compose build model-api
#
# Layers (bottom → top):
#   1. base image (Python runtime)
#   2. OS packages + pip install (changes rarely → cached)
#   3. COPY source code (changes often → rebuilds from here)

FROM python:3.11-slim

WORKDIR /app

# ChromaDB / some wheels need a compiler on slim images
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# CPU-only PyTorch first — PyPI default torch on Linux pulls multi-GB NVIDIA/CUDA wheels.
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu \
        "torch>=2.0,<3" \
    && pip install --no-cache-dir -r requirements.txt

COPY core/ core/

# Pre-download CrossEncoder reranker used by product RAG (~90MB; avoids first-query delay).
RUN python -c "from sentence_transformers import CrossEncoder; CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"

# Corpus (PDFs, product Excel) is mounted at runtime — see docker-compose.yml

# Indexes live on a named volume (see docker-compose.yml), not in the image
RUN mkdir -p vectorstore/chroma vectorstore/chroma_products

ENV PYTHONUNBUFFERED=1

EXPOSE 8001

HEALTHCHECK --interval=15s --timeout=5s --retries=8 --start-period=120s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8001/health')" || exit 1

CMD ["python", "-m", "uvicorn", "core.api.app:app", "--host", "0.0.0.0", "--port", "8001"]
