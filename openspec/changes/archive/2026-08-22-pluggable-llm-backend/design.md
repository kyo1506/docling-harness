# Design: Pluggable LLM Backend

## Context

See proposal.md for motivation. Current `classifier.py` hardcodes `base_url="http://localhost:11434/v1"`, `api_key="ollama"` in `_get_client()`, and `model="qwen2.5:14b"` in `_call_llm`. The `openai` client already targets any OpenAI-compatible base URL, so Ollama and DeepSeek/OpenAI are the same code path — only the three values differ.

## Goals / Non-Goals

**Goals:**
- Backend resolved from env vars with local Ollama as the default.
- `--model` flag overrides the model per-run.
- Default behavior byte-for-byte unchanged.
- No provider-specific code.

**Non-Goals:**
- No provider registry or `--backend ollama|deepseek` presets (three config values suffice).
- No pre-flight connectivity check (the first request failing naturally gives a clear error — same decision as the Ollama switch).
- No single-pass consolidation mode (future change, needs a strong remote model to justify dropping the deterministic scaffolding).

## Decisions

### 1. Resolve config in one place
Add a small config helper that returns `(base_url, api_key, model)` with precedence CLI flag > env var > default:
- `HARNESS_LLM_BASE_URL` → default `http://localhost:11434/v1`
- `HARNESS_LLM_API_KEY` → default `ollama`
- `HARNESS_LLM_MODEL` → default `qwen2.5:14b`
- `--model` flag overrides model only.

`_get_client()` and `_call_llm` read from this helper instead of literals. Precedence is evaluated once at CLI startup and passed down, so the flag/env resolution is testable without touching the network.
- *Alternative considered:* a dataclass/`LLMConfig` object. Rejected — three values; a tuple from one function is enough (YAGNI).

### 2. No provider presets
The OpenAI client is provider-agnostic. A `--backend` flag with a preset registry would be speculative abstraction — DeepSeek needs exactly the same three fields as Ollama, just different values. Document the DeepSeek example in the README instead.

### 3. `response_format={"type": "json_object"}` stays
DeepSeek and OpenAI both support JSON mode; the classification prompt already contains the word "JSON", which their JSON modes require. No change.

### 4. Retry logic stays
`_call_llm` keeps its single retry after 1s. Remote providers fail transiently for the same reasons (timeouts, rate limits); the retry handles them.

## Risks / Trade-offs

- **[Privacy]** A remote backend sends document text off-machine → This is user-elected: the default stays local, and the proposal flags the "Uso restrito" classification. No remote default.
- **[Provider JSON-mode drift]** Some providers require `json` in the prompt or reject `json_object` → The prompt already says "Return ONLY valid JSON"; if a provider rejects `json_object`, the fix is a provider-specific note, not code. Out of scope until observed.
- **[Secret leakage via env]** API key lives in the shell env → Documented; no key is logged (only base URL + model are reported).
