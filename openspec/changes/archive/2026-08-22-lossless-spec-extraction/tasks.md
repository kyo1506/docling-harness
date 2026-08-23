# Tasks: Lossless Spec Extraction

## 1. Deterministic rule extraction

- [x] 1.1 Create `src/docling_harness/rules_extractor.py` with a `structured_extract(text: str, heading_path: str, source: str) -> dict` that regex-captures business rules (`RQxx-RNxx`, `RQxx-RQxx`, standalone `RNxx`) and acceptance criteria (`RQxx-CAxx`) with verbatim body text including continuation bullets, normalizing `-`/`–` separators and skipping page-header/footer noise
- [x] 1.2 Return items in the classified shape (`specs.business_rules`, `specs.acceptance_criteria`) with the rule id preserved and a source field from `heading_path`

## 2. Section-grouped chunking

- [x] 2.1 Add `group_chunks(chunks) -> list[dict]` to `chunker.py` that reassembles hierarchical fragments into top-level numbered-section groups (each `7.N RQxx`, sections 8/9/10, front matter), absorbing running-header fragments into the current section and dropping fragments <40 chars with no rule/criterion pattern

## 3. Lossless merge

- [x] 3.1 In `classifier.py`, replace `fallback_merge` with `merge_items(chunk_items)` that concatenates every item, dedups by exact text across all categories, assigns stable ids (`REQ-01`, `AC-01`, `BR-01`, `DM-01`) and writes count-based `summary` per category; delete `merge_results` and `_build_merge_payload`
- [x] 3.2 Update `merger.py` `merge()` to call `merge_items()` only, drop the LLM merge import, and set `_meta["merge_mode"] = "lossless_programmatic"` (remove `merge_fallback` semantics)
- [x] 3.3 Fix `ChunkItem.items` type annotation in `models.py` from `list[dict]` to `dict`

## 4. Pipeline wiring

- [x] 4.1 In `cli.py`, call `group_chunks` after chunking; for each section group run the LLM classifier, run `structured_extract` on the same text, and union the results (dedup by rule id, preferring exact extracted text) before appending to `all_chunk_items`
- [x] 4.2 Update `cli.py` log line to report section-group counts instead of raw chunk indices

## 5. Tests and verification

- [x] 5.1 Add tests to `tests/test_pipeline.py`: `structured_extract` captures multi-line rules and criteria verbatim; `group_chunks` yields one group per RQ section and drops noise; `merge_items` preserves all items with stable ids and exact-text dedup
- [x] 5.2 Run `python tests/test_pipeline.py` — all tests pass
- [x] 5.3 Run `harness sources/` against the Prodesp spec PDF and verify `harness.json` contains all 19 RQs' rules and criteria (spot-check RQ01 and RQ15) and `_meta.merge_mode` is set
