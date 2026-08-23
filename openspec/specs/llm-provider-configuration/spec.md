# llm-provider-configuration Specification

## Purpose
Resolve the LLM backend — endpoint, API key, and model — from configuration so the tool runs against local Ollama by default and any OpenAI-compatible provider (e.g. DeepSeek) when configured, without code changes.

## Requirements

### Requirement: Configurable LLM backend via environment variables

The system SHALL resolve the LLM base URL, API key, and model from environment variables, defaulting to local Ollama (`http://localhost:11434/v1`, key `ollama`, model `qwen2.5:14b`) when they are unset.

#### Scenario: Default backend is local Ollama
- **WHEN** no backend environment variables are set
- **THEN** the classifier targets `http://localhost:11434/v1` with key `ollama` and model `qwen2.5:14b`

#### Scenario: Remote provider is selected via environment
- **WHEN** `HARNESS_LLM_BASE_URL`, `HARNESS_LLM_API_KEY`, and `HARNESS_LLM_MODEL` are set to a DeepSeek endpoint, key, and model
- **THEN** the classifier targets that endpoint, key, and model with no code change

### Requirement: Model override via CLI flag

The system SHALL accept a `--model` CLI flag that overrides the resolved model for a single run, taking precedence over the `HARNESS_LLM_MODEL` environment variable and the default.

#### Scenario: Model flag overrides the default
- **WHEN** the CLI is invoked with `--model deepseek-chat` and no `HARNESS_LLM_MODEL` is set
- **THEN** classification runs against the `deepseek-chat` model on the resolved base URL

### Requirement: Active backend is reported at startup

The system SHALL log the resolved backend (base URL and model) before classification begins.

#### Scenario: Backend is logged
- **WHEN** classification starts with a resolved backend
- **THEN** a log line reports the base URL and model in use
