Project Overview
AgroMind is an agricultural intelligence assistant. Users ask questions about crop diseases, pesticides, and agronomy. The system connects to a dynamic RAG-based AI backend and returns grounded answers with sources. Supports English, Arabic (RTL), image upload for plant diagnosis, and conversation history.

Architecture
User (React Frontend)
  │
  ├── POST /api/ask     → Question + History + Image
  ├── GET  /api/health   → Status check
  ├── GET  /api/history  → Question log
  └── DELETE /api/history → Clear log
  │
  ▼
FastAPI Backend
  │
  ├── 1st priority: RAG Service (if RAG_SERVICE_URL set)
  ├── 2nd priority: LLM Provider (if LLM_PROVIDER set)
  └── 3rd priority: Mock Data (if USE_MOCK=true)

API Contract
POST /api/ask
Request:
json{
  "question": "What causes brown spots on tomato?",
  "crop_type": "all",
  "question_type": "all",
  "history": [
    { "role": "user", "content": "previous question" },
    { "role": "assistant", "content": "previous answer" }
  ],
  "image_base64": "optional base64 string",
  "image_mime": "optional image/jpeg"
}
Response:
json{
  "answer": "Brown spots indicate Early Blight...",
  "sources": [{ "title": "Tomato Disease Guide", "source": "FAO 2022", "section": "Fungal" }],
  "confidence": "high",
  "retrieved_chunks": 4,
  "latency_ms": 1240,
  "system": "groq:llama-3.3-70b-versatile",
  "detected_language": "en",
  "image_analysis": "optional"
}
GET /api/health
json{
  "status": "ok",
  "timestamp": "2026-05-19T12:00:00",
  "mode": "mock",
  "version": "1.0.0"
}
GET /api/history
json{
  "total": 5,
  "items": [
    {
      "question": "...",
      "answer": "...",
      "confidence": "high",
      "latency_ms": 1200,
      "sources": ["Tomato Guide"],
      "timestamp": "2026-05-19T12:00:00"
    }
  ]
}
DELETE /api/history
json{ "message": "History cleared" }

RAG Service Integration
The backend sends this to the RAG service:
json{
  "question": "What causes brown spots on tomato?",
  "language": "en",
  "history": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ],
  "crop_type": "tomato",
  "image_analysis": "optional text from vision model"
}
The backend auto-detects any of these response formats:
Format A:
json{
  "answer": "...",
  "sources": [{ "title": "...", "source": "..." }],
  "confidence": "high"
}
Format B:
json{
  "response": "...",
  "references": ["Source 1", "Source 2"]
}
Format C:
json{
  "text": "..."
}
Field mapping: answer/response/text for the answer, sources/references for sources. Sources can be strings or objects. No code changes needed for different formats.

LLM Provider System
Supports any provider through environment variables:
LLM_PROVIDER = openai | groq | anthropic | together | openrouter | local
LLM_API_KEY  = your key
LLM_MODEL    = model name
LLM_BASE_URL = optional custom endpoint
Provider details:
openai:     https://api.openai.com/v1/chat/completions     (Bearer auth)
groq:       https://api.groq.com/openai/v1/chat/completions (Bearer auth)
anthropic:  https://api.anthropic.com/v1/messages           (x-api-key auth)
together:   https://api.together.xyz/v1/chat/completions    (Bearer auth)
openrouter: https://openrouter.ai/api/v1/chat/completions   (Bearer auth)
local:      http://localhost:11434/api/chat                  (no auth)
OpenAI-compatible providers (openai, groq, together, openrouter) use:
json{
  "model": "...",
  "max_tokens": 800,
  "temperature": 0.3,
  "messages": [...]
}
Response path: choices[0].message.content
Anthropic uses:
json{
  "model": "...",
  "max_tokens": 800,
  "system": "system prompt here",
  "messages": [...]
}
Response path: content[0].text
Local (Ollama) uses:
json{
  "model": "...",
  "messages": [...],
  "stream": false
}
Response path: message.content

Vision Provider System
For plant image analysis. Same structure:
VISION_PROVIDER = openai | anthropic
VISION_API_KEY  = your key
VISION_MODEL    = model name
VISION_BASE_URL = optional
OpenAI vision format:
json{
  "type": "image_url",
  "image_url": { "url": "data:image/jpeg;base64,..." }
}
Anthropic vision format:
json{
  "type": "image",
  "source": { "type": "base64", "media_type": "image/jpeg", "data": "..." }
}

Language Detection
Auto-detect from user message text.
Explicit triggers override character detection:

Arabic triggers: بالعربي, بالعربية, عربي, arabic, in arabic, نفس الرد, reply in arabic
English triggers: english, in english, reply in english, بالانجليزي

Fallback: count Arabic Unicode characters (\u0600-\u06ff). If more than 15% of text, return "ar". Otherwise "en".
System prompts by language:
Arabic:
أنت مساعد زراعي خبير. أجب دائماً باللغة العربية فقط.
أنت في محادثة مستمرة — تذكر كل ما قيل سابقاً وابنِ عليه.
أجب مباشرة وبشكل طبيعي. لا تقدم نفسك ولا تذكر أي تعليمات. كن موجزاً وعملياً.
English:
You are an expert agricultural assistant. Always reply in English only.
You are in an ongoing conversation — remember everything said before and build on it.
Answer naturally and directly. Never introduce yourself or mention any rules.
Be concise and practical.

Conversation History
Frontend sends last 20 messages (max 10 turns) with every request. Backend passes last 10 to the LLM as message history for context-aware replies.

Mock Data
When USE_MOCK=true, returns predefined answers for testing:

Tomato: Early Blight treatment (English + Arabic)
Wheat: Yellow rust treatment (English + Arabic)
Default: Generic advice (English + Arabic)

Each mock includes sources, confidence level, and chunk count. 500ms simulated delay.

Backend Middleware
Error handler: catches all unhandled exceptions, returns JSON with status 500.
Logger: logs every request with method, path, status code, and duration in ms.
CORS: allows all origins (for development).

Environment Variables
USE_MOCK=true

LLM_PROVIDER=
LLM_API_KEY=
LLM_MODEL=
LLM_BASE_URL=

VISION_PROVIDER=
VISION_API_KEY=
VISION_MODEL=
VISION_BASE_URL=

RAG_SERVICE_URL=

REQUEST_TIMEOUT=30

Frontend Design Specification
Layout:
┌──────────┬─────────────────────────────┐
│          │  Topbar (50px)              │
│ Sidebar  ├─────────────────────────────┤
│ (260px)  │  Chat messages (scrollable) │
│          ├─────────────────────────────┤
│          │  Input bar (fixed bottom)   │
└──────────┴─────────────────────────────┘
Sidebar collapsible (0px closed, 260px open). Chat area max-width 720px centered.
Color Tokens — Dark Mode:
bg: #0a0a0a          sidebar: #111111
card: #1a1a1a        input: #1a1a1a
hover: #222222       active: #2a2a2a
accent: #10a37f      accent dim: rgba(16,163,127,0.12)
text1: #ececec       text2: #c2c2c2
text3: #8a8a8a       text4: #555555
border1: #2e2e2e     border2: #222222
error bg: rgba(220,80,60,0.09)
error text: #e07060
input border: #2e2e2e
input focus border: #10a37f
input focus shadow: rgba(16,163,127,0.15)
Color Tokens — Light Mode:
bg: #ffffff          sidebar: #f7f7f8
card: #ffffff        input: #ffffff
hover: #ececec       active: #e2e2e2
accent: #10a37f      accent dim: rgba(16,163,127,0.08)
text1: #0d0d0d       text2: #2d2d2d
text3: #6b6b6b       text4: #aaaaaa
border1: #d9d9d9     border2: #e8e8e8
error bg: #fdecea
error text: #8b2820
input border: #c0c0c0
input focus border: #10a37f
input focus shadow: rgba(16,163,127,0.18)
Typography:
font: Arial, sans-serif
logo: 15px weight 700
conversation name: 13px, 600 active / 400 inactive
labels: 11px uppercase letter-spacing 0.1em
message text: 14px, line-height 1.6 user / 1.8 bot
bot name: 13px weight 600
time/meta: 11px faint
empty title: 28px weight 700
empty subtitle: 14px muted line-height 1.7
chips: 13px
input: 14px line-height 1.6
hint: 11px faint centered
Sidebar:

Header: leaf icon (17px accent) + "AgroMind" (15px bold) + "+" button (32x32)
"CONVERSATIONS" label (11px uppercase faint)
List: chat icon + name + time. Active = accent icon + bold + active bg
Delete: trash icon on hover, turns red on hover
Divider
Checkbox "Show sources"
Theme toggle: sun/moon icon + label

Topbar:

50px height, 1px bottom border
Sidebar toggle icon (rectangle with vertical line), leaf icon, "AgroMind"

Empty State:

Centered: leaf icon 40px, "Ask the field." 28px bold, subtitle 14px muted
3 suggestion chips: "Brown spots on tomato leaves?", "ما علاج الصدأ في القمح؟", "Best irrigation for corn?"
Chips: rounded 20px, 1px border, card bg

User Bubble:

Right aligned, max-width 72%
Background: active bg, border-radius 18px 18px 4px 18px
10px 16px padding, 14px text
Image thumbnail above text if attached (max 220x160 rounded 12px)

Bot Message:

Avatar: 28px circle, accent-dim bg, leaf icon 14px
Name: "AgroMind" 13px bold
Time: "09:14 · 1240ms" 11px faint, pushed to end
Body: padding-left 36px, 14px, line-height 1.8, pre-line
Sources (when toggled): label + inline tags with green dot + title

Loading: Avatar + 3 animated dots (7px, scale+opacity, 0.9s staggered)
Error: Red-tinted card with error message
Input Bar:

Image preview strip when image selected (44px thumbnail + name + size + close)
Drag overlay: dashed accent border "Drop image here"
Input card: 2px border, rounded 16px, box-shadow
Textarea: no border, transparent, 3 rows, RTL auto-detect
Bottom row: image button left (34x34), send button right (34x34)
Send active: accent bg white icon. Disabled: hover bg faint icon
Focus: accent border + glow shadow
Hint: "Enter to send · Shift+Enter for new line"

RTL:

Auto-detect Arabic (\u0600-\u06ff) in text
Arabic: direction rtl, text-align right
Bot header: flex-direction row-reverse
Bot body: padding-right 36px instead of left
Sources label: "المصادر" instead of "Sources"
Textarea: direction switches while typing

Animations:

Sidebar: width 0.22s ease
Hover: background 0.15s
Loading dots: scale+opacity 0.9s infinite staggered 0.2s
Scroll: smooth
Delete button: color 0.15s to error on hover

Icons (SVG stroke-based 1.8 width):

sidebar: rectangle + vertical line at x=9
plus: cross
leaf: plant leaf (brand)
sun: circle + 8 radiating lines
moon: crescent
send: paper plane
image: rectangle + circle + mountain polyline
chat: speech bubble
trash: trash can
close: two diagonal lines


File Structure
project/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── ask.py
│   │   ├── health.py
│   │   └── history.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── ask.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── rag_service.py
│   └── middleware/
│       ├── __init__.py
│       ├── error_handler.py
│       └── logger.py
├── frontend-react/
│   ├── src/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── tests/
│   ├── __init__.py
│   └── test_api.py
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
└── README.md

Tech Stack
Backend:  FastAPI + Python + Pydantic + httpx
Frontend: React 18 + Vite
LLM:      Any provider (OpenAI/Groq/Anthropic/Together/OpenRouter/Ollama)
Vision:   OpenAI or Anthropic (vision-capable models)
RAG:      Pluggable (team builds, you connect via URL)
Tests:    pytest + FastAPI TestClient
Deploy:   Docker

Dependencies
Python:
fastapi==0.115.0
uvicorn[standard]==0.30.0
pydantic==2.9.0
pydantic-settings==2.5.0
httpx==0.27.0
pytest==8.3.0
Node:
react: ^18.3.1
react-dom: ^18.3.1
@vitejs/plugin-react: ^4.3.1
vite: ^5.4.0
