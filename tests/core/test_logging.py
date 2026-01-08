import os
import pytest
from mueta.core.logging import setup_logging

def test_setup_logging_suppresses_tensorflow_logs():
    """Test that setup_logging sets TF_CPP_MIN_LOG_LEVEL environment variable."""
    # Ensure variable is not set or reset
    if 'TF_CPP_MIN_LOG_LEVEL' in os.environ:
        del os.environ['TF_CPP_MIN_LOG_LEVEL']
    
    setup_logging(debug=False)
    
    assert os.environ.get('TF_CPP_MIN_LOG_LEVEL') == '3'

def test_setup_logging_debug_mode():
    """Test that setup_logging still sets TF logs to FATAL even in debug mode to avoid noise."""
    if 'TF_CPP_MIN_LOG_LEVEL' in os.environ:
        del os.environ['TF_CPP_MIN_LOG_LEVEL']
        
    setup_logging(debug=True)
    
    assert os.environ.get('TF_CPP_MIN_LOG_LEVEL') == '3'
