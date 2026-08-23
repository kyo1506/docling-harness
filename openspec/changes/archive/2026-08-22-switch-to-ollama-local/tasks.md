# Tasks: Switch to Ollama Local

- [x] Update `classifier.py` — swap `base_url` to `http://localhost:11434/v1`, model to `mistral:7b`, remove `sort` parameter from `classify_chunk`, `merge_results`, and `_call_llm`, remove `extra_body` and `default_headers`
- [x] Update `cli.py` — remove `--sort` argument, remove `.env` file parsing, remove `OPENROUTER_API_KEY` pre-flight check
- [x] Delete `.env` and `.env.example`
- [x] Sync `context-generation` spec (delta already written, archive will merge to main)
- [x] Verify — run `harness sources/` and confirm full pipeline works
