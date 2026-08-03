## Context

The CLI currently performs operations in this order:

```
main() → parse_args → collect_sources → extract(docling) → chunk → classify(LLM) → merge(LLM) → output
```

The first opportunity for a credential error is inside `classify_chunk()` → `_get_client()` → `OpenAI(...)`, which runs AFTER the expensive docling extraction (~158 seconds for a PDF). The `.env` file exists in the repo root but no code reads it.

## Goals / Non-Goals

**Goals:**
- Validate OPENROUTER_API_KEY exists before any document extraction runs
- Load `.env` file automatically so users don't need to manually export variables
- Fail with a clear, actionable error message (not a cryptic traceback)
- Skip the check when `--tokens-only` is active

**Non-Goals:**
- General-purpose dotenv library with variable expansion, multiline values, or quoting support
- Validation of other keys or configuration beyond OPENROUTER_API_KEY
- Changing the classifier, chunker, or any other module

## Decisions

### Decision 1: Parse .env inline instead of adding python-dotenv

**Chosen:** Minimal inline parser (~5 lines) at the top of `main()`.

**Alternatives considered:**
- `python-dotenv` library: +1 dependency for a single `load_dotenv()` call. Overkill for KEY=VALUE-only format.
- `os.environ.setdefault` approach: parse each line, split on first `=`, call `os.environ.setdefault(k, v)` — existing env vars take precedence over `.env`, which is standard dotenv behavior.

**Rationale:** Zero new dependencies. The `.env.example` shows a simple `KEY=value` format — no quoting, no interpolation, no multiline. The lazy parse handles that perfectly.

### Decision 2: Check at CLI top-level, not in classifier

**Chosen:** Pre-flight check in `main()` BEFORE `collect_sources()` or any `extract()` call.

**Rationale:** Putting the check in `_get_client()`/`classify_chunk()` still wastes the extraction time. The check must be the very first thing after argument parsing (except for `--tokens-only`). This also means the Docling `DocumentConverter` import is never triggered on a failed run.

### Decision 3: Exit code 1, message to stderr via logger

**Chosen:** `logger.error(...)` + `sys.exit(1)` — consistent with existing error handling in `cli.py`.

## Risks / Trade-offs

- `.env` in repo root assumption: if user runs `harness` from a different working directory, the `.env` won't be found. Mitigation: resolve relative to the harness package root, not CWD.
- **BREAKING?** No — the behavior when a key IS set is identical. The only change is when the key is missing: instead of a delayed crash, it fails immediately.
