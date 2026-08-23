# Tasks: Pluggable LLM Backend

## 1. Config resolution

- [x] 1.1 Add a `resolve_llm_config(model_override)` helper (in `classifier.py` or a new `config.py`) returning `(base_url, api_key, model)` with precedence `--model` flag > `HARNESS_LLM_MODEL` > default `qwen2.5:14b`, and `HARNESS_LLM_BASE_URL` / `HARNESS_LLM_API_KEY` defaulting to `http://localhost:11434/v1` / `ollama`
- [x] 1.2 Thread the resolved values through `_get_client()` and `_call_llm()` so no literal base URL, key, or model remains

## 2. CLI wiring

- [x] 2.1 Add a `--model` CLI flag to `cli.py` and pass it into `resolve_llm_config` before classification
- [x] 2.2 Log the resolved backend (base URL + model) before classification starts

## 3. Tests

- [x] 3.1 Add a test that `resolve_llm_config(None)` returns the Ollama defaults when no env vars are set
- [x] 3.2 Add a test that `resolve_llm_config` honors `HARNESS_LLM_BASE_URL` / `HARNESS_LLM_API_KEY` / `HARNESS_LLM_MODEL` when set
- [x] 3.3 Add a test that the `--model` override takes precedence over `HARNESS_LLM_MODEL`

## 4. Docs and verification

- [x] 4.1 Update README "Considerations" with env-var and `--model` usage plus a DeepSeek example
- [x] 4.2 Run `python tests/test_pipeline.py` — all tests pass
- [x] 4.3 Run `harness sources/` with no env vars and confirm the default backend (Ollama) is logged and the run completes as before
