## MODIFIED Requirements

### Requirement: Generate cost comparison report

The system SHALL produce a comparison report in the output JSON's `_meta` section including raw token count, processed token count, and a signed reduction percentage reflecting the actual size change (which MAY be negative when the processed output exceeds the raw input). A negative reduction SHALL be reported as growth, not as cost savings.

#### Scenario: Comparison report is included in output
- **WHEN** processing completes with 50000 raw tokens and 5000 processed tokens
- **THEN** the `_meta.cost_comparison` object includes `raw_tokens: 50000`, `processed_tokens: 5000`, `reduction_pct: 90.0`, and `break_even_queries` indicating how many LLM queries it takes to recoup the processing cost

#### Scenario: Processed output exceeds raw input
- **WHEN** processing completes with 17000 raw tokens and 25000 processed tokens
- **THEN** the `_meta.cost_comparison` object reports `reduction_pct` as a negative value and does not present the result as savings
