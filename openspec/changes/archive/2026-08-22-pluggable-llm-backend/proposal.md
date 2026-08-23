## Why

The classifier hardcodes the LLM backend to local Ollama (`http://localhost:11434/v1`, `qwen2.5:14b`). Local is the right default — the target documents are Prodesp requirement specs marked "Classificação: Uso restrito", so content must not leave the machine — but the 14B model on CPU is the weak link: it paraphrases, leaks English, and is slow (31+ calls). When a document is not privacy-restricted, the user wants the option to point the tool at a paid OpenAI-compatible provider (e.g. DeepSeek) for higher quality and speed without changing code.

## What Changes

- **Configurable LLM backend** — the base URL, API key, and model are resolved from environment variables with local Ollama as the default, so switching to a remote provider is a configuration change, not a code change.
- **Model override via CLI flag** — a `--model` flag overrides the configured model for a single run.
- **Active backend logged** — the CLI reports the resolved backend (URL + model) before classification.
- No provider-specific code, presets, or registries: the existing OpenAI client already speaks both Ollama and any OpenAI-compatible endpoint (DeepSeek, OpenAI, etc.).

## Capabilities

### New Capabilities
- `llm-provider-configuration`: The tool resolves the LLM backend (endpoint, key, model) from configuration, defaulting to local Ollama, and supports any OpenAI-compatible provider without code changes.

### Modified Capabilities
<!-- none: classification semantics are unchanged; only the backend it targets becomes configurable -->

## Impact

- **Code**: `src/docling_harness/classifier.py` (config resolution in `_get_client`/`_call_llm`), `src/docling_harness/cli.py` (`--model` flag, backend log line).
- **Config**: env vars `HARNESS_LLM_BASE_URL`, `HARNESS_LLM_API_KEY`, `HARNESS_LLM_MODEL` (all optional, Ollama defaults).
- **Dependencies**: none added (uses the existing `openai` client).
- **Behavior**: default run is byte-for-byte unchanged (local Ollama, `qwen2.5:14b`); remote providers require the user to set env vars.
- **Docs**: README "Considerations" updated with provider configuration examples.
- **Tests**: `tests/test_pipeline.py` gains config-resolution and flag-override coverage.
