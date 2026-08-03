# CLI Startup Validation Specification

## Purpose

Ensures the CLI validates required configuration before starting any document processing pipeline, failing immediately with actionable error messages when preconditions are not met.

## Requirements

### Requirement: .env file is loaded at startup
The CLI SHALL load environment variables from a `.env` file located in the project root directory before executing any command logic.

#### Scenario: .env file exists with valid key
- **WHEN** a `.env` file exists in the project root with `OPENROUTER_API_KEY=sk-...`
- **THEN** the key SHALL be available via `os.environ["OPENROUTER_API_KEY"]` for all subsequent operations

#### Scenario: .env file does not exist
- **WHEN** no `.env` file exists in the project root
- **THEN** the CLI SHALL proceed without error; any missing keys SHALL be caught by the pre-flight validation step

#### Scenario: .env file has comments or empty lines
- **WHEN** the `.env` file contains blank lines or lines starting with `#`
- **THEN** those lines SHALL be ignored during parsing

---

### Requirement: Pre-flight API key validation
Before any document extraction or processing begins, the CLI SHALL verify that `OPENROUTER_API_KEY` is set (non-empty) in the environment if the classification phase will run.

#### Scenario: API key is set and non-empty
- **WHEN** `--tokens-only` is NOT set and `OPENROUTER_API_KEY` is a non-empty string
- **THEN** the CLI SHALL proceed with the full pipeline (extract → chunk → classify → merge → output)

#### Scenario: API key is missing or empty
- **WHEN** `--tokens-only` is NOT set and `OPENROUTER_API_KEY` is either not set or is an empty string
- **THEN** the CLI SHALL exit immediately with exit code 1 and an error message indicating the key is missing and where to set it

#### Scenario: API key is missing but tokens-only mode is active
- **WHEN** `--tokens-only` IS set
- **THEN** the CLI SHALL skip the API key check entirely, regardless of whether `OPENROUTER_API_KEY` is set

---

### Requirement: Pre-flight validation runs before extraction
The API key validation SHALL execute before any call to `extract()`, `DocumentConverter`, or any ML model loading.

#### Scenario: Key is missing, no extraction runs
- **WHEN** `OPENROUTER_API_KEY` is not set
- **THEN** the CLI SHALL exit without importing or initializing Docling's `DocumentConverter`
