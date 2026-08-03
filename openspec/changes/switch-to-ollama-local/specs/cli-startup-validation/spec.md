## REMOVED Requirements

### Requirement: .env file is loaded at startup

The `.env` file loading mechanism is removed. With Ollama as the local LLM backend, no API key or environment-based configuration is required for classification.

### Requirement: Pre-flight API key validation

The `OPENROUTER_API_KEY` validation is removed. The CLI no longer depends on any external API key for classification. The `--tokens-only` flag already bypasses all LLM calls, so no substitute validation is needed.

## MODIFIED Requirements

### Requirement: Pre-flight validation runs before extraction

Replace the API key check: the system SHALL NOT perform any pre-flight validation of the LLM backend before extraction. LLM connectivity errors (Ollama not running, model not pulled) SHALL surface naturally when the first classification call fails, with error messages from the OpenAI client providing actionable troubleshooting information.

#### Scenario: Ollama is not running
- **WHEN** classification is attempted and Ollama is unreachable
- **THEN** the CLI SHALL fail with a connection error pointing the user to start Ollama
