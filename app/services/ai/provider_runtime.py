from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from typing import Any, Dict, Optional

import httpx

from config.settings import settings

logger = logging.getLogger(__name__)

DEFAULT_VECTOR_DIMENSION = 1536
DEFAULT_SCORE = 0.92


def _is_openai_enabled() -> bool:
    return settings.AI_PROVIDER.lower() == "openai" and bool(settings.OPENAI_API_KEY.strip())


def _normalize_score(value: Any, default: float = DEFAULT_SCORE) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        score = default
    return max(0.0, min(1.0, score))


def _normalize_vector(values: list[float], dimensions: int) -> list[float]:
    if len(values) == dimensions:
        return values
    if len(values) > dimensions:
        return values[:dimensions]
    return values + ([0.0] * (dimensions - len(values)))


def _deterministic_vector(content: str, dimensions: int) -> list[float]:
    seed = hashlib.sha256(content.encode("utf-8")).digest()
    values: list[float] = []
    state = seed
    while len(values) < dimensions:
        for byte_value in state:
            values.append((byte_value / 127.5) - 1.0)
            if len(values) >= dimensions:
                break
        state = hashlib.sha256(state + seed).digest()
    return values


def _mock_agent_response(
    input_data: Optional[Dict[str, Any]],
    *,
    agent_name: str,
    stage_type: Optional[str],
) -> Dict[str, Any]:
    stage_label = stage_type or "unknown"
    context_keys = sorted((input_data or {}).keys())
    return {
        "mode": "mock",
        "summary": f"{agent_name} processed stage {stage_label}.",
        "highlights": [f"context_keys={','.join(context_keys) or 'none'}"],
        "score": DEFAULT_SCORE,
    }


async def _call_openai_embeddings(content: str) -> Optional[list[float]]:
    if not _is_openai_enabled():
        return None

    payload = {
        "model": settings.OPENAI_EMBEDDING_MODEL,
        "input": content,
    }
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    url = f"{settings.OPENAI_BASE_URL.rstrip('/')}/embeddings"
    max_retries = 3
    base_delay = 1.0

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=settings.AI_REQUEST_TIMEOUT_SECONDS,
                )
            response.raise_for_status()
            data = response.json()
            raw_vector = data["data"][0]["embedding"]
            vector = [float(x) for x in raw_vector]
            return _normalize_vector(vector, DEFAULT_VECTOR_DIMENSION)
        except Exception as exc:  # pragma: no cover
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning("OpenAI embedding call failed (attempt %d/%d): %s. Retrying in %ss...", attempt + 1, max_retries, exc, delay)
                await asyncio.sleep(delay)
            else:
                logger.warning("OpenAI embedding call failed after %d retries; using deterministic fallback: %s", max_retries, exc)
                return None
    return None


async def generate_embedding_vector(content: str, dimensions: int = DEFAULT_VECTOR_DIMENSION) -> list[float]:
    vector = await _call_openai_embeddings(content)
    if vector is not None:
        return _normalize_vector(vector, dimensions)
    return _normalize_vector(_deterministic_vector(content, dimensions), dimensions)


async def _call_openai_agent_response(
    input_data: Optional[Dict[str, Any]],
    *,
    agent_name: str,
    stage_type: Optional[str],
) -> Optional[Dict[str, Any]]:
    if not _is_openai_enabled():
        return None

    prompt_payload = {
        "agent_name": agent_name,
        "stage_type": stage_type,
        "context": input_data or {},
    }
    messages = [
        {
            "role": "system",
            "content": (
                "You are a startup execution assistant. Return concise actionable output "
                "and include a numeric 'score' between 0 and 1."
            ),
        },
        {"role": "user", "content": json.dumps(prompt_payload, ensure_ascii=True)},
    ]
    payload = {
        "model": settings.OPENAI_CHAT_MODEL,
        "messages": messages,
        "temperature": 0.2,
    }
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    url = f"{settings.OPENAI_BASE_URL.rstrip('/')}/chat/completions"
    max_retries = 3
    base_delay = 1.0

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=settings.AI_REQUEST_TIMEOUT_SECONDS,
                )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise ValueError("OpenAI response content is empty")

            try:
                parsed = json.loads(content)
                output: Dict[str, Any] = parsed if isinstance(parsed, dict) else {"summary": str(parsed)}
            except json.JSONDecodeError:
                output = {"summary": content.strip()}

            output.setdefault("mode", "openai")
            output["score"] = _normalize_score(output.get("score"))
            return output
        except Exception as exc:  # pragma: no cover
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning("OpenAI agent call failed (attempt %d/%d): %s. Retrying in %ss...", attempt + 1, max_retries, exc, delay)
                await asyncio.sleep(delay)
            else:
                logger.warning("OpenAI agent call failed after %d retries; using mock fallback: %s", max_retries, exc)
                return None
    return None


async def run_agent_execution(
    input_data: Optional[Dict[str, Any]],
    *,
    agent_name: str,
    stage_type: Optional[str],
) -> Dict[str, Any]:
    output = await _call_openai_agent_response(
        input_data,
        agent_name=agent_name,
        stage_type=stage_type,
    )
    if output is not None:
        return output
    return _mock_agent_response(input_data, agent_name=agent_name, stage_type=stage_type)
