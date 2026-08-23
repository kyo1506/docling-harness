## Why

The harness loses nearly all rules and validations from dense spec documents. Running `harness sources/` on the Prodesp "Recad Personalizado" spec (51 pages, 19 RQs RQ01–RQ19, dozens of `RQxx-RNxx` business rules and `RQxx-CAxx` acceptance criteria) produced only 2 requirements, 5 business rules, and 2 acceptance criteria — all fragments of RQ15-17. Diagnosis: the LLM merge step is a single lossy consolidation call over ~139 classified items; a 14B model drops or empties almost everything. Reproduced: 12 chunks classified (17 rules, 15 criteria, 36 requirements) → LLM merge returned 0 items. The 96.4% "token reduction" is destroyed content, not noise removal.

## What Changes

- **Merge becomes lossless** — replace the LLM-based merge with a programmatic concatenation + dedup that keeps every classified item. The LLM merge path (`merge_results`, `_build_merge_payload`) is removed. Items get generated ids (`REQ-01`, `AC-01`, `BR-01`, `DM-01`, …) and per-category summaries are produced programmatically. `_meta` reports `merge_mode: "lossless_programmatic"` instead of `merge_fallback`.
- **Deterministic rule extraction** — a new regex-based extractor captures structured business rules (`RQxx-RNxx`, `RQxx-RQxx`, `RNxx`) and acceptance criteria (`RQxx-CAxx`) with exact source text, guaranteed complete where the LLM paraphrases or omits. Results are unioned with LLM classification per chunk, deduped by rule id, preferring exact text.
- **Section-grouped chunking** — chunk fragments are reassembled into document-section super-chunks (each `7.N RQxx` section, section 8 validation table, glossary, traceability matrix) before classification, so each LLM call sees a coherent section instead of a torn fragment. Noise chunks (<40 chars, no rule pattern) are dropped. Cuts classification calls from ~139 to ~25.
- **Completeness over compression** — for dense spec documents the processed token count rises and `reduction_pct` becomes modest; that is correct, the document itself is rules. No behavior change for sparse documents.

## Capabilities

### New Capabilities
- `rule-extraction`: Deterministically extracts structured business rules (`RN`) and acceptance criteria (`CA`) from spec document text with exact source text, guaranteeing completeness independent of LLM classification.

### Modified Capabilities
- `context-generation`: Chunking now groups fragments into document sections before classification; classification is augmented by deterministic rule extraction; the merge step is lossless programmatic concatenation with id assignment instead of lossy LLM consolidation.

## Impact

- **Code**: `src/docling_harness/merger.py` (lossless merge), `classifier.py` (remove LLM merge, improve `fallback_merge` → `merge_items`), new `src/docling_harness/rules_extractor.py`, `chunker.py` (add `group_chunks`), `cli.py` (wire section grouping + rule extraction + union), `models.py` (fix `ChunkItem.items` type).
- **Output**: `harness.json` grows to include all extracted rules/criteria; ids and programmatic summaries replace LLM summaries; `_meta` gains `merge_mode`.
- **Dependencies**: none added; deterministic extraction uses stdlib `re`.
- **Performance**: fewer LLM calls per document (section grouping), one expensive merge call eliminated.
- **Tests**: `tests/test_pipeline.py` gains coverage for the regex extractor, section grouping, and lossless merge.
