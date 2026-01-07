from mueta.core.config import LLMSettings, Settings

def test_llm_settings_defaults():
    """Test default values for LLMSettings."""
    llm = LLMSettings()
    assert llm.enable is False
    assert llm.provider == "openai"
    assert llm.api_key == ""
    assert llm.model == "gpt-4o-mini"
    assert llm.prompt_template is None

def test_settings_include_llm():
    """Test that Settings includes LLMSettings."""
    settings = Settings(
        audio_save_dir="/tmp",
        lyrics_save_dir="/tmp",
        acoustid_api_key="key",
        genius_api_key="key"
    )
    assert isinstance(settings.llm, LLMSettings)
    assert settings.llm.enable is False
