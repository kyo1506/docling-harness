## Purpose

Measure and compare token counts between raw Docling-extracted markdown and the final processed JSON to quantify cost savings from the processing pipeline.

## ADDED Requirements

### Requirement: Count tokens of raw extracted markdown

The system SHALL count tokens of the full Docling-extracted markdown output (before chunking and classification) using the TokenCount library configured for a specified model.

#### Scenario: Raw token count is computed
- **WHEN** a PDF is extracted by Docling producing 5000 words of markdown
- **THEN** the raw token count is computed and stored as an integer

### Requirement: Count tokens of final processed JSON

The system SHALL count tokens of the final processed JSON output (after chunking, classification, and merge) using the same tokenizer and model.

#### Scenario: Processed token count is computed
- **WHEN** the final harness.json is generated from the same source
- **THEN** the processed token count is computed and stored as an integer

### Requirement: Generate cost comparison report

The system SHALL produce a comparison report in the output JSON's `_meta` section including raw token count, processed token count, reduction percentage, and estimated cost savings per query.

#### Scenario: Comparison report is included in output
- **WHEN** processing completes with 50000 raw tokens and 5000 processed tokens
- **THEN** the `_meta.cost_comparison` object includes `raw_tokens: 50000`, `processed_tokens: 5000`, `reduction_pct: 90.0`, and `break_even_queries` indicating how many LLM queries it takes to recoup the processing cost

### Requirement: Dry-run token-only mode

The system SHALL support a `--tokens-only` flag that computes and displays token comparison without running the full classification pipeline.

#### Scenario: Token-only mode skips classification
- **WHEN** the CLI is invoked with `--tokens-only`
- **THEN** only extraction and token counting are performed; no LLM classification calls are made
