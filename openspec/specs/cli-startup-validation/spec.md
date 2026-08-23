# CLI Startup Validation Specification

## Purpose

Ensures the CLI validates required configuration before starting any document processing pipeline, failing immediately with actionable error messages when preconditions are not met.

## Requirements

### Requirement: Pre-flight validation runs before extraction

Replace the API key check: the system SHALL NOT perform any pre-flight validation of the LLM backend before extraction. LLM connectivity errors (Ollama not running, model not pulled) SHALL surface naturally when the first classification call fails, with error messages from the OpenAI client providing actionable troubleshooting information.

#### Scenario: Key is missing, no extraction runs
- **WHEN** no LLM API key is configured and classification begins
- **THEN** the CLI SHALL proceed without a pre-flight key check; any backend error surfaces on the first classification call

#### Scenario: Ollama is not running
- **WHEN** classification is attempted and Ollama is unreachable
- **THEN** the CLI SHALL fail with a connection error pointing the user to start Ollama
