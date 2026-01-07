import os
from unittest.mock import patch
import pytest
from pydantic import ValidationError

def test_settings_validation_error_no_config():
    """Test that Settings does NOT raise ValidationError when config is missing."""
    # Ensure no env vars interfere
    with patch.dict(os.environ, clear=True):
        # We need to reload the module or patch where Settings is defined
        # But Settings.load_from_file() is called at module level in src/mueta/core/config.py
        # So we can try to instantiate Settings() directly with empty args
        from mueta.core.config import Settings
        
        # This should now succeed with defaults
        settings = Settings()
        assert settings.audio_save_dir
        assert settings.acoustid_api_key == ""
