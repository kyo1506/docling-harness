from .classifier import merge_results as _llm_merge
from .models import ChunkItem, HarnessOutput
from .prompts import MERGE_SYSTEM_PROMPT


def merge(chunk_items: list[ChunkItem], sort: str = "throughput") -> HarnessOutput:
    merged = _llm_merge(chunk_items, sort)

    specs = merged.get("specs", {})
    loop = merged.get("loop_engineering", {})
    harness = merged.get("harness_engineering", {})

    return HarnessOutput(
        meta={},
        specs=specs,
        loop_engineering=loop,
        harness_engineering=harness,
    )
