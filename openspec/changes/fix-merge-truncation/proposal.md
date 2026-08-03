## Why

When processing documents with enough chunks that the merged JSON payload exceeds 30,000 characters, `classifier.py:merge_results()` truncates the payload mid-structure with `payload[:30000]`. The merge LLM receives broken, invalid JSON and produces a response whose keys don't match the expected schema (`"project_specs"` instead of `"specs"`, etc.). The downstream `merger.py` uses `.get("specs", {})` which silently returns `{}`, producing completely empty output (zero requirements, zero triggers, zero rules) despite successful chunk classification.

This was discovered after processing a 139-page PDF where all 139 chunks classified correctly but the final `harness.json` had all-empty categories.

## What Changes

- Fix the merge payload construction in `classifier.py` to avoid truncating JSON mid-structure
- Add robustness in `merger.py` to detect and handle malformed merge responses instead of silently producing empty output
- The merge LLM must receive valid, processable input regardless of chunk count

## Capabilities

### Modified Capabilities

- `context-generation`: The merge-and-deduplicate step currently violates its requirement ("merge all chunk classification results into a single consolidated JSON") when the accumulated payload exceeds 30K chars. The truncation must be replaced with a strategy that preserves valid, mergeable input.

## Impact

- `src/docling_harness/classifier.py` — `merge_results()` payload construction and truncation logic
- `src/docling_harness/merger.py` — merge response handling and validation
- No API changes, no new dependencies, no breaking changes to output schema
