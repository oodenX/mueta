from typer.testing import CliRunner
from mueta.cli.commands import app
from unittest.mock import patch, MagicMock

runner = CliRunner()

@patch('mueta.engine.pipeline.MetaPipeline')
@patch('mueta.engine.tagger.TaggerService')
def test_get_meta_defaults(mock_tagger_cls, mock_pipeline_cls, tmp_path):
    """Test that embedded default is False."""
    # Mock file existence
    file_path = tmp_path / "test.mp3"
    file_path.touch()
    
    mock_tagger = mock_tagger_cls.return_value
    mock_tagger.validate_audio_file.return_value = (True, "")
    
    mock_pipeline = mock_pipeline_cls.return_value
    mock_pipeline.process_file.return_value = MagicMock(success=True)
    
    result = runner.invoke(app, ["get-meta", str(file_path)])
    
    assert result.exit_code == 0
    
    # Check call args to process_file
    args, _ = mock_pipeline.process_file.call_args
    options = args[1]
    
    assert options.embed_lyrics is False
    assert options.download_lyrics is False
    assert options.embed_cover is True # Cover is True by default

@patch('mueta.engine.pipeline.MetaPipeline')
@patch('mueta.engine.tagger.TaggerService')
def test_get_meta_from_folder_defaults(mock_tagger_cls, mock_pipeline_cls, tmp_path):
    """Test that embedded default is False for folder command."""
    folder = tmp_path / "music"
    folder.mkdir()
    (folder / "test.mp3").touch()
    
    mock_tagger = mock_tagger_cls.return_value
    mock_tagger.validate_audio_file.return_value = (True, "")
    
    mock_pipeline = mock_pipeline_cls.return_value
    mock_pipeline.process_file.return_value = MagicMock(success=True)
    
    result = runner.invoke(app, ["get-meta-from-folder", str(folder)])
    
    assert result.exit_code == 0
    
    # Check call args (it calls get_meta internal logic which calls process_file)
    # Since get_meta logic is reused, we check the last call to process_file
    args, _ = mock_pipeline.process_file.call_args
    options = args[1]
    
    assert options.embed_lyrics is False
