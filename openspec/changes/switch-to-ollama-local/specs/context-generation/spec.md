## MODIFIED Requirements

### Requirement: LLM-based classification into three categories

The system SHALL send each chunk to a local LLM via Ollama (`mistral:7b`) with a prompt that classifies content into one or more categories: Spec-Driven Development (requirements, acceptance criteria, data models, business rules), Loop Engineering (automation triggers, verifiable outputs, feedback loops), or Harness Engineering (context rules, validation gates, tool requirements).

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
