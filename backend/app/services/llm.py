import json

import httpx

from app.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from app.schemas import DailyBriefing


def llm_status() -> dict:
    configured = bool(OPENAI_API_KEY)
    message = (
        "OpenAI LLM reasoning is configured."
        if configured
        else "Set OPENAI_API_KEY in backend/.env to enable the optional LLM reasoning layer."
    )
    return {"available": configured, "model": OPENAI_MODEL, "message": message}


async def improve_answer_with_llm(
    question: str,
    base_answer: dict,
    briefing: DailyBriefing,
    groceries: list[dict],
    expenses: dict,
    budget: dict,
) -> dict:
    if not OPENAI_API_KEY:
        return base_answer

    context = {
        "question": question,
        "intent": base_answer["intent"],
        "rule_based_answer": base_answer["answer"],
        "weather": briefing.weather.model_dump(),
        "schedule": briefing.schedule,
        "outfit": [item.model_dump() for item in briefing.outfit_details],
        "meals": [item.model_dump() for item in briefing.meal_details],
        "shopping": briefing.shopping,
        "alerts": briefing.alerts,
        "groceries": groceries[:30],
        "expenses": expenses,
        "budget": budget,
    }
    prompt = (
        "You are Jarvis, a concise personal student-life assistant. "
        "Answer using only the provided context. Do not invent calendar events, groceries, weather, or expenses. "
        "If the context is missing something, say what is missing. Keep the answer natural and speakable for Alexa."
    )

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{OPENAI_BASE_URL}/responses",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": OPENAI_MODEL,
                    "input": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": json.dumps(context, ensure_ascii=True)},
                    ],
                    "max_output_tokens": 350,
                },
            )
            response.raise_for_status()
    except httpx.HTTPError:
        return base_answer

    answer = _extract_output_text(response.json())
    if not answer:
        return base_answer
    improved = base_answer.copy()
    improved["answer"] = answer.strip()
    improved["source"] = "openai_llm"
    return improved


def _extract_output_text(payload: dict) -> str | None:
    if payload.get("output_text"):
        return payload["output_text"]

    chunks: list[str] = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if text:
                chunks.append(text)
    return " ".join(chunks) if chunks else None
