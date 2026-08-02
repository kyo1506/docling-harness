## 1. Project Setup

- [x] 1.1 Create `pyproject.toml` with dependencies (`docling`, `docling-core`, `openai`, `token-count`, `tiktoken`, `httpx`) and CLI entry point
- [x] 1.2 Create `src/docling_harness/` package structure with `__init__.py`
- [x] 1.3 Create `.env.example` with `OPENROUTER_API_KEY` placeholder
- [x] 1.4 Add `httpx` dependency for URL source fetching

## 2. Data Models

- [x] 2.1 Create `models.py` with `SourceRef` dataclass (type, path, hash, status)
- [x] 2.2 Create `models.py` with `ChunkResult` dataclass (category, items, source, model_used)
- [x] 2.3 Create `models.py` with `HarnessOutput` dataclass (meta, specs, loop_engineering, harness_engineering)
- [x] 2.4 Create `models.py` with `CostComparison` dataclass (raw_tokens, processed_tokens, reduction_pct, break_even_queries)

## 3. Document Extraction

- [x] 3.1 Implement `extractor.py` — wrap `DocumentConverter` with per-format options (PDF pipeline, image OCR, ASR pipeline for audio/video)
- [x] 3.2 Support URL sources via `httpx` fetch before Docling conversion
- [x] 3.3 Return structured markdown with tables preserved for each source

## 4. Chunking

- [x] 4.1 Implement `chunker.py` — wrap `HierarchicalChunker` from `docling_core.transforms.chunker`
- [x] 4.2 Configure max chunk size (~2000 tokens) to fit within free model context windows
- [x] 4.3 Preserve heading path in chunk metadata for classification context

## 5. LLM Classification

- [x] 5.1 Create `prompts.py` with system prompt defining specs/loop/harness categories and JSON output schema
- [x] 5.2 Implement `classifier.py` — OpenRouter client with `base_url`, API key from env, `HTTP-Referer` and `X-OpenRouter-Title` headers
- [x] 5.3 Call `openrouter/free` with `provider.sort` (default throughput), `provider.require_parameters: true`, `response_format: json_object`
- [x] 5.4 Parse JSON response, validate structure, retry once on parse failure
- [x] 5.5 Log model used and tokens consumed for each LLM call

## 6. Merge and Consolidation

- [x] 6.1 Implement `merger.py` — send all `ChunkResult` items to LLM with merge prompt for deduplication
- [x] 6.2 Handle large result sets with fallback: if merge output exceeds limit, split and re-merge
- [x] 6.3 Produce final `HarnessOutput` with resolved, deduplicated items preserving source links

## 7. Token Comparison

- [x] 7.1 Implement `token_counter.py` — wrap `TokenCount` with configurable model name
- [x] 7.2 Count tokens of raw markdown output (pre-chunking) for each source
- [x] 7.3 Count tokens of final processed JSON
- [x] 7.4 Compute `CostComparison` with reduction percentage and break-even queries

## 8. Output Generation

- [x] 8.1 Implement `output.py` — write `harness.json` from `HarnessOutput` dataclass
- [x] 8.2 Generate `AGENTS.md` index file with markdown links to `harness.json` sections and item counts
- [x] 8.3 Support `--output` flag for custom output directory (default `.context/`)

## 9. CLI

- [x] 9.1 Implement `cli.py` with `argparse` entry point
- [x] 9.2 `sources` positional argument (directory or file list)
- [x] 9.3 `--output` flag for output directory
- [x] 9.4 `--tokens-only` flag for dry-run token comparison without LLM classification
- [x] 9.5 `--sort` flag (`throughput|latency|price`, default `throughput`)
- [x] 9.6 Wire pipeline: extract → token count raw → chunk → classify → merge → token count processed → output

## 10. Testing

- [x] 10.1 Test extraction with the local PDF fixture (`Especificação - Recad Personalizado...`)
- [x] 10.2 Test token comparison output (raw > processed)
- [x] 10.3 Test `harness.json` has correct top-level keys and item source references
- [x] 10.4 Test `AGENTS.md` is generated and under 100 lines
