import json
from token_count import TokenCount
from .models import CostComparison

tc = TokenCount(model_name="gpt-3.5-turbo")


def count_tokens(text: str) -> int:
    return tc.num_tokens_from_string(text)


def compute_comparison(raw_text: str, processed_json: dict) -> CostComparison:
    raw = count_tokens(raw_text)
    processed = count_tokens(json.dumps(processed_json, ensure_ascii=False))
    reduction = (1 - processed / raw) * 100 if raw > 0 else 0.0
    break_even = 1 if processed < raw else 999
    return CostComparison(
        raw_tokens=raw,
        processed_tokens=processed,
        reduction_pct=round(reduction, 1),
        break_even_queries=break_even,
    )
