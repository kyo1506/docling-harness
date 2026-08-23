from .classifier import merge_items
from .models import ChunkItem, HarnessOutput


def merge(chunk_items: list[ChunkItem]) -> HarnessOutput:
    merged = merge_items(chunk_items)
    return HarnessOutput(
        meta={"merge_mode": "lossless_programmatic"},
        specs=merged.get("specs", {}),
        loop_engineering=merged.get("loop_engineering", {}),
        harness_engineering=merged.get("harness_engineering", {}),
    )
