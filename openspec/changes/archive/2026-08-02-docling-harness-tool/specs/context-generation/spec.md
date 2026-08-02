## Purpose

Classify and summarize extracted document content into three engineering disciplines — Spec-Driven Development, Loop Engineering, and Harness Engineering — producing a structured JSON consumable by human developers and AI coding agents.

## ADDED Requirements

### Requirement: Hierarchical chunking of extracted content

The system SHALL split extracted markdown into chunks preserving document hierarchy using Docling's HierarchicalChunker before classification.

#### Scenario: Document is split into hierarchical chunks
- **WHEN** a markdown document with section headers is processed
- **THEN** chunks are created respecting section boundaries and each chunk carries its heading path for context

### Requirement: LLM-based classification into three categories

The system SHALL send each chunk to an LLM via OpenRouter with a prompt that classifies content into one or more categories: Spec-Driven Development (requirements, acceptance criteria, data models, business rules), Loop Engineering (automation triggers, verifiable outputs, feedback loops), or Harness Engineering (context rules, validation gates, tool requirements).

#### Scenario: Chunk containing a requirement is classified
- **WHEN** a chunk contains text describing a functional requirement with acceptance criteria
- **THEN** the chunk is classified under specs with extracted requirement items and acceptance criteria

#### Scenario: Chunk containing automation trigger is classified
- **WHEN** a chunk describes a CI/CD trigger or scheduled job
- **THEN** the chunk is classified under loop_engineering with extracted trigger and verifiable output items

#### Scenario: Chunk containing a coding convention rule is classified
- **WHEN** a chunk contains an architecture constraint or coding standard
- **THEN** the chunk is classified under harness_engineering with extracted context rule and validation gate items

#### Scenario: Chunk fits no category
- **WHEN** a chunk contains generic introductory text or table of contents
- **THEN** the chunk produces empty arrays and is excluded from final output

### Requirement: Source traceability on every output item

The system SHALL include a `source` field on every extracted item (requirement, rule, trigger, etc.) referencing the original document path and section.

#### Scenario: Requirement carries source reference
- **WHEN** a requirement is extracted from section 3.2 of especificacao.pdf
- **THEN** the output item includes `"source": "pdf:especificacao.pdf:§3.2"`

### Requirement: Merge and deduplicate classified results

The system SHALL merge all chunk classification results into a single consolidated JSON, deduplicating semantically similar items and resolving conflicts.

#### Scenario: Duplicate requirements across chunks are merged
- **WHEN** two chunks from different sections reference the same business rule
- **THEN** the final output contains one merged item with both source references
