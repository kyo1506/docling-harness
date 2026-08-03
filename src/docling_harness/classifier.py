import json
import logging
import time
from openai import OpenAI
from .models import ChunkItem
from .prompts import CLASSIFY_SYSTEM_PROMPT, MERGE_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama",
        )
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


def _build_merge_payload(chunk_items: list[ChunkItem], max_chars: int = 100000) -> tuple[str, int]:
    all_items = [item.items for item in chunk_items]
    payload = json.dumps(all_items, indent=2, ensure_ascii=False)

    if len(payload) <= max_chars:
        return payload, 0

    cutoff = payload.rfind("\n  }", 0, max_chars)
    if cutoff == -1:
        cutoff = payload.rfind("\n}", 0, max_chars)

    if cutoff != -1:
        payload = payload[:cutoff + 4]  # include "\n  }"

    payload = payload.rstrip().rstrip(",") + "\n]"
    omitted = len(all_items) - (payload.count("\n  {") if payload.count("\n  {") > 0 else 1)
    return payload, max(0, omitted)


def merge_results(chunk_items: list[ChunkItem]) -> dict:
    client = _get_client()

    payload, omitted = _build_merge_payload(chunk_items)
    user_msg = f"Classified items from all chunks:\n{payload}\n\nConsolidate into final output."
    if omitted > 0:
        user_msg += f"\n(Note: {omitted} out of {len(chunk_items)} classified items were omitted due to size limits.)"

    response = _call_llm(client, MERGE_SYSTEM_PROMPT, user_msg)
    return _safe_parse(response)


def _call_llm(client, system_prompt: str, user_msg: str):
    try:
        response = client.chat.completions.create(
            model="mistral:7b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
        )
        return response
    except Exception as e:
        logger.warning("LLM call failed, retrying: %s", e)
        time.sleep(1)
        response = client.chat.completions.create(
            model="mistral:7b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
        )
        return response


def fallback_merge(chunk_items: list[ChunkItem]) -> dict:
    specs = {"summary": "Programmatic merge (LLM merge failed)", "requirements": [], "acceptance_criteria": [], "data_models": [], "business_rules": []}
    loop = {"summary": "Programmatic merge (LLM merge failed)", "automation_triggers": [], "verification_points": [], "feedback_loops": []}
    harness = {"summary": "Programmatic merge (LLM merge failed)", "context_rules": [], "validation_gates": [], "tool_requirements": []}

    seen_reqs = set()
    seen_rules = set()
    for item in chunk_items:
        chunk_specs = item.items.get("specs", {}) if isinstance(item.items, dict) else {}
        chunk_loop = item.items.get("loop_engineering", {}) if isinstance(item.items, dict) else {}
        chunk_harness = item.items.get("harness_engineering", {}) if isinstance(item.items, dict) else {}

        for req in chunk_specs.get("requirements", []):
            key = req.get("description", "")
            if key and key not in seen_reqs:
                seen_reqs.add(key)
                req["source"] = req.get("source", item.source)
                specs["requirements"].append(req)

        for ac in chunk_specs.get("acceptance_criteria", []):
            specs["acceptance_criteria"].append(ac)

        for dm in chunk_specs.get("data_models", []):
            specs["data_models"].append(dm)

        for rule in chunk_specs.get("business_rules", []):
            key = rule.get("rule", "")
            if key and key not in seen_rules:
                seen_rules.add(key)
                rule["source"] = rule.get("source", item.source)
                specs["business_rules"].append(rule)

        for trig in chunk_loop.get("automation_triggers", []):
            loop["automation_triggers"].append(trig)

        for vp in chunk_loop.get("verification_points", []):
            loop["verification_points"].append(vp)

        for fb in chunk_loop.get("feedback_loops", []):
            loop["feedback_loops"].append(fb)

        for cr in chunk_harness.get("context_rules", []):
            harness["context_rules"].append(cr)

        for gate in chunk_harness.get("validation_gates", []):
            harness["validation_gates"].append(gate)

        for tool in chunk_harness.get("tool_requirements", []):
            harness["tool_requirements"].append(tool)

    return {"specs": specs, "loop_engineering": loop, "harness_engineering": harness}


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
