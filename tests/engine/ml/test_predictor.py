import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from mueta.engine.ml.predictor import MLPredictor

@pytest.fixture
def mock_predictor():
    with patch('mueta.engine.ml.predictor.HAS_ESSENTIA_TF', True):
        predictor = MLPredictor()
        return predictor

def test_ml_predictor_init(mock_predictor):
    """Test MLPredictor initialization."""
    assert mock_predictor.enabled is True

@patch('mueta.engine.ml.predictor.MLPredictor._load_audio')
@patch('mueta.engine.ml.predictor.MLPredictor._extract_embeddings')
@patch('mueta.engine.ml.predictor.MLPredictor._get_genre_model')
def test_predict_genre(mock_get_genre_model, mock_extract_embeddings, mock_load_audio, mock_predictor):
    """Test genre prediction with mocks."""
    mock_load_audio.return_value = MagicMock()
    mock_extract_embeddings.return_value = MagicMock()
    
    # Mock genre model call
    mock_genre_model = MagicMock()
    # Return some probabilities
    import numpy as np
    # 400 classes, index 0 is "Electronic"
    mock_probs = np.zeros((1, 400))
    mock_probs[0, 0] = 0.9 
    mock_genre_model.return_value = mock_probs
    mock_get_genre_model.return_value = mock_genre_model
    
    # Mock classes
    mock_predictor.model_manager.get_genre_classes = MagicMock(return_value=["Electronic"] + ["Other"] * 399)
    
    genres = mock_predictor.predict_genre("test.mp3")
    assert "Electronic" in genres

@patch('mueta.engine.ml.predictor.MLPredictor._load_audio')
@patch('mueta.engine.ml.predictor.MLPredictor._extract_embeddings')
@patch('mueta.engine.ml.predictor.MLPredictor._get_mood_model')
def test_predict_mood(mock_get_mood_model, mock_extract_embeddings, mock_load_audio, mock_predictor):
    """Test mood prediction with mocks."""
    mock_load_audio.return_value = MagicMock()
    mock_extract_embeddings.return_value = MagicMock()
    
    # Mock mood model call
    mock_mood_model = MagicMock()
    import numpy as np
    # 56 classes, "happy" mapping to "Happy"
    mock_probs = np.zeros((1, 56))
    # We need to find the index for "happy" in Jamendo classes, but let's just mock get_mood_classes
    mock_probs[0, 0] = 0.9
    mock_mood_model.return_value = mock_probs
    mock_get_mood_model.return_value = mock_mood_model
    
    mock_predictor.model_manager.get_mood_classes = MagicMock(return_value=["happy"] + ["other"] * 55)
    
    moods = mock_predictor.predict_mood("test.mp3")
    assert "Happy" in moods

def test_predict_all(mock_predictor):
    """Test predict_all calls both genre and mood."""
    mock_predictor.predict_genre = MagicMock(return_value=["Electronic"])
    mock_predictor.predict_mood = MagicMock(return_value=["Happy"])
    
    result = mock_predictor.predict_all("test.mp3")
    assert result["genres"] == ["Electronic"]
    assert result["moods"] == ["Happy"]
