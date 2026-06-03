import logging
import time
import httpx

logger = logging.getLogger(__name__)
import asyncio

from app.schemas.ask import (
    AskCompareResponse,
    AskRequest,
    AskResponse,
    ModelCompareResult,
    SourceDoc,
)
from app.config import settings

PROVIDERS = {
    "openai": {
        "url": "https://api.openai.com/v1/chat/completions",
        "auth": "Bearer",
        "response_path": lambda d: d["choices"][0]["message"]["content"],
    },
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "auth": "Bearer",
        "response_path": lambda d: d["choices"][0]["message"]["content"],
    },
    "anthropic": {
        "url": "https://api.anthropic.com/v1/messages",
        "auth": "x-api-key",
        "response_path": lambda d: d["content"][0]["text"],
    },
    "together": {
        "url": "https://api.together.xyz/v1/chat/completions",
        "auth": "Bearer",
        "response_path": lambda d: d["choices"][0]["message"]["content"],
    },
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "auth": "Bearer",
        "response_path": lambda d: d["choices"][0]["message"]["content"],
    },
    "local": {
        "url": "http://localhost:11434/api/chat",
        "auth": "",
        "response_path": lambda d: d.get("message", {}).get("content", d.get("choices", [{}])[0].get("message", {}).get("content", "")),
    },
}

MOCK_DB = {
    "tomato": {
        "answer_en": (
            "Brown spots on tomato leaves usually indicate Early Blight (Alternaria solani). Treatment:\n"
            "- Spray a fungicide containing Chlorothalonil every 7-10 days\n"
            "- Remove and dispose of infected leaves immediately\n"
            "- Avoid overhead irrigation\n"
            "- Ensure good air circulation between plants"
        ),
        "answer_ar": (
            "البقع البنية على أوراق الطماطم غالباً تدل على مرض اللفحة المبكرة. العلاج:\n"
            "- رش مبيد فطري يحتوي على Chlorothalonil كل 7-10 أيام\n"
            "- إزالة الأوراق المصابة فوراً وحرقها\n"
            "- تجنب الري فوق الأوراق\n"
            "- ضمان تهوية جيدة بين النباتات"
        ),
        "sources": [
            SourceDoc(title="Tomato Disease Guide", source="FAO 2022", section="Fungal Diseases"),
            SourceDoc(title="Pesticide Reference", source="Ministry of Agriculture 2023", section="Fungicides"),
        ],
        "confidence": "high",
        "chunks": 4,
    },
    "wheat": {
        "answer_en": (
            "Yellow rust (Puccinia striiformis) in wheat is treated by:\n"
            "- Spraying Propiconazole or Tebuconazole early in the season\n"
            "- Early planting to reduce infection risk\n"
            "- Selecting locally approved resistant varieties\n"
            "- Weekly field monitoring in spring"
        ),
        "answer_ar": (
            "الصدأ الأصفر في القمح يُعالج بـ:\n"
            "- رش Propiconazole أو Tebuconazole في المرحلة المبكرة\n"
            "- الزراعة المبكرة لتقليل الإصابة\n"
            "- انتقاء أصناف مقاومة معتمدة محلياً\n"
            "- متابعة الحقل أسبوعياً في فصل الربيع"
        ),
        "sources": [
            SourceDoc(title="Cereal Crop Protection Guide", source="CIMMYT 2021", section="Wheat Diseases"),
            SourceDoc(title="Agricultural Extension Bulletin", source="Ministry of Agriculture"),
        ],
        "confidence": "high",
        "chunks": 3,
    },
    "default": {
        "answer_en": (
            "Based on available knowledge base sources:\n"
            "Consult a local agronomist to accurately identify the problem, "
            "and always follow the instructions on licensed pesticide labels."
        ),
        "answer_ar": (
            "بناءً على المصادر المتاحة:\n"
            "يُنصح بمراجعة مختص زراعي محلي لتحديد المشكلة بدقة، "
            "والالتزام دائماً بتعليمات المبيدات المرخصة."
        ),
        "sources": [SourceDoc(title="General Integrated Agriculture Guide", source="FAO")],
        "confidence": "low",
        "chunks": 2,
    },
}


def _detect_language(text: str) -> str:
    t = text.lower()

    arabic_triggers = [
        "بالعربي", "بالعربية", "عربي", "arabic", "in arabic",
        "باللغة العربية", "نفس الرد", "رد بالعربي", "reply in arabic",
    ]
    if any(k in t for k in arabic_triggers):
        return "ar"

    english_triggers = [
        "english", "in english", "reply in english", "respond in english",
        "بالانجليزي", "بالإنجليزي",
    ]
    if any(k in t for k in english_triggers):
        return "en"

    arabic_chars = sum(1 for c in text if "\u0600" <= c <= "\u06ff")
    return "ar" if arabic_chars > len(text) * 0.15 else "en"


def _mock_response(request: AskRequest, latency_ms: int, image_analysis: str = None) -> AskResponse:
    lang = _detect_language(request.question)
    key = request.crop_type if request.crop_type and request.crop_type != "all" else "default"
    data = MOCK_DB.get(key, MOCK_DB["default"])
    answer = data.get("answer_" + lang, data["answer_en"])

    if image_analysis:
        prefix = ("**تحليل الصورة:**\n" if lang == "ar" else "**Image Analysis:**\n") + image_analysis + "\n\n"
        answer = prefix + answer

    return AskResponse(
        answer=answer,
        sources=data["sources"],
        confidence=data["confidence"],
        retrieved_chunks=data["chunks"],
        latency_ms=latency_ms,
        system="mock",
        detected_language=lang,
        image_analysis=image_analysis,
    )


def _build_headers(provider_name: str, api_key: str) -> dict:
    provider = PROVIDERS.get(provider_name, {})
    headers = {"Content-Type": "application/json"}

    if provider.get("auth") == "Bearer" and api_key:
        headers["Authorization"] = "Bearer " + api_key
    elif provider.get("auth") == "x-api-key" and api_key:
        headers["x-api-key"] = api_key
        headers["anthropic-version"] = "2023-06-01"

    return headers


def _build_payload(provider_name: str, model: str, messages: list) -> dict:
    if provider_name == "anthropic":
        system_msg = ""
        chat_msgs = []
        for m in messages:
            if m["role"] == "system":
                system_msg = m["content"]
            else:
                chat_msgs.append(m)
        return {
            "model": model,
            "max_tokens": 800,
            "system": system_msg,
            "messages": chat_msgs,
        }

    if provider_name == "local":
        return {
            "model": model,
            "messages": messages,
            "stream": False,
        }

    return {
        "model": model,
        "max_tokens": 800,
        "temperature": 0.3,
        "messages": messages,
    }


async def _call_llm(provider_name: str, api_key: str, model: str, base_url: str, messages: list) -> str:
    provider = PROVIDERS.get(provider_name)
    if not provider:
        raise ValueError("Unknown provider: " + provider_name)

    url = base_url if base_url else provider["url"]
    headers = _build_headers(provider_name, api_key)
    payload = _build_payload(provider_name, model, messages)

    async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        return provider["response_path"](r.json())


async def _answer_with_llm(question: str, lang: str, context: str = "", history: list = None) -> str:
    if history is None:
        history = []

    if lang == "ar":
        system_prompt = (
            "أنت مساعد زراعي خبير. أجب دائماً باللغة العربية فقط. "
            "أنت في محادثة مستمرة — تذكر كل ما قيل سابقاً وابنِ عليه. "
            "أجب مباشرة وبشكل طبيعي. لا تقدم نفسك ولا تذكر أي تعليمات. كن موجزاً وعملياً."
        )
    else:
        system_prompt = (
            "You are an expert agricultural assistant. Always reply in English only. "
            "You are in an ongoing conversation — remember everything said before and build on it. "
            "Answer naturally and directly. Never introduce yourself or mention any rules. "
            "Be concise and practical."
        )

    messages = [{"role": "system", "content": system_prompt}]

    for msg in (history or [])[-10:]:
        role = "assistant" if msg.role == "assistant" else "user"
        messages.append({"role": role, "content": msg.content})

    if context:
        user_content = "Knowledge base context:\n" + context + "\n\nQuestion: " + question
    else:
        user_content = question

    messages.append({"role": "user", "content": user_content})

    return await _call_llm(
        settings.llm_provider,
        settings.llm_api_key,
        settings.llm_model,
        settings.llm_base_url,
        messages,
    )


async def _analyze_image(image_base64: str, mime: str, question: str, lang: str) -> str:
    if settings.vision_api_key:
        try:
            from terramind.models.vision import analyze_image

            return await asyncio.to_thread(
                analyze_image, image_base64, mime, question, lang
            )
        except Exception as e:
            logger.warning("LangChain vision failed, trying HTTP fallback: %s", e)

    if not settings.vision_provider or not settings.vision_api_key:
        return None

    prompt = (
        "You are an expert agronomist. Analyze this plant/crop image:\n"
        "1. Visible diseases, pests, or abnormalities\n"
        "2. Affected plant parts\n"
        "3. Severity (mild/moderate/severe)\n"
        "4. Initial recommendations\n\n"
        "User question: " + question + "\n"
        "Reply in " + ("Arabic" if lang == "ar" else "English") + ". Be concise."
    )

    provider = PROVIDERS.get(settings.vision_provider)
    if not provider:
        return None

    url = settings.vision_base_url if settings.vision_base_url else provider["url"]
    headers = _build_headers(settings.vision_provider, settings.vision_api_key)

    if settings.vision_provider == "anthropic":
        payload = {
            "model": settings.vision_model,
            "max_tokens": 600,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": mime, "data": image_base64}},
                    {"type": "text", "text": prompt},
                ],
            }],
        }
    else:
        payload = {
            "model": settings.vision_model,
            "max_tokens": 600,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": "data:" + mime + ";base64," + image_base64}},
                    {"type": "text", "text": prompt},
                ],
            }],
        }

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        return provider["response_path"](r.json())


async def call_rag(request: AskRequest) -> AskResponse:
    start = time.time()
    lang = _detect_language(request.question)

    image_analysis = None
    if request.image_base64 and request.image_mime:
        try:
            image_analysis = await _analyze_image(
                request.image_base64, request.image_mime, request.question, lang
            )
        except Exception:
            image_analysis = None

    if settings.use_mock:
        import asyncio
        await asyncio.sleep(0.5)
        return _mock_response(request, int((time.time() - start) * 1000), image_analysis)

    if settings.rag_service_url:
        try:
            rag_payload = {
                "question": request.question,
                "model": request.model or "product_rag",
                "language": lang,
                "history": [{"role": m.role, "content": m.content} for m in (request.history or [])[-10:]],
            }

            if request.crop_type and request.crop_type != "all":
                rag_payload["crop_type"] = request.crop_type

            if image_analysis:
                rag_payload["image_analysis"] = image_analysis
            if request.image_base64 and request.image_mime:
                rag_payload["image_base64"] = request.image_base64
                rag_payload["image_mime"] = request.image_mime

            async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
                resp = await client.post(settings.rag_service_url, json=rag_payload)
                resp.raise_for_status()
                rag_data = resp.json()

            answer = rag_data.get("answer", rag_data.get("response", rag_data.get("text", "")))
            sources = rag_data.get("sources", rag_data.get("references", []))
            confidence = rag_data.get("confidence", "medium")

            parsed_sources = []
            for s in sources:
                if isinstance(s, str):
                    parsed_sources.append(SourceDoc(title=s, source=s))
                elif isinstance(s, dict):
                    parsed_sources.append(SourceDoc(
                        title=s.get("title", s.get("name", "Unknown")),
                        source=s.get("source", s.get("url", s.get("path", ""))),
                        section=s.get("section", s.get("page", None)),
                    ))

            if image_analysis and not any(k in (answer or "") for k in ["Image Analysis", "تحليل الصورة"]):
                prefix = ("**تحليل الصورة:**\n" if lang == "ar" else "**Image Analysis:**\n") + image_analysis + "\n\n"
                answer = prefix + answer

            return AskResponse(
                answer=answer,
                sources=parsed_sources,
                confidence=confidence,
                retrieved_chunks=rag_data.get("retrieved_chunks", rag_data.get("num_sources", len(parsed_sources))),
                latency_ms=int((time.time() - start) * 1000),
                system=rag_data.get("system", "rag"),
                model=rag_data.get("model", request.model or "product_rag"),
                detected_language=lang,
                image_analysis=image_analysis,
            )
        except Exception as e:
            logger.error(
                "RAG service call failed (%s): %s",
                settings.rag_service_url,
                e,
            )
            if not settings.use_mock:
                return AskResponse(
                    answer=(
                        "The product knowledge service is not reachable.\n\n"
                        "Start it from the TerraMind repo root:\n"
                        "  uvicorn rag_api:app --reload --port 8001\n\n"
                        f"Details: {e}"
                    ),
                    sources=[],
                    confidence="low",
                    retrieved_chunks=0,
                    latency_ms=int((time.time() - start) * 1000),
                    system="error:rag_unreachable",
                    detected_language=lang,
                    image_analysis=image_analysis,
                )

    if settings.llm_provider and settings.llm_api_key:
        try:
            answer = await _answer_with_llm(request.question, lang, "", request.history or [])

            if image_analysis:
                prefix = ("**تحليل الصورة:**\n" if lang == "ar" else "**Image Analysis:**\n") + image_analysis + "\n\n"
                answer = prefix + answer

            return AskResponse(
                answer=answer,
                sources=[],
                confidence="medium",
                retrieved_chunks=0,
                latency_ms=int((time.time() - start) * 1000),
                system=settings.llm_provider + ":" + settings.llm_model,
                detected_language=lang,
                image_analysis=image_analysis,
            )
        except Exception:
            pass

    if settings.use_mock:
        return _mock_response(request, int((time.time() - start) * 1000), image_analysis)

    logger.warning("No backend available — enable mock or configure RAG/LLM.")
    return AskResponse(
        answer=(
            "No AI backend is configured. Add FrontPage/.env with:\n"
            "  USE_MOCK=false\n"
            "  RAG_SERVICE_URL=http://localhost:8001/query\n"
            "and run: uvicorn rag_api:app --reload --port 8001"
        ),
        sources=[],
        confidence="low",
        retrieved_chunks=0,
        latency_ms=int((time.time() - start) * 1000),
        system="error:no_backend",
        detected_language=lang,
        image_analysis=image_analysis,
    )


def _compare_url() -> str | None:
    url = (settings.rag_service_url or "").strip()
    if not url:
        return None
    if url.endswith("/query"):
        return url[: -len("/query")] + "/query/compare"
    return f"{url.rstrip('/')}/compare"


def _parse_sources(sources: list) -> list[SourceDoc]:
    parsed = []
    for s in sources:
        if isinstance(s, str):
            parsed.append(SourceDoc(title=s, source=s))
        elif isinstance(s, dict):
            parsed.append(SourceDoc(
                title=s.get("title", s.get("name", "Unknown")),
                source=s.get("source", s.get("url", s.get("path", ""))),
                section=s.get("section", s.get("page", None)),
            ))
    return parsed


async def call_rag_compare(request: AskRequest) -> AskCompareResponse:
    start = time.time()
    lang = _detect_language(request.question)

    image_analysis = None
    if request.image_base64 and request.image_mime:
        try:
            image_analysis = await _analyze_image(
                request.image_base64, request.image_mime, request.question, lang
            )
        except Exception:
            image_analysis = None

    history_payload = [
        {"role": m.role, "content": m.content}
        for m in (request.history or [])[-10:]
    ]

    if settings.use_mock:
        await asyncio.sleep(0.5)
        mock_results = []
        labels = {
            "product_rag": "Product Catalog RAG",
            "general_rag": "Agriculture Knowledge RAG",
            "base_llm": "Base LLM",
        }
        for mid, name in labels.items():
            single = _mock_response(
                AskRequest(question=request.question, model=mid, history=request.history),
                400,
                image_analysis,
            )
            mock_results.append(ModelCompareResult(
                model=mid,
                model_name=name,
                answer=single.answer,
                sources=single.sources,
                confidence=single.confidence,
                retrieved_chunks=single.retrieved_chunks,
                latency_ms=400,
            ))
        return AskCompareResponse(
            question=request.question,
            results=mock_results,
            latency_ms=int((time.time() - start) * 1000),
            detected_language=lang,
            image_analysis=image_analysis,
        )

    compare_url = _compare_url()
    if compare_url:
        try:
            payload = {
                "question": request.question,
                "history": history_payload,
            }
            if request.crop_type and request.crop_type != "all":
                payload["crop_type"] = request.crop_type
            if image_analysis:
                payload["image_analysis"] = image_analysis
            if request.image_base64 and request.image_mime:
                payload["image_base64"] = request.image_base64
                payload["image_mime"] = request.image_mime

            async with httpx.AsyncClient(timeout=settings.request_timeout * 3) as client:
                resp = await client.post(compare_url, json=payload)
                resp.raise_for_status()
                data = resp.json()

            results = []
            for row in data.get("results", []):
                answer = row.get("answer", "")
                if image_analysis and not any(
                    k in (answer or "") for k in ["Image Analysis", "تحليل الصورة"]
                ):
                    prefix = (
                        "**تحليل الصورة:**\n" if lang == "ar" else "**Image Analysis:**\n"
                    ) + image_analysis + "\n\n"
                    answer = prefix + answer

                results.append(ModelCompareResult(
                    model=row.get("model", ""),
                    model_name=row.get("model_name", row.get("model", "")),
                    answer=answer,
                    sources=_parse_sources(row.get("sources", [])),
                    confidence=row.get("confidence", "medium"),
                    retrieved_chunks=row.get("retrieved_chunks", 0),
                    latency_ms=row.get("latency_ms", 0),
                    error=row.get("error"),
                ))

            return AskCompareResponse(
                question=data.get("question", request.question),
                results=results,
                latency_ms=data.get("latency_ms", int((time.time() - start) * 1000)),
                detected_language=lang,
                image_analysis=image_analysis,
            )
        except Exception as e:
            logger.error("Compare RAG call failed (%s): %s", compare_url, e)
            if not settings.use_mock:
                error_results = [
                    ModelCompareResult(
                        model=mid,
                        model_name=mid,
                        answer="",
                        error=str(e),
                    )
                    for mid in ("product_rag", "general_rag", "base_llm")
                ]
                return AskCompareResponse(
                    question=request.question,
                    results=error_results,
                    latency_ms=int((time.time() - start) * 1000),
                    detected_language=lang,
                    image_analysis=image_analysis,
                )

    # Fallback: parallel single-model calls
    model_ids = ["product_rag", "general_rag", "base_llm"]
    names = {
        "product_rag": "Product Catalog RAG",
        "general_rag": "Agriculture Knowledge RAG",
        "base_llm": "Base LLM",
    }

    async def fetch_one(mid: str) -> ModelCompareResult:
        t0 = time.time()
        try:
            sub = AskRequest(
                question=request.question,
                model=mid,
                history=request.history,
                crop_type=request.crop_type,
                image_base64=request.image_base64,
                image_mime=request.image_mime,
            )
            res = await call_rag(sub)
            return ModelCompareResult(
                model=mid,
                model_name=names[mid],
                answer=res.answer,
                sources=res.sources,
                confidence=res.confidence,
                retrieved_chunks=res.retrieved_chunks,
                latency_ms=int((time.time() - t0) * 1000),
            )
        except Exception as ex:
            return ModelCompareResult(
                model=mid,
                model_name=names[mid],
                answer="",
                error=str(ex),
                latency_ms=int((time.time() - t0) * 1000),
            )

    results = await asyncio.gather(*[fetch_one(mid) for mid in model_ids])
    return AskCompareResponse(
        question=request.question,
        results=list(results),
        latency_ms=int((time.time() - start) * 1000),
        detected_language=lang,
        image_analysis=image_analysis,
    )
