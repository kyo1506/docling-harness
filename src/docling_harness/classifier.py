import json
import logging
import os
import time
from openai import OpenAI
from .models import ChunkItem
from .prompts import CLASSIFY_SYSTEM_PROMPT, MERGE_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            default_headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-OpenRouter-Title": "Docling Harness",
            },
        )
    return _client


def classify_chunk(chunk: dict, source_path: str, sort: str = "throughput") -> ChunkItem:
    client = _get_client()
    heading = chunk.get("heading_path", "")
    user_msg = f"Heading path: {heading}\n\nContent:\n{chunk['text']}"

    response = _call_llm(client, CLASSIFY_SYSTEM_PROMPT, user_msg, sort)
    body = _safe_parse(response)
    model_used = response.model if response else "unknown"
    tokens_used = response.usage.total_tokens if response and response.usage else 0

    return ChunkItem(
        category="classified",
        items=body,
        source=f"file:{source_path}",
        model_used=model_used,
        tokens_used=tokens_used,
    )


def merge_results(chunk_items: list[ChunkItem], sort: str = "throughput") -> dict:
    client = _get_client()
    all_items = []
    for item in chunk_items:
        all_items.append(item.items)

    payload = json.dumps(all_items, indent=2, ensure_ascii=False)
    if len(payload) > 30000:
        payload = payload[:30000]

    user_msg = f"Classified items from all chunks:\n{payload}\n\nConsolidate into final output."
    response = _call_llm(client, MERGE_SYSTEM_PROMPT, user_msg, sort)
    return _safe_parse(response)


def _call_llm(client, system_prompt: str, user_msg: str, sort: str):
    try:
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
            extra_body={
                "provider": {
                    "sort": sort,
                    "require_parameters": True,
                }
            },
        )
        return response
    except Exception as e:
        logger.warning("LLM call failed, retrying: %s", e)
        time.sleep(1)
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            extra_body={
                "provider": {
                    "sort": sort,
                    "require_parameters": True,
                }
            },
        )
        return response


def _safe_parse(response) -> dict:
    if response is None:
        return {}
    content = response.choices[0].message.content
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        if content.startswith("```json"):
            content = content.split("```json")[1].split("```")[0].strip()
        elif content.startswith("```"):
            content = content.split("```")[1].strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM response as JSON")
            return {}
