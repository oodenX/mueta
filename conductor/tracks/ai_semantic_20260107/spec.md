# Spec: Implement AI-Powered Genre and Mood Detection (v0.3.0)

## Background
Abstract metadata like "Genre" and "Mood" are often subjective and difficult to determine using traditional fingerprinting or rigid database lookups. Large Language Models (LLMs) excel at synthesizing information from multiple text-based metadata fields (Title, Artist, Album) and acoustic features (BPM, Key) to provide accurate semantic predictions.

## Requirements
- **Semantic Engine:** A new core component responsible for interacting with LLM providers.
- **Provider Support:** Initial support for OpenAI/Claude or a generic OpenAI-compatible API.
- **Data Input:** The LLM should receive:
    - Track Title
    - Artist Name
    - Album Name
    - BPM (if available)
    - Key (if available)
- **Output:** Predicted "Genre" and "Mood" strings.
- **Configuration:** Users must be able to configure:
    - LLM Provider
    - API Key
    - Model Name
    - Custom Prompt (optional)
- **Pipeline Integration:** Add a `SemanticStage` to the existing metadata pipeline.
- **Tagging:** Update the `Tagger` to write these new fields to audio files.

## Acceptance Criteria
- [ ] Genre and Mood are successfully predicted for a given audio track.
- [ ] Predicted metadata is written correctly to the file's tags (ID3, Vorbis, etc.).
- [ ] The feature can be toggled via a CLI flag (e.g., `--semantic`).
- [ ] Configuration is managed via the standard `mueta` config file.
- [ ] Unit tests cover the `SemanticEngine` and `SemanticStage`.
- [ ] Integration tests verify the end-to-end flow with real audio files.
