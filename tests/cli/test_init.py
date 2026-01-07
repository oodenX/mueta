from typer.testing import CliRunner
from mueta.cli.commands import app
import os
from unittest.mock import patch, MagicMock

runner = CliRunner()

@patch('mueta.utils.system.check_fpcalc')
@patch('mueta.core.config.Settings._get_config_path')
def test_init_command(mock_get_config_path, mock_check_fpcalc, tmp_path):
    """Test that init command runs successfully."""
    # Mock fpcalc check to avoid dependency on system
    mock_check_fpcalc.return_value = (True, "")
    
    # Mock config path to use a temp file
    config_file = tmp_path / "config.toml"
    mock_get_config_path.return_value = config_file
    
    # We need to mock input because init asks for paths and API key
    # Inputs: Continue? (if fpcalc missing - mocked to present), Audio Dir, Lyrics Dir, API Key, Genius Key
    # With fpcalc present, it asks: Audio Dir, Lyrics Dir, API Key, Genius Key
    
    # Mock network validation for API key
    with patch('httpx.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"status": "ok"}
        
        result = runner.invoke(app, ["init"], input="\n\ntest_key\n\n")
    
    assert result.exit_code == 0
    assert "Configuration saved" in result.stdout
    assert config_file.exists()
