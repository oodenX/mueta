# Plan: Implement AI-Powered Genre and Mood Detection (v0.3.0)

## Phase 1: Infrastructure and Configuration
- [x] Task: Define Pydantic models for semantic results (Genre, Mood) in `src/mueta/engine/models.py`. 2ca0041
- [x] Task: Refine `src/mueta/core/config.py` and `MLSettings` to support advanced semantic options. 0a37e8d
- [ ] Task: Conductor - User Manual Verification 'Infrastructure and Configuration' (Protocol in workflow.md)

## Phase 2: ML Engine Refinement
- [x] Task: Ensure `src/mueta/engine/ml/models.py` correctly handles all required models (Discogs-Effnet, Genre-Discogs400, MTG-Jamendo). 97bb44d
- [x] Task: Verify `src/mueta/engine/ml/predictor.py` provides high-level `predict_all` functionality. 97bb44d
- [x] Task: Implement unit tests for `MLPredictor`. 97bb44d
- [ ] Task: Conductor - User Manual Verification 'ML Engine Refinement' (Protocol in workflow.md)

## Phase 3: Pipeline and CLI Integration
- [~] Task: Implement `SemanticStage` in `src/mueta/engine/pipeline.py` using `MLPredictor`.
- [ ] Task: Update the `Tagger` in `src/mueta/engine/tagger.py` to support writing multiple Genre and Mood tags.
- [ ] Task: Integrate `SemanticStage` into the main `MetadataPipeline`.
- [ ] Task: Update CLI commands (`get-meta`, `get-meta-from-folder`) to ensure `--analyze` triggers semantic detection.
- [ ] Task: Conductor - User Manual Verification 'Pipeline and CLI Integration' (Protocol in workflow.md)

## Phase 4: Final Verification and End-to-End Testing
- [ ] Task: Execute the full processing pipeline on the test dataset in `~/test/test_audio`.
- [ ] Task: Verify that output files in `~/test/output/` contain correct Genre and Mood tags using `mueta view-meta`.
- [ ] Task: Conductor - User Manual Verification 'Final Verification and End-to-End Testing' (Protocol in workflow.md)