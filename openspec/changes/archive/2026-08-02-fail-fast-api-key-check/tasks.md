## 1. .env Loading

- [x] 1.1 Add `.env` file parser at top of `main()` in `cli.py`: resolve `.env` path relative to package root, skip blank/comment lines, parse `KEY=VALUE` pairs, call `os.environ.setdefault(k, v)`

## 2. Pre-flight API Key Check

- [x] 2.1 After argument parsing and `.env` loading, check `OPENROUTER_API_KEY`: if `--tokens-only` is false and the key is missing or empty, call `logger.error(...)` with a clear message and `sys.exit(1)`

## 3. Verification

- [x] 3.1 Run `harness sources/ --tokens-only` with no key set — SHALL succeed (key check skipped)
- [x] 3.2 Run `harness sources/` with no key set — SHALL exit immediately with code 1 and message, no Docling initialization
- [x] 3.3 Run `harness sources/` with valid key in `.env` — SHALL proceed normally through full pipeline
