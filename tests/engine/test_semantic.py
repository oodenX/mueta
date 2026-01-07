import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from mueta.engine.semantic import SemanticAnalyzer

@pytest.fixture
def mock_analyzer():
    with patch('mueta.engine.semantic.settings') as mock_settings:
        mock_settings.ml.enable = True
        mock_settings.lastfm.enable = False
        analyzer = SemanticAnalyzer()
        return analyzer

@patch('mueta.engine.semantic.get_ml_predictor')
def test_analyze_prioritizes_ml_over_lastfm(mock_get_predictor, mock_analyzer):
    """Test that analyze calls ML predictor primarily."""
    mock_analyzer.enabled = True # Enable Last.fm
    mock_analyzer._analyze_lastfm = MagicMock(return_value={"genres": ["Pop"], "moods": ["Sad"]})
    
    mock_predictor = MagicMock()
    mock_predictor.is_available.return_value = True
    mock_predictor.predict_all.return_value = {"genres": ["Electronic"], "moods": ["Happy"]}
    mock_get_predictor.return_value = mock_predictor
    
    result = mock_analyzer.analyze("Artist", "Title", audio_file="test.mp3")
    
    # It should favor ML results
    assert result["genres"] == ["Electronic"]
    assert result["moods"] == ["Happy"]
