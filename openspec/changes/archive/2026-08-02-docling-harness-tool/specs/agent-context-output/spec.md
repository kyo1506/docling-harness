## Purpose

Generate structured output files — a JSON harness document and an AGENTS.md index — formatted for direct consumption by AI coding agents (Claude Code, Codex, opencode).

## ADDED Requirements

### Requirement: Structured harness JSON output

The system SHALL produce a `harness.json` file with top-level sections for `_meta`, `specs`, `loop_engineering`, and `harness_engineering`, each containing categorized and sourced items from the classification pipeline.

#### Scenario: JSON output has correct top-level structure
- **WHEN** classification and merge complete
- **THEN** the output file contains `_meta`, `specs`, `loop_engineering`, and `harness_engineering` top-level keys

#### Scenario: Specs section contains requirement items
- **WHEN** requirements were extracted during classification
- **THEN** `specs.requirements` is an array of objects with `id`, `description`, `source`, and `priority` fields

#### Scenario: Loop section contains trigger items
- **WHEN** automation triggers were extracted during classification
- **THEN** `loop_engineering.automation_triggers` is an array of objects with `trigger`, `action`, and `verifiable` fields

#### Scenario: Harness section contains rule items
- **WHEN** context rules were extracted during classification
- **THEN** `harness_engineering.context_rules` is an array of objects with `rule`, `enforced_by`, and `source` fields

### Requirement: AGENTS.md index generation

The system SHALL generate an `AGENTS.md` file containing a concise index that points to sections of the harness JSON, formatted as relative file references that agents can resolve.

#### Scenario: AGENTS.md references JSON sections
- **WHEN** harness.json is generated with 23 requirements and 4 triggers
- **THEN** AGENTS.md contains markdown links pointing to `harness.json#specs.requirements` with a count of items

#### Scenario: AGENTS.md is short enough to be read in one pass
- **WHEN** the AGENTS.md file is generated
- **THEN** the file is under 100 lines, serving as an index rather than a full document

### Requirement: Configurable output directory

The system SHALL accept a `--output` CLI flag specifying the directory where harness.json and AGENTS.md are written, defaulting to `.context/`.

#### Scenario: Custom output directory is used
- **WHEN** the CLI is invoked with `--output ./my-context/`
- **THEN** harness.json and AGENTS.md are written to `./my-context/`
