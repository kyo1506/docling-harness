# Design: Lossless Spec Extraction

## Context

See proposal.md for motivation. Current pipeline (cli.py): docling extract → `HierarchicalChunker` (chunker.py) → per-chunk LLM classification (classifier.py) → LLM merge (classifier.py `merge_results`, merger.py) → output. Verified failure: per-chunk classification works (extracts RN/CA correctly), but the LLM merge drops nearly everything (12-item subset → 0 items out) and the chunker tears each RQ into ~7 fragments. Specs: `context-generation` (chunking/classification/merge) and new `rule-extraction` (deterministic RN/CA capture) — see `specs/`.

## Goals / Non-Goals

**Goals:**
- Zero loss of classified items through the merge step.
- Complete, verbatim capture of structured `RN`/`CA` rules independent of LLM quality.
- Coherent per-section inputs to the LLM classifier.
- Deterministic output (same input → same ids, counts, summaries).

**Non-Goals:**
- No semantic dedup of similar-but-not-identical rules (kept as separate items).
- No change to docling extraction or token comparison mechanics.
- No changes to sparse/generic documents' behavior beyond the merge path.

## Decisions

### 1. Merge is purely programmatic and lossless
`merger.py` calls a single `merge_items()` that concatenates every classified item, dedups by exact text, assigns ids (`REQ-01`, `AC-01`, `BR-01`, `DM-01`), and writes count-based `summary` strings. The LLM merge (`merge_results`, `_build_merge_payload`) is deleted.
- *Alternative considered:* keep the LLM merge but raise `max_tokens` and forbid dropping items. Rejected — a 14B model cannot reliably consolidate 139 items without loss; empirically returned empty output on a 12-item subset. Nondeterministic.

### 2. Deterministic regex extraction for structured rules (`rule-extraction`)
New `rules_extractor.py` (stdlib `re` only). Patterns on raw section text:
- rule id: `(RQ\d+-(?:RN|RQ)\d+|RN\d+)`
- criterion id: `RQ\d+-CA\d+`
- body: capture from the marker through continuation lines (`- o ...`, wrapped lines) until the next marker, joining lines; normalize `–`/`-` separators; strip page-header/footer noise lines.
Per group, extracted items are unioned with the LLM items, deduplicated by rule id, **preferring the exact extracted text**.
- *Alternative considered:* rely on the LLM alone. Rejected — it paraphrases and omits (RQ01 lost `RN04`; RQ15 collapsed 3 rules to 1 in testing).

### 3. Section-grouped chunking
`chunker.py` gains `group_chunks()`: after hierarchical chunking, fragments are reassembled by top-level numbered heading (each `7.N RQxx`, section `8`, `9`, `10`, front matter) — fragments under the running page-header heading are absorbed into the current section; fragments <40 chars with no rule pattern are dropped. Output is ~25 section groups instead of 139 fragments, each classified as one unit.
- *Alternative considered:* keep the raw HierarchicalChunker output. Rejected — RQ sections are fragmented (user story split across chunks, RN list separated from CA list, rule bullets split by header rows), destroying context for classification.

### 4. Programmatic summaries
`merge_items()` writes `summary` per category as counts ("N requisitos, M regras de negócio, K critérios de aceitação").
- *Alternative considered:* a summary-only LLM call. Rejected — one more LLM call for marginal value; counts are deterministic and adequate for the AGENTS.md index.

### 5. Union ordering and id stability
Per group, deterministic `RN`/`CA` items are appended first, then LLM items that are not exact-text duplicates, so ids remain stable regardless of LLM output order.

## Risks / Trade-offs

- **[Output grows for dense specs]** `reduction_pct` in `_meta` drops (document is mostly rules) → This is intended completeness, not waste; token comparison reports the honest number.
- **[Regex misses irregular formatting]** Rules that break the `- <id> -` bullet pattern (e.g., nested tables in section 8) are still captured only via the LLM path → LLM classification is kept for those sections; regex is a floor, not the only source.
- **[Duplicate rules across RQ sections kept]** The parent/child accordion rule recurs in RQ07–12 as separate `RQxx-RNxx` items → kept deliberately per spec; semantic dedup is out of scope.
- **[Runs slower per classification call]** Larger section inputs to the LLM → fewer calls total (~25 vs 139); net faster, no per-call size concern within a 14B context.
