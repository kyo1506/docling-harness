# Tasks: Dedupe Spec Extraction

## 1. Section grouping fix

- [x] 1.1 Update `group_chunks` in `chunker.py` to start a new group only when the heading is a section heading *different* from the current group's heading; non-section headings always append, so consecutive same-section fragments merge into one group
- [x] 1.2 Add a test asserting consecutive chunks with the same `7.N RQxx` heading collapse into a single group (49 → ~26 groups behavior)

## 2. Deterministic-first dedup

- [x] 2.1 Extend `merge_deterministic` in `rules_extractor.py` to also drop LLM business rules and acceptance criteria that are near-duplicates of a deterministic item (normalized token overlap, no id required), preferring the verbatim text
- [x] 2.2 Add a test that an id-less LLM paraphrase of an existing verbatim rule is dropped while a distinct section-8 table rule is kept

## 3. Requirements from section headings

- [x] 3.1 Add a `requirements_from_headings(heading_path, source)` helper in `rules_extractor.py` that derives one requirement per `7.N RQxx: <TITLE>` heading (regex `\d+\.\d+\s+RQ\d+:\s*(.+)`) with id `RQxx` and a fallback to the first rule's RQ prefix when no heading matches
- [x] 3.2 In `cli.py`, replace LLM-provided requirements with the heading-derived requirements for each section group before appending to `all_chunk_items`
- [x] 3.3 Add a test that a document with 19 numbered requirement sections plus changelog/scope text yields exactly 19 requirements

## 4. Section traceability for LLM items

- [x] 4.1 In `cli.py`, set each classified item's source to `f"file:{src}§{heading}"` so LLM items carry the same section reference as deterministic items
- [x] 4.2 Add a test asserting an LLM-classified item's source includes the section heading

## 5. Language pinning and metric

- [x] 5.1 Add "Respond in the same language as the document content." to `CLASSIFY_SYSTEM_PROMPT` in `prompts.py`
- [x] 5.2 Update the CLI log line in `cli.py` to report a negative `reduction_pct` as growth rather than reduction (value stays signed)
- [x] 5.3 Add a test asserting `compute_comparison` yields a negative `reduction_pct` when processed > raw

## 6. Verification

- [x] 6.1 Run `python tests/test_pipeline.py` — all tests pass
- [x] 6.2 Run `harness sources/` against the Prodesp spec PDF and verify `harness.json` has ~19 requirements (no changelog/scope entries), no duplicate `RQxx-CAxx`/`RQxx-RNxx` ids, no English paraphrases, and `_meta.merge_mode` still `lossless_programmatic`
