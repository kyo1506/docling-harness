## Context

See proposal.md for motivation. This is a greenfield Python CLI tool with no existing code to integrate with. The project already has `docling`, `token-count`, and `tiktoken` installed. The PDF `Especificação - Recad Personalizado - Melhorias - Minha Área e Sou Conectado_2.0.pdf` serves as a real-world test fixture.

## Goals / Non-Goals

**Goals:**
- Single CLI entry point that processes a directory of sources end-to-end
- Docling extraction with all format support (PDF, DOCX, HTML, video ASR, image OCR)
- Hierarchical chunking preserving section boundaries
- OpenRouter free-model LLM classification into specs/loop/harness
- TokenCount comparison report embedded in output
- Output: `harness.json` + `AGENTS.md` in a configurable directory

**Non-Goals:**
- Real-time document watching or file system monitoring
- A web UI or HTTP API (CLI only)
- Parallel/async LLM calls (sequential is good enough for initial version)
- Multi-language support beyond what Docling and the LLM handle natively
- Custom embedding or vector database integration
- Custom model training or fine-tuning

## Decisions

### Architecture: Linear pipeline with cache gate

```
CLI → Docling extract → TokenCount(raw) → Chunk
  → [per chunk] OpenRouter classify → Merge → TokenCount(processed)
  → Write harness.json + AGENTS.md
```

**Why this over alternatives:**
- Batch processing (all chunks → single merge) would require holding all chunk results in memory and a second LLM call for merge. The linear pipeline is simpler and the merge call is just one extra LLM invocation.
- Streaming each chunk result directly to output without merge would produce duplicated/unresolved items. The merge pass deduplicates and resolves conflicts.

### Package layout: Flat src/ package with explicit modules

```
src/docling_harness/
├── __init__.py
├── cli.py            # argparse entry point
├── extractor.py      # Docling DocumentConverter wrapper
├── chunker.py        # HierarchicalChunker wrapper
├── classifier.py     # OpenRouter LLM calls
├── merger.py         # Merge & consolidate
├── token_counter.py  # TokenCount wrapper
├── models.py         # Dataclasses for ChunkResult, HarnessOutput, etc.
├── prompts.py        # LLM prompt templates
└── output.py         # JSON + AGENTS.md writer
```

**Why this over a single-file script:**
- Multiple concerns (extraction, chunking, LLM, output) would make a single file hard to navigate. Each module has one responsibility.
- No framework needed — standard library + the 4 dependencies.

### LLM integration: openai Python client with OpenRouter base_url

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)
```

**Why this over raw requests:**
- OpenAI-compatible SDK handles retries, streaming, and error parsing
- Already a project dependency (needed for structured output + token counting)
- `response_format={"type": "json_object"}` forces valid JSON output for classification

**Provider routing**: Use `provider.sort: "throughput"` as default for batch processing. Support `--sort throughput|latency|price` CLI flag. Use `provider.require_parameters: true` to ensure the selected free model supports JSON structured output.

**Why `openrouter/free` over specific free models:**
- Letting OpenRouter select models handles availability automatically
- No need to manage model deprecation or availability
- The router filters for capabilities (JSON mode, context length) automatically

### Classification prompt design: Single prompt, three categories

The LLM receives each chunk with a system prompt that defines the three categories and requests structured JSON output. The prompt is in `prompts.py` to keep it version-controlled separately from code.

**Why single prompt over three separate classification passes:**
- One LLM call per chunk instead of three → 3x fewer API calls
- The model can determine that a chunk may span multiple categories or none
- Simpler: one response to parse per chunk

### Merge strategy: Single LLM call with iterative refinement fallback

The merger sends all classified chunk results to the LLM with instructions to deduplicate and consolidate. If the output exceeds the output token limit, a second pass handles the overflow.

**Why LLM-based merge over programmatic:**
- Deduplication and semantic conflict resolution require understanding content meaning
- Simple concatenation would produce duplicate items and unresolved contradictions

## Risks / Trade-offs

### [Risk] Free model quality varies unpredictably
OpenRouter `openrouter/free` routes to 18 different models with varying quality. A weak model may produce malformed JSON or poor classification.
→ **Mitigation**: Validate JSON response after each LLM call. Retry once with a different system prompt if parsing fails. Log the model used for each call so quality issues are traceable.

### [Risk] Large documents may exceed free model context windows
Some free models have limited context (8K-32K tokens). A large chunk might not fit.
→ **Mitigation**: HierarchicalChunker already splits at section boundaries. Configure maximum chunk size (~2000 tokens) well within even 8K limits.

### [Risk] LLM classification accuracy is not guaranteed
The classification into specs/loop/harness depends on LLM judgment, which may misclassify or miss items.
→ **Mitigation**: Include `source` pointers on every item so humans/agents can verify against the original document. The tool reduces cognitive load, not replaces human review.

### [Risk] Docling ASR accuracy depends on Whisper model quality
The default `whisper_tiny` model has lower accuracy than larger Whisper variants.
→ **Mitigation**: Acceptable for v1 — transcripts are better than no content from videos. Configurable model selection can be added later.

## Open Questions

- None at this stage. All design decisions are resolved.
