## ADDED Requirements

### Requirement: Robust merge for large chunk counts

The system SHALL pass complete, valid JSON to the merge LLM regardless of source document size, avoiding truncation that breaks JSON structure and causes the LLM to produce malformed responses.

#### Scenario: Payload under safe limit is sent complete
- **WHEN** all chunk classification results fit within a safe payload size (at least 4× the current 30,000 character limit)
- **THEN** the full payload is sent to the merge LLM without structural truncation

#### Scenario: Payload exceeds safe limit is sampled cleanly
- **WHEN** the accumulated classification payload exceeds the safe character limit
- **THEN** the payload is truncated at the last complete JSON item boundary, and a note is appended indicating how many items were omitted

#### Scenario: Merge LLM returns response with unexpected schema
- **WHEN** the merge LLM produces a JSON response that lacks one or more expected top-level keys (`specs`, `loop_engineering`, `harness_engineering`)
- **THEN** the system SHALL not silently produce empty output; it SHALL log a warning and include whatever valid sections were returned, using empty defaults only for truly missing sections

### Requirement: Merge response fallback on failure

The system SHALL detect when the merge phase produces no useful output and provide a graceful degradation path.

#### Scenario: Merge response is empty or structurally invalid
- **WHEN** the merge LLM returns `{}` or an unparseable response after a retry
- **THEN** the system SHALL fall back to a programmatic merge that preserves all individually classified items in the output, annotated with a warning that LLM-based deduplication was skipped
