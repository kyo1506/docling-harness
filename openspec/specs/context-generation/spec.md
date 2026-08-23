# Context Generation Specification

## Purpose

Classify and summarize extracted document content into three engineering disciplines — Spec-Driven Development, Loop Engineering, and Harness Engineering — producing a structured JSON consumable by human developers and AI coding agents.

## Requirements

### Requirement: Hierarchical chunking of extracted content

The system SHALL split extracted markdown into section groups before classification, reassembling hierarchical chunk fragments into coherent document sections. Consecutive fragments carrying the same section heading SHALL be merged into a single group so that each section (e.g., `7.N RQxx`) is classified as one unit. Fragments shorter than 40 characters that match no structured rule or criterion pattern SHALL be excluded.

#### Scenario: Document is split into hierarchical chunks
- **WHEN** a markdown document with section headers is processed
- **THEN** fragments under the same section header are merged into a single section group, consecutive fragments of the same section form one group, and each group carries its heading path for context

#### Scenario: Noise fragments are excluded
- **WHEN** a fragment contains only a running page header or a few stray characters with no rule or criterion pattern
- **THEN** the fragment is excluded from classification

### Requirement: LLM-based classification into three categories

The system SHALL send each section group to a local LLM with a prompt that classifies content into one or more categories: Spec-Driven Development (requirements, acceptance criteria, data models, business rules), Loop Engineering (automation triggers, verifiable outputs, feedback loops), or Harness Engineering (context rules, validation gates, tool requirements). Structured business rules and acceptance criteria SHALL be captured deterministically as the source of truth; the LLM SHALL supplement only content the deterministic extraction cannot capture (unstructured tables, data models, loops, and harness items). The prompt SHALL instruct the model to respond in the document's language.

#### Scenario: Chunk containing a requirement is classified
- **WHEN** a section group contains text describing a functional requirement with acceptance criteria
- **THEN** the section group is classified under specs with extracted requirement items and acceptance criteria

#### Scenario: Chunk containing automation trigger is classified
- **WHEN** a section group describes a CI/CD trigger or scheduled job
- **THEN** the section group is classified under loop_engineering with extracted trigger and verifiable output items

#### Scenario: Chunk containing a coding convention rule is classified
- **WHEN** a section group contains an architecture constraint or coding standard
- **THEN** the section group is classified under harness_engineering with extracted context rule and validation gate items

#### Scenario: Chunk fits no category
- **WHEN** a section group contains generic introductory text or table of contents
- **THEN** the section group produces empty arrays and is excluded from final output

### Requirement: Source traceability on every output item

The system SHALL include a `source` field on every extracted item (requirement, rule, trigger, etc.) referencing the original document path and section.

#### Scenario: Requirement carries source reference
- **WHEN** a requirement is extracted from section 3.2 of especificacao.pdf
- **THEN** the output item includes `"source": "pdf:especificacao.pdf:§3.2"`

### Requirement: Merge and deduplicate classified results

The system SHALL merge all section group classification results into a single consolidated JSON using a lossless programmatic merge that retains every distinct item. The merge SHALL deduplicate LLM-classified items against deterministically extracted items so that paraphrases of an already-captured rule or criterion are dropped in favor of the verbatim text, and SHALL assign stable identifiers to requirements, acceptance criteria, data models, and business rules.

#### Scenario: All classified items survive the merge
- **WHEN** section groups are classified and passed to the merge step
- **THEN** the final output contains every extracted requirement, criterion, rule, and model item across all section groups, each with a source reference

#### Scenario: Duplicate requirements across chunks are merged
- **WHEN** an LLM-classified business rule or acceptance criterion paraphrases a deterministically extracted item with the same rule id or substantially the same text
- **THEN** the final output contains one item — the verbatim deterministic text — and drops the paraphrase

#### Scenario: Generated identifiers are assigned
- **WHEN** the merge produces the final JSON
- **THEN** requirements, acceptance criteria, business rules, and data models carry stable generated ids in their category ordering

### Requirement: Requirements derived from section headings

The system SHALL derive requirement items from numbered requirement section headings (e.g., `7.15 RQ15: INCLUSÃO DE CAMPOS DE CONTATO DE EMERGÊNCIA`) so that each requirement section yields one clean requirement, and SHALL exclude changelog, scope, premise, and story fragments from the requirements list.

#### Scenario: Requirements are derived from headings, not noise
- **WHEN** a document has 19 numbered requirement sections plus a change history table and scope/premise text
- **THEN** the final output contains 19 requirement items derived from the section headings, with no changelog or scope entries among them
