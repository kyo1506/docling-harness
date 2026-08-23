# Design: Dedupe Spec Extraction

## Context

Builds on `lossless-spec-extraction` (un-archived): that change made extraction complete — all 19 RQs' rules/criteria captured verbatim — but left the LLM competing with the deterministic extractor, producing a `harness.json` 2.5x the source with ~108 redundant items and ~65 noise items. This change refines the same pipeline. Archive `lossless-spec-extraction` before this one; both MODIFY `context-generation`.

## Goals / Non-Goals

**Goals:**
- One section group per `7.N RQxx` (no fragmentation).
- Deterministic verbatim rules/criteria as the single source of truth; LLM paraphrases dropped.
- 19 clean requirements from section headings, not 92 noisy LLM items.
- Section traceability on every output item.
- Honest signed `reduction_pct`.

**Non-Goals:**
- No change to docling extraction or OCR.
- No new dependencies.
- No change to loop/harness categorization mechanics (LLM remains the extractor there).

## Decisions

### 1. Merge consecutive same-section fragments (`chunker.py`)
`group_chunks` currently starts a new group for *every* chunk whose heading matches the section pattern. Change: start a new group only when `current is None` or the heading is a section heading *different* from the current group's heading. Non-section headings (running headers, "REGRAS DE NEGÓCIO:", "CRITÉRIOS DE ACEITAÇÃO:") always append. Result: 49 → ~26 groups.
- *Alternative considered:* fuzzy rejoin after grouping. Rejected — fixing the loop condition is smaller and correct.

### 2. Deterministic-first dedup (`rules_extractor.py`, `classifier.py`)
`merge_deterministic` already drops LLM items whose rule id matches a deterministic id. Extend it to also drop LLM business rules/acceptance criteria that are near-duplicates of a deterministic item *without* an id, using normalized token overlap (>=2 shared content words, mirroring the diagnostic). The verbatim deterministic item always wins.
- *Alternative considered:* semantic dedup via a second LLM pass. Rejected — nondeterministic, slow, and the overlap heuristic already recovered 30/31 redundant rules in testing.

### 3. Requirements from headings (`rules_extractor.py`)
Derive requirement items from section-group headings matching `7.N RQxx: <TITLE>` (regex `\d+\.\d+\s+RQ\d+:\s*(.+)`). Each match yields one `{id: "RQxx", description: "<TITLE>"}` requirement with the group's source. LLM-provided requirements are dropped entirely. If a group has rules but no RQ heading, fall back to deriving the requirement from the first rule's `RQxx` prefix.
- *Alternative considered:* filter LLM requirements heuristically. Rejected — headings are deterministic and exactly 19, so filtering is unnecessary guesswork.

### 4. Section traceability for all items (`cli.py`)
After `classify_chunk`, overwrite `item.source` with `f"file:{src}§{heading}"` so LLM items carry the same section reference as deterministic items. `merge_items` already propagates `item.source` into every row via `setdefault`.

### 5. Language pinning (`prompts.py`)
Add one line to `CLASSIFY_SYSTEM_PROMPT`: "Respond in the same language as the document content."

### 6. Signed reduction (`token_counter.py`)
`reduction_pct` is already signed (`(1 - processed/raw)*100`, negative when grown) and `break_even_queries` is already `999` when `processed >= raw`. Change the CLI log line to report "reduction"/"growth" wording and keep the value signed; no formula change.

## Risks / Trade-offs

- **[Near-duplicate heuristic over-drops]** An LLM item sharing >=2 words with a verbatim rule could be a genuinely new rule → Mitigation: only rules/criteria are subject to the overlap check; section-8 table content (no `RQxx` ids) shares few words with verbatim rules and is preserved. Tunable threshold if false drops appear.
- **[Heading derivation misses a section]** Docling occasionally mis-heads a section (RQ03 lacked a heading chunk in one run) → Mitigation: fallback derives the requirement from the rule id prefix; completeness of rules is unaffected (deterministic extractor still captures them).
- **[Archive ordering]** Both this change and `lossless-spec-extraction` MODIFY `context-generation` → Archive lossless first; this change's MODIFIED blocks already state the final intended behavior.
