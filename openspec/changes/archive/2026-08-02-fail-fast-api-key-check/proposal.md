## Why

The CLI crashes AFTER 158 seconds of heavy PDF processing and ML model loading because the OpenRouter API key is missing from the environment. The `.env` file exists but nothing loads it, so `os.environ.get("OPENROUTER_API_KEY")` returns an empty string. Users waste minutes of CPU time only to hit a credential error at the final phase.

## What Changes

- Load `.env` file at CLI startup so `OPENROUTER_API_KEY` is available without manual export
- Validate the API key exists **before** any document processing begins, failing immediately with a clear message
- Skip the key check entirely when `--tokens-only` is used (no LLM needed)

## Capabilities

### New Capabilities
- `cli-startup-validation`: Pre-flight checks that run before the extraction pipeline, ensuring required configuration (API key) is present and failing fast with actionable error messages when it's not.

### Modified Capabilities
<!-- None — existing behavior for extraction, chunking, classification, merging, and output is unchanged. -->

## Impact

- `src/docling_harness/cli.py` — new startup logic (`.env` loading + key validation)
- `pyproject.toml` — optional: add `python-dotenv` dependency, or inline a minimal `.env` parser
- No API changes, no output format changes, no existing spec behavior changes
