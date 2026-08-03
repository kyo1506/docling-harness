# Switch to Ollama Local

## Problem

The tool currently uses OpenRouter's free tier (`openrouter/free` model) for LLM classification, which imposes a hard cap of **50 requests/day**. Each document generates N+1 calls (one per chunk + one merge), making the cap hit after ~8-10 small documents or a single large one. The tool is a local development utility — this rate limit is a non-starter for practical use.

## Proposed Solution

Replace OpenRouter with a local Ollama instance running `mistral:7b`. The OpenAI Python client already speaks Ollama's API (`http://localhost:11434/v1`). The change is minimal: swap `base_url`, `model`, drop OpenRouter-specific headers and `--sort`, remove `.env`-based API key management.

## Scope

**In:**
- Point LLM client at `http://localhost:11434/v1` with model `mistral:7b`
- Remove `--sort` CLI flag (provider sorting is an OpenRouter concept)
- Remove `.env` loading and `OPENROUTER_API_KEY` validation from CLI
- Delete `.env` file (contains real key, no longer needed)
- Update specs: `context-generation` (replace "OpenRouter" with "LLM"), `cli-startup-validation` (replace API key validation with Ollama connectivity check)

**Out:**
- No provider abstraction layer (YAGNI — one backend is enough today)
- No model selection CLI flag (re-evaluate when overridden need is proven)
- No fallback to OpenRouter (if Ollama is down, the tool is down — local-first)
- No changes to extraction, chunking, token counting, or output modules

## Impact

- **Zero external dependencies** — no API keys, no rate limits, no network calls for classification
- **Privacy** — document content stays local
- **Faster iteration** — local latency beats remote queue, especially for batches
