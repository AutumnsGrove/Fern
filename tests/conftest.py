"""Pytest configuration and fixtures for Fern tests."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import numpy as np


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables and paths."""
    # Use temporary directory for test data
    with tempfile.TemporaryDirectory() as temp_dir:
        test_home = Path(temp_dir) / ".fern"
        test_home.mkdir(parents=True, exist_ok=True)
        
        # Mock home directory for tests
        with patch("pathlib.Path.home", return_value=Path(temp_dir)):
            with patch.dict(os.environ, {"HOME": str(Path(temp_dir))}):
                yield {"test_home": test_home, "temp_dir": temp_dir}


@pytest.fixture
def mock_console():
    """Mock Rich console for testing CLI output."""
    mock_console = MagicMock()
    return mock_console


@pytest.fixture
def sample_audio_data():
    """Generate sample audio data for testing."""
    # Generate 1 second of synthetic audio at 44100 Hz
    sample_rate = 44100
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Generate a 440 Hz sine wave (A note)
    frequency = 440.0
    audio_data = np.sin(2 * np.pi * frequency * t) * 0.3
    
    return audio_data.astype(np.float32)


@pytest.fixture
def mock_parselmouth_sound():
    """Mock parselmouth Sound object."""
    mock_sound = MagicMock()
    mock_pitch = MagicMock()
    
    # Mock pitch values - some voiced, some unvoiced
    pitch_values = np.array([440.0, 0.0, 455.0, 0.0, 442.0, 0.0, 448.0])
    mock_pitch.selected_array = {'frequency': pitch_values}
    
    with patch("parselmouth.Sound", return_value=mock_sound):
        with patch("parselmouth.praat.call", return_value=mock_pitch):
            yield {
                'sound': mock_sound,
                'pitch': mock_pitch,
                'pitch_values': pitch_values
            }


@pytest.fixture
def mock_sounddevice():
    """Mock sounddevice for testing."""
    with patch("sounddevice.rec") as mock_rec:
        with patch("sounddevice.wait") as mock_wait:
            mock_rec.return_value = np.random.random((22050, 1)).astype(np.float32)
            mock_wait.return_value = None
            yield {
                'rec': mock_rec,
                'wait': mock_wait
            }


@pytest.fixture
def mock_librosa():
    """Mock librosa for testing."""
    with patch("librosa.load") as mock_load:
        mock_load.return_value = (
            np.random.random(44100).astype(np.float32),
            44100
        )
        yield {'load': mock_load}


@pytest.fixture
def cli_runner():
    """Create a Typer test runner for CLI testing."""
    from typer.testing import CliRunner
    from fern.cli import app
    
    runner = CliRunner()
    return runner


@pytest.fixture
def mock_config_data():
    """Mock configuration data."""
    return {
        'target_pitch_range': {
            'min': 80.0,
            'max': 250.0
        },
        'audio': {
            'sample_rate': 44100,
            'channels': 1,
            'device': None
        },
        'analysis': {
            'pitch_min': 75.0,
            'pitch_max': 600.0
        }
    }


@pytest.fixture(autouse=True)
def suppress_warnings():
    """Suppress warnings during tests."""
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        yield