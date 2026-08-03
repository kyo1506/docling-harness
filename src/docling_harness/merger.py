import logging
from .classifier import merge_results as _llm_merge, fallback_merge
from .models import ChunkItem, HarnessOutput

logger = logging.getLogger(__name__)

_EXPECTED_KEYS = {"specs", "loop_engineering", "harness_engineering"}


def merge(chunk_items: list[ChunkItem]) -> HarnessOutput:
    merged = _llm_merge(chunk_items)
    meta = {}

    for key in _EXPECTED_KEYS:
        val = merged.get(key)
        if not isinstance(val, dict) or not val:
            logger.warning("Merge response missing or empty key: %s", key)
            merged[key] = {}

    has_content = any(
        isinstance(merged.get(k), dict) and merged[k]
        for k in _EXPECTED_KEYS
    )

    if not has_content:
        logger.error("LLM merge produced no content, falling back to programmatic merge")
        merged = fallback_merge(chunk_items)
        meta["merge_fallback"] = True

    return HarnessOutput(
        meta=meta,
        specs=merged.get("specs", {}),
        loop_engineering=merged.get("loop_engineering", {}),
        harness_engineering=merged.get("harness_engineering", {}),
    )
