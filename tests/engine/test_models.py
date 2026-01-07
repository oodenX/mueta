from mueta.engine.models import SemanticResult

def test_semantic_result_model():
    """Test that SemanticResult model can be instantiated with valid data."""
    result = SemanticResult(
        genre="Pop",
        mood="Happy"
    )
    assert result.genre == "Pop"
    assert result.mood == "Happy"

def test_semantic_result_defaults():
    """Test defaults for SemanticResult."""
    result = SemanticResult()
    assert result.genre is None
    assert result.mood is None
