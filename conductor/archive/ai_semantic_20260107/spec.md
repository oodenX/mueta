# Spec: Implement AI-Powered Genre and Mood Detection (v0.3.0)

## Background
Abstract metadata like "Genre" and "Mood" are often subjective. This track implements semantic prediction using Essentia's TensorFlow models (specifically Discogs-Effnet and MTG-Jamendo mood models) to provide accurate, locally-computed semantic attributes.

## Requirements
- **ML Engine:** Leverage existing `MLPredictor` and `ModelManager` to download and run models.
- **Data Input:** Raw audio signal (decoded and resampled to 16kHz).
- **Output:** Predicted "Genre" and "Mood" strings based on probability thresholds.
- **Configuration:** Users can configure:
    - Thresholds for genre and mood detection.
    - Model download directory.
    - Max number of genres/moods to return.
- **Pipeline Integration:** Add a `SemanticStage` to the existing metadata pipeline using the `MLPredictor`.
- **Tagging:** Update the `Tagger` to write these new fields to audio files.

## Acceptance Criteria
- [ ] Genre and Mood are successfully predicted using Essentia models.
- [ ] Predicted metadata is written correctly to the file's tags (ID3, Vorbis, etc.).
- [ ] The feature can be toggled via a CLI flag (e.g., `--analyze`).
- [ ] Configuration is managed via `MLSettings` in `mueta` config file.
- [ ] Integration tests verify the end-to-end flow with real audio files.