## Context

`classifier.py:merge_results()` serializes all `ChunkItem.items` into a JSON array and sends it to the merge LLM. A hard truncation at 30,000 characters (`payload[:30000]`) breaks the JSON structure mid-key or mid-array when the accumulated payload exceeds this limit. The merge LLM receives invalid JSON and produces responses with unexpected key names (e.g., `"project_specs"` instead of `"specs"`). `merger.py:merge()` uses `.get("specs", {})` which silently returns `{}` when the expected keys are missing, producing completely empty output.

See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- Merge LLM always receives structurally valid JSON input
- Malformed merge responses are detected and handled instead of silently producing empty output
- Works for documents of any page count without artificial truncation limits

**Non-Goals:**
- Changing the merge prompt or classification prompts
- Switching to a different LLM model or provider
- Modifying the output file format (`harness.json` / `AGENTS.md` schema)

## Decisions

### Decision 1: Clean truncation at JSON item boundary instead of byte-level cut

**Choice**: Replace `payload[:30000]` with a function that truncates at the last complete JSON object boundary, closes the array with `]`, and appends a note about omitted items.

**Rationale**: A byte-level slice guarantees broken JSON when the limit is hit. Truncating at an object boundary produces valid (if incomplete) JSON that the LLM can process. The note helps the LLM understand the context without disrupting parsing.

**Alternatives considered**:
- *Remove the limit entirely*: Risks hitting the LLM's context window (mistral:7b has 32K tokens) for very large documents, causing silent failures at the API level.
- *Batch merge (merge subsets, then merge results)*: Correct but adds complexity (multiple LLM calls, intermediate results management). Premiature for the current scale.

### Decision 2: Increase safe payload limit to 100K characters

**Choice**: Set the truncation threshold to 100,000 characters (~25K tokens, well within mistral:7b's 32K context window leaving room for prompt and response).

**Rationale**: 30K characters was an arbitrary limit. 100K allows documents up to ~400 chunks (assuming ~250 chars per classified item) to pass through without truncation, covering the vast majority of use cases.

### Decision 3: Validate merge response schema before using it

**Choice**: In `merger.py`, after parsing the merge response, verify that the expected top-level keys exist. If a key is missing or its value is not a dict, use `{}` but log a warning. If ALL three categories are empty/missing, log an error and fall back to programmatic concatenation.

**Rationale**: The current code silently accepts any dict as valid, even when the LLM returns a completely different structure. Schema validation catches the failure case we observed and provides actionable logging.

**Alternatives considered**:
- *Prompt-level enforcement only*: The prompt already specifies the schema. Relying on prompt adherence alone failed in practice.
- *Retry with stricter prompt*: Adds latency without guarantee of success.

### Decision 4: Programmatic fallback when LLM merge fails

**Choice**: When the merge LLM returns empty or invalid output after a retry, concatenate all individually classified items into the output structure without deduplication, annotating the meta section with a warning flag (`"merge_fallback": true`).

**Rationale**: Better to have un-deduplicated (but complete) output than silent empty output. The fallback preserves all extracted information at the cost of potential duplicates, which is an acceptable trade-off over losing data.

## Risks / Trade-offs

- **[Risk] 100K char limit could still be exceeded for very large documents (500+ pages)** → The clean truncation at object boundary ensures graceful degradation, and the note about omitted items informs the user.
- **[Risk] Clean truncation may split a logical group of related items across the truncation boundary** → The fallback note in the prompt tells the LLM which items were omitted, and the user can re-run with a subset of sources.
- **[Risk] Programmatic fallback skips deduplication** → The `meta.merge_fallback` flag alerts consumers that duplicates may exist. Most agent consumers can handle duplicates trivially.
