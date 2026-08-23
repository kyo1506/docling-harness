# Design: Switch to Ollama Local

## Architecture change

```
Before:                          After:
┌──────────┐                     ┌──────────┐
│  CLI     │                     │  CLI     │
│  .env →  │ OPENROUTER_API_KEY  │          │ (no .env needed)
│  --sort  │─────────────────>   │          │
└────┬─────┘                     └────┬─────┘
     │                                │
┌────▼──────────┐                ┌────▼──────────┐
│  classifier   │                │  classifier   │
│  base_url:    │                │  base_url:    │
│  openrouter.ai│                │  localhost:   │
│               │                │  11434/v1     │
│  model:       │                │  model:       │
│  openrouter/  │                │  mistral:7b   │
│  free         │                │               │
│  extra_body:  │                │  (no extra_   │
│  provider.sort│                │   body)       │
└───────────────┘                └───────────────┘
```

## Files changed

| File | Change |
|------|--------|
| `classifier.py` | `base_url` → `http://localhost:11434/v1`, `model` → `mistral:7b`, `api_key` → `"ollama"`, remove `default_headers`, remove `sort` param from all functions, remove `extra_body` |
| `cli.py` | Remove `--sort` argument, remove `.env` file parsing, remove `OPENROUTER_API_KEY` pre-flight check |
| `.env` | Delete |
| `.env.example` | Delete |

## Key decisions

### Hardcoded model, no CLI flag
Ladder rung 1: does this need to exist? The tool currently has no model-switching feature. Adding a `--model` flag is speculative abstraction — zero evidence anyone switches models per-run. Revisit when it becomes a real need.

### Ollama connectivity check
The `cli-startup-validation` spec currently mandates an API key check. With Ollama, the equivalent is verifying the Ollama service is reachable. Instead of an explicit health check call, we let the first LLM request fail naturally — Ollama errors are clear and the stack trace points to the fix. A pre-flight check would add complexity for zero improvement to the error message.

### `response_format={"type": "json_object"}` stays
Ollama supports this — mistral:7b respects it. No change needed.

### Retry logic untouched
The 1-retry pattern stays. Ollama calls fail locally for the same reasons (model not loaded, OOM, etc.), and a single retry after 1s handles transient overlap.

## Risks

- **Classification quality**: mistral:7b is weaker than the models OpenRouter routes to. Mitigation: this tool classifies engineering documentation into three predefined categories — a structured JSON task well within 7B model capabilities. If quality drops measurably, the fix is a model switch, not a provider switch.
- **Ollama not running**: user gets a clear connection error from the OpenAI client. Acceptable for a local dev tool.
