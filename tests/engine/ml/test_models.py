import pytest
from pathlib import Path
from mueta.engine.ml.models import ModelManager, MODELS

def test_model_manager_init(tmp_path):
    """Test ModelManager initialization."""
    manager = ModelManager(model_dir=tmp_path)
    assert manager.model_dir == tmp_path
    assert tmp_path.exists()

def test_list_available_models():
    """Test listing available models."""
    manager = ModelManager()
    models = manager.list_available_models()
    assert "discogs-effnet" in models
    assert "genre-discogs400" in models
    assert "mood-mtg-jamendo" in models

def test_get_model_path_invalid():
    """Test getting path for unknown model."""
    manager = ModelManager()
    assert manager.get_model_path("non-existent") is None
