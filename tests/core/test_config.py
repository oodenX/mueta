from mueta.core.config import MLSettings, Settings

def test_ml_settings_defaults():
    """Test default values for MLSettings."""
    ml = MLSettings()
    assert ml.enable is True
    assert ml.genre_threshold == 0.1
    assert ml.mood_threshold == 0.3
    assert ml.max_genres == 5
    assert ml.max_moods == 3

def test_settings_include_ml():
    """Test that Settings includes MLSettings."""
    settings = Settings(
        audio_save_dir="/tmp",
        lyrics_save_dir="/tmp",
        acoustid_api_key="key",
        genius_api_key="key"
    )
    assert isinstance(settings.ml, MLSettings)
    assert settings.ml.enable is True