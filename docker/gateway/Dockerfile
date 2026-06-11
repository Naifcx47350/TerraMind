# =============================================================================
# Gateway API — FrontPage FastAPI (port 8000)
# =============================================================================
# Proxies the React UI to the model API. Needs repo root on PYTHONPATH for vision/RAG helpers.

FROM python:3.11-slim

WORKDIR /app

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

COPY terramind/ terramind/
COPY FrontPage/ FrontPage/

ENV PYTHONUNBUFFERED=1
# Compose overrides this; default matches local dev
ENV RAG_SERVICE_URL=http://model-api:8001/query
ENV USE_MOCK=false

WORKDIR /app/FrontPage

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --retries=5 --start-period=20s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')" || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
