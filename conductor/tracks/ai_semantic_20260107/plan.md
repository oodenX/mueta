# Plan: Implement AI-Powered Genre and Mood Detection (v0.3.0)

## Phase 1: Infrastructure and Configuration
- [ ] Task: Define Pydantic models for semantic results (Genre, Mood) in `src/mueta/engine/models.py`.
- [ ] Task: Update `src/mueta/core/config.py` to include LLM provider settings (API Key, Model, Provider).
- [ ] Task: Conductor - User Manual Verification 'Infrastructure and Configuration' (Protocol in workflow.md)

## Phase 2: Semantic Engine Implementation
- [ ] Task: Implement the base `SemanticEngine` class in `src/mueta/engine/semantic.py`.
- [ ] Task: Implement an OpenAI-compatible provider implementation.
- [ ] Task: Define and implement robust prompt templates for high-accuracy genre/mood extraction.
- [ ] Task: Implement error handling, retries, and fallback mechanisms for API failures.
- [ ] Task: Conductor - User Manual Verification 'Semantic Engine Implementation' (Protocol in workflow.md)

## Phase 3: Pipeline and CLI Integration
- [ ] Task: Implement `SemanticStage` in `src/mueta/engine/pipeline.py`.
- [ ] Task: Update the `Tagger` in `src/mueta/engine/tagger.py` to support writing Genre and Mood tags.
- [ ] Task: Integrate `SemanticStage` into the main `MetadataPipeline`.
- [ ] Task: Update CLI commands (`get-meta`, `get-meta-from-folder`) to include a `--semantic` flag.
- [ ] Task: Conductor - User Manual Verification 'Pipeline and CLI Integration' (Protocol in workflow.md)

## Phase 4: Final Verification and End-to-End Testing
- [ ] Task: Create integration tests that mock the LLM response but verify the full tagging flow.
- [ ] Task: Execute the full processing pipeline on the test dataset in `~/test/test_audio`.
- [ ] Task: Verify that output files in `~/test/output/` contain correct Genre and Mood tags.
- [ ] Task: Conductor - User Manual Verification 'Final Verification and End-to-End Testing' (Protocol in workflow.md)
