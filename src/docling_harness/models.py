from dataclasses import dataclass, field


@dataclass
class ChunkItem:
    category: str
    items: dict
    source: str
    model_used: str
    tokens_used: int = 0


@dataclass
class CostComparison:
    raw_tokens: int
    processed_tokens: int
    reduction_pct: float
    break_even_queries: int
    processing_cost_usd: float = 0.0


@dataclass
class HarnessOutput:
    meta: dict = field(default_factory=dict)
    specs: dict = field(default_factory=dict)
    loop_engineering: dict = field(default_factory=dict)
    harness_engineering: dict = field(default_factory=dict)
