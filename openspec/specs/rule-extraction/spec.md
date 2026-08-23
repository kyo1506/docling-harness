# rule-extraction Specification

## Purpose
Deterministically extracts structured business rules and acceptance criteria from specification documents, guaranteeing complete capture of rule items with exact source text regardless of LLM classification quality.

## Requirements

### Requirement: Extract structured business rules

The system SHALL identify business rule items in section text matching structured rule patterns (`RQxx-RNxx`, `RQxx-RQxx`, or standalone `RNxx`) and capture the rule title and full body text, including continuation bullet lines, up to the next rule marker.

#### Scenario: Rules in a requirement section are extracted
- **WHEN** section text contains `- RQ01-RN01 - Alteração de Label: O sistema deverá alterar o texto...` followed by more rule bullets
- **THEN** each rule is captured as a business rule item whose text is the verbatim source text with the rule id preserved

#### Scenario: Multi-line rule body is captured completely
- **WHEN** a rule's body spans continuation bullets (e.g., sub-options under `- o ...`)
- **THEN** the full text of the rule, including continuation bullets, is included until the next rule or criterion marker

### Requirement: Extract acceptance criteria

The system SHALL identify acceptance criterion items matching the structured pattern `RQxx-CAxx` and capture each with its verbatim text and rule id.

#### Scenario: Criteria in a requirement section are extracted
- **WHEN** section text contains `- RQ01-CA01 - Validação da Label: O sistema deve exibir...`
- **THEN** the criterion is captured as an acceptance criterion item with the exact source text

### Requirement: Deterministic completeness independent of LLM classification

The system SHALL extract structured rules and criteria deterministically from raw text so that items are captured even when the LLM classification omits or paraphrases them; extracted items SHALL be unioned with LLM-classified items and deduplicated by rule id, preferring the exact extracted text.

#### Scenario: LLM omission is compensated by deterministic extraction
- **WHEN** a section contains 4 business rules but the LLM classifies only 3
- **THEN** the final output contains all 4 rules, with the deterministic extraction supplying the missing item

#### Scenario: Duplicate across deterministic and LLM extraction is deduplicated
- **WHEN** the same rule id is produced by both the deterministic extractor and the LLM classifier
- **THEN** the final output contains one item, using the verbatim extracted text

### Requirement: Source traceability of extracted rules

The system SHALL attach a source reference (document path and section heading) to every deterministically extracted rule and criterion item.

#### Scenario: Extracted rule carries source reference
- **WHEN** a business rule is extracted from the section headed `7.15 RQ15`
- **THEN** the output item includes a source field referencing the document path and the RQ15 section
