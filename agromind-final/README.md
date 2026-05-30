# AgroMind — Agriculture RAG System

An agricultural intelligence assistant powered by RAG (Retrieval-Augmented Generation).
Ask about crop diseases, pesticide guidance, and agronomy in any language.

---

## Project Structure

```
agromind-final/
├── app/
│   ├── main.py                  # FastAPI entry point
│   ├── config.py                # Environment settings
│   ├── routers/
│   │   ├── ask.py               # POST /api/ask
│   │   ├── health.py            # GET /api/health
│   │   └── history.py           # GET/DELETE /api/history
│   ├── schemas/
│   │   └── ask.py               # Request/Response models
│   ├── services/
│   │   └── rag_service.py       # LLM + RAG logic
│   └── middleware/
│       ├── error_handler.py     # Global error handling
│       └── logger.py            # Request logging
├── frontend-react/
│   ├── src/
│   │   ├── App.jsx              # Main React component
│   │   └── main.jsx             # React entry point
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── tests/
│   └── test_api.py
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## Quick Start

### 1. Setup

```bash
cd agromind-final
cp .env.example .env
pip install -r requirements.txt
```

### 2. Start the API

```bash
uvicorn app.main:app --reload --port 8000
```

API running at http://localhost:8000
Docs at http://localhost:8000/docs

### 3. Start the frontend (new terminal)

```bash
cd frontend-react
npm install
npm run dev
```

Frontend running at http://localhost:3000

---

## Supported LLM Providers

The system works with any LLM provider. Set in `.env`:

| Provider   | LLM_PROVIDER | Example Model                          |
|------------|--------------|----------------------------------------|
| OpenAI     | openai       | gpt-4o                                 |
| Groq       | groq         | llama-3.3-70b-versatile                |
| Anthropic  | anthropic    | claude-sonnet-4-20250514                    |
| Together   | together     | meta-llama/Llama-3-70b-chat-hf        |
| OpenRouter | openrouter   | meta-llama/llama-3.3-70b-instruct     |
| Ollama     | local        | llama3                                 |

### Example: Using Groq

```env
USE_MOCK=false
LLM_PROVIDER=groq
LLM_API_KEY=gsk_your_key
LLM_MODEL=llama-3.3-70b-versatile
```

### Example: Using OpenAI

```env
USE_MOCK=false
LLM_PROVIDER=openai
LLM_API_KEY=sk-your_key
LLM_MODEL=gpt-4o
```

### Example: Using Ollama (local, no key needed)

```env
USE_MOCK=false
LLM_PROVIDER=local
LLM_MODEL=llama3
LLM_BASE_URL=http://localhost:11434/api/chat
```

---

## Image Analysis

For plant photo analysis, set a vision-capable provider:

```env
VISION_PROVIDER=openai
VISION_API_KEY=sk-your_key
VISION_MODEL=gpt-4o
```

Or with Anthropic:

```env
VISION_PROVIDER=anthropic
VISION_API_KEY=sk-ant-your_key
VISION_MODEL=claude-sonnet-4-20250514
```

---

## Connecting RAG Service

This system is designed for a dynamic RAG pipeline, not static chunk retrieval.
When your team's RAG service is ready, set the full endpoint URL:

```env
RAG_SERVICE_URL=http://localhost:8001/query
```

The API sends this to your RAG service:

```json
{
  "question": "What causes brown spots on tomato?",
  "language": "en",
  "history": [
    { "role": "user", "content": "previous question" },
    { "role": "assistant", "content": "previous answer" }
  ],
  "crop_type": "tomato",
  "image_analysis": "optional image analysis text"
}
```

Your RAG service can return any of these formats:

```json
{
  "answer": "The brown spots indicate...",
  "sources": [{ "title": "...", "source": "..." }],
  "confidence": "high"
}
```

Or simply:

```json
{
  "response": "The brown spots indicate...",
  "references": ["Tomato Guide", "FAO 2022"]
}
```

Or even:

```json
{
  "text": "The brown spots indicate..."
}
```

The system auto-detects the field names (answer/response/text, sources/references).
Sources can be strings or objects. No code changes needed.

**Priority order:**
1. RAG service (if RAG_SERVICE_URL is set)
2. LLM only (if LLM_PROVIDER is set, no RAG)
3. Mock data (if USE_MOCK=true)

---

## API Endpoints

| Method | URL            | Description     |
|--------|----------------|-----------------|
| POST   | /api/ask       | Send a question |
| GET    | /api/health    | Status check    |
| GET    | /api/history   | Question log    |
| DELETE | /api/history   | Clear log       |

### POST /api/ask

Request:
```json
{
  "question": "What causes brown spots on tomato?",
  "crop_type": "all",
  "history": [
    { "role": "user", "content": "previous question" },
    { "role": "assistant", "content": "previous answer" }
  ],
  "image_base64": "optional",
  "image_mime": "optional"
}
```

Response:
```json
{
  "answer": "Brown spots indicate Early Blight...",
  "sources": [{ "title": "...", "source": "..." }],
  "confidence": "high",
  "retrieved_chunks": 4,
  "latency_ms": 1240,
  "system": "groq:llama-3.3-70b-versatile",
  "detected_language": "en"
}
```

---

## Features

- Works with any LLM provider (OpenAI, Groq, Anthropic, Together, OpenRouter, Ollama)
- Multi-language support (Arabic/English auto-detection)
- Conversation history (context-aware follow-ups)
- Image upload for plant disease analysis
- Dark/Light mode
- Conversation management (create, switch, delete)
- RTL support for Arabic
- Mock mode for development without API keys
- Ready for RAG integration

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Docker

```bash
docker build -t agromind .
docker run -p 8000:8000 --env-file .env agromind
```
