import json
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI
from .models import ChunkItem
from .prompts import CLASSIFY_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_DEFAULTS = {
    "base_url": "http://localhost:11434/v1",
    "api_key": "ollama",
    "model": "qwen3:14b",
}

_client = None
_config = None


def resolve_llm_config(model_override: str | None = None) -> tuple[str, str, str]:
    """Resolve (base_url, api_key, model) with precedence: override > env > default."""
    base_url = os.environ.get("HARNESS_LLM_BASE_URL") or _DEFAULTS["base_url"]
    api_key = os.environ.get("HARNESS_LLM_API_KEY") or _DEFAULTS["api_key"]
    model = model_override or os.environ.get("HARNESS_LLM_MODEL") or _DEFAULTS["model"]
    return base_url, api_key, model


def set_llm_config(model_override: str | None = None) -> tuple[str, str, str]:
    global _config
    _config = resolve_llm_config(model_override)
    return _config


def _get_client():
    global _client
    if _client is None:
        base_url, api_key, _ = _config or resolve_llm_config()
        _client = OpenAI(base_url=base_url, api_key=api_key)
    return _client


def classify_chunk(chunk: dict, source_path: str) -> ChunkItem:
    client = _get_client()
    heading = chunk.get("heading_path", "")
    user_msg = f"Heading path: {heading}\n\nContent:\n{chunk['text']}"

    response = _call_llm(client, CLASSIFY_SYSTEM_PROMPT, user_msg)
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


def classify_chunks(chunks: list[dict], sources: list[str], max_workers: int = 4) -> list[ChunkItem]:
    """Classify section groups concurrently, returning results in submission order.

    Each chunk is paired with its source path by index, so results stay associated
    with the correct section group even when the pool finishes them out of order.
    `max_workers=1` reproduces today's sequential behavior.
    """
    if not chunks:
        return []
    results = [None] * len(chunks)
    with ThreadPoolExecutor(max_workers=max(1, max_workers)) as executor:
        futures = {
            executor.submit(classify_chunk, chunk, sources[i] if i < len(sources) else ""): i
            for i, chunk in enumerate(chunks)
        }
        for future, i in futures.items():
            results[i] = future.result()
    return results


def _max_tokens() -> int | None:
    """Optional output cap via HARNESS_MAX_TOKENS.

    Unset means "let the model decide", which is the historical behavior. Setting it
    bounds a thinking model that would otherwise ramble past the JSON answer, at the
    cost of truncating very large extractions.
    """
    raw = os.environ.get("HARNESS_MAX_TOKENS")
    if not raw:
        return None
    try:
        limit = int(raw)
    except ValueError:
        logger.warning("HARNESS_MAX_TOKENS invalido (%r); ignorando", raw)
        return None
    return limit if limit > 0 else None


def _call_llm(client, system_prompt: str, user_msg: str):
    _, _, model = _config or resolve_llm_config()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg},
    ]
    limit = _max_tokens()
    extra = {"max_tokens": limit} if limit else {}
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
            **extra,
        )
        return response
    except Exception as e:
        logger.warning("LLM call failed, retrying: %s", e)
        time.sleep(1)
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            **extra,
        )
        return response


_SECTIONS = {
    "specs": ["requirements", "acceptance_criteria", "data_models", "business_rules"],
    "loop_engineering": ["automation_triggers", "verification_points", "feedback_loops"],
    "harness_engineering": ["context_rules", "validation_gates", "tool_requirements"],
}

_KEY_FOR = {
    "requirements": "description",
    "acceptance_criteria": "description",
    "business_rules": "rule",
    "data_models": "name",
    "automation_triggers": "trigger",
    "verification_points": "output",
    "feedback_loops": "loop",
    "context_rules": "rule",
    "validation_gates": "gate",
    "tool_requirements": "tool",
}

_ID_PREFIX = {
    "requirements": "REQ",
    "acceptance_criteria": "AC",
    "business_rules": "BR",
    "data_models": "DM",
}

_SUMMARY = {
    "specs": "Requisitos, critérios de aceitação, regras de negócio e modelos de dados extraídos do documento",
    "loop_engineering": "Gatilhos de automação, pontos de verificação e loops de feedback extraídos do documento",
    "harness_engineering": "Regras de contexto, gates de validação e ferramentas recomendadas extraídos do documento",
}


def merge_items(chunk_items: list[ChunkItem]) -> dict:
    """Lossless programmatic merge: keep every item, dedup by exact text, assign stable ids."""
    sections = {"specs": {}, "loop_engineering": {}, "harness_engineering": {}}

    for item in chunk_items:
        body = item.items if isinstance(item.items, dict) else {}
        for section, cats in _SECTIONS.items():
            src_section = body.get(section, {}) if isinstance(body.get(section), dict) else {}
            for cat in cats:
                rows = []
                for row in (src_section.get(cat) if isinstance(src_section.get(cat), list) else []):
                    if not isinstance(row, dict):
                        continue
                    row = dict(row)
                    row.setdefault("source", item.source)
                    rows.append(row)
                sections[section].setdefault(cat, []).extend(rows)

    for section, cats in _SECTIONS.items():
        for cat in cats:
            rows = _dedup(sections[section].get(cat, []), _KEY_FOR[cat])
            if cat in ("business_rules", "acceptance_criteria"):
                rows = _dedup_by_id(rows)
            for i, row in enumerate(rows, start=1):
                prefix = _ID_PREFIX.get(cat)
                if prefix and not row.get("id"):
                    row["id"] = f"{prefix}-{i:02d}"
                row["source"] = row.get("source", "unknown")
            sections[section][cat] = rows

        counts = {cat: len(sections[section].get(cat, [])) for cat in cats}
        parts = ", ".join(f"{n} {cat}" for cat, n in counts.items() if n)
        sections[section]["summary"] = _SUMMARY[section] + (f" ({parts})" if parts else "")

    return sections


def _dedup(rows: list[dict], key: str) -> list[dict]:
    by_key = {}
    order = []
    for row in rows:
        k = re.sub(r"\s+", " ", str(row.get(key, ""))).strip().lower()
        if not k:
            order.append(row)
            continue
        if k not in by_key:
            by_key[k] = {"row": row, "sources": [row["source"]] if row.get("source") else []}
            order.append(by_key[k])
        else:
            src = row.get("source")
            if src and src not in by_key[k]["sources"]:
                by_key[k]["sources"].append(src)

    out = []
    for entry in order:
        if isinstance(entry, dict) and "row" in entry:
            row = dict(entry["row"])
            if entry["sources"]:
                row["source"] = "; ".join(entry["sources"])
            out.append(row)
        else:
            out.append(entry)
    return out


def _dedup_by_id(rows: list[dict]) -> list[dict]:
    """Collapse rows sharing the same natural id (e.g. RQ07-RN03), merging their sources."""
    seen = {}
    out = []
    for row in rows:
        rid = row.get("id")
        if rid and rid in seen:
            src = row.get("source")
            if src and src not in seen[rid].get("source", ""):
                seen[rid]["source"] = f"{seen[rid]['source']}; {src}"
            continue
        if rid:
            seen[rid] = row
        out.append(row)
    return out


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
