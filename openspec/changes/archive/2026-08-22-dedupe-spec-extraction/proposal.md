## Why

The `lossless-spec-extraction` change fixed completeness but over-corrected: `harness.json` now ballooned to 2.5x the source (44K vs 17K tokens) for dense spec documents. Root-cause analysis found three compounding problems — (1) `group_chunks` opens a new group for every chunk carrying a section heading, even consecutive fragments of the same section, producing 49 groups instead of ~26 and duplicate captures of the same rule across groups; (2) the LLM re-extracts and paraphrases rules the deterministic extractor already captured verbatim, and those id-less paraphrases (some in English) survive the merge; (3) the LLM dumps changelog lines, scope/premise text, and literal rule echoes into `requirements`, yielding 92 items for a document with 19 real RQs. The result is 343 spec items of which ~108 are pure redundancy and ~65 are noise, LLM items lacking section traceability, and a misleading `-156%` "reduction" metric.

## What Changes

- **Merge consecutive same-section fragments** — `group_chunks` starts a new group only when the section heading *changes*, collapsing story/rule/criteria fragments of the same `7.N RQxx` section into one group (49 → ~26 groups).
- **Deterministic extraction is the source of truth for structured RN/CA** — LLM business rules and acceptance criteria are deduplicated against the verbatim deterministic items (by rule id and near-duplicate text), so redundant paraphrases are dropped and the verbatim text wins. The LLM contributes only what the regex cannot capture (section-8 tables, data models, loop/harness).
- **Requirements derived from section headings** — requirements come from `7.N RQxx` section headings (19 clean items) rather than 92 noisy LLM classifications; changelog, scope, premise, and story fragments are filtered out.
- **Section traceability on every item** — LLM-classified items inherit the section heading of their group, matching the deterministic items' `source` form (`file:...pdf§7.1 RQ01`).
- **Honest cost comparison** — `reduction_pct` is reported as a signed value reflecting actual size change, without implying savings when the processed output exceeds the raw input.
- **Document-language pinning** — the classification prompt instructs the model to respond in the document's language.

## Capabilities

### New Capabilities
<!-- none: this is a refinement of existing capabilities -->

### Modified Capabilities
- `context-generation`: chunking merges consecutive same-section fragments; classification is deterministic-first for structured RN/CA with requirements derived from headings and noise filtered; the merge deduplicates LLM paraphrases against verbatim items.
- `token-comparison`: the cost comparison reports an accurate signed reduction and does not present output growth as savings.

## Impact

- **Code**: `src/docling_harness/chunker.py` (`group_chunks` same-heading merge), `rules_extractor.py` (deterministic-first dedup helper, requirements-from-headings extraction), `classifier.py` (dedup LLM items against verbatim at merge; language pinning), `cli.py` (wiring), `token_counter.py` (signed reduction).
- **Output**: `harness.json` shrinks from ~343 to ~170 spec items with no loss of completeness; English paraphrases removed; all items carry section traceability.
- **Performance**: fewer LLM calls (~26 vs 49) from section merging.
- **Dependencies**: none added.
- **Tests**: `tests/test_pipeline.py` gains coverage for same-heading merge, deterministic-first dedup, requirements-from-headings, and the signed reduction metric.
