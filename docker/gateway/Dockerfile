# =============================================================================
# Gateway API — TerraMind web BFF (port 8000)
# =============================================================================
# Proxies the React UI to the model API. Handles optional vision pre-processing.
# Does NOT run RAG, ChromaDB, or torch — see requirements-gateway.txt.
#
# Layers (bottom → top):
#   1. base image (Python runtime)
#   2. pip install gateway deps only (changes rarely → cached)
#   3. COPY source code (changes often → rebuilds from here)

FROM python:3.11-slim

WORKDIR /app

COPY requirements-gateway.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements-gateway.txt

COPY core/ core/
COPY web/ web/

ENV PYTHONUNBUFFERED=1
# Compose overrides RAG_SERVICE_URL; default matches local dev
ENV RAG_SERVICE_URL=http://model-api:8001/query
ENV USE_MOCK=false

WORKDIR /app/web

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --retries=5 --start-period=20s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')" || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
