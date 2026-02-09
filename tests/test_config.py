"""Tests for Fern configuration management."""

import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open
import pytest
from typing import Dict, Any


class TestConfigModule:
    """Test the config module exists and can be imported."""

    def test_config_module_import(self):
        """Test that config module can be imported."""
        from fern import config
        assert config is not None

    def test_config_module_has_docstring(self):
        """Test that config module has proper documentation."""
        from fern import config
        assert config.__doc__ is not None
        assert "Configuration" in config.__doc__


class TestConfigInitialization:
    """Test configuration initialization and defaults."""

    def test_default_config_structure(self):
        """Test that default configuration has expected structure."""
        from fern.config import get_default_config
        
        default_config = get_default_config()
        
        # Test main sections exist
        assert "target_pitch_range" in default_config
        assert "audio" in default_config
        assert "analysis" in default_config
        
        # Test target pitch range
        target_range = default_config["target_pitch_range"]
        assert "min" in target_range
        assert "max" in target_range
        assert target_range["min"] < target_range["max"]
        
        # Test audio settings
        audio = default_config["audio"]
        assert "sample_rate" in audio
        assert "channels" in audio
        assert "device" in audio
        assert audio["sample_rate"] > 0
        assert audio["channels"] in [1, 2]
        
        # Test analysis settings
        analysis = default_config["analysis"]
        assert "pitch_min" in analysis
        assert "pitch_max" in analysis
        assert analysis["pitch_min"] < analysis["pitch_max"]

    def test_default_config_values(self, mock_config_data):
        """Test that default config values are reasonable."""
        from fern.config import get_default_config
        
        config = get_default_config()
        
        # Audio sample rate should be standard
        assert config["audio"]["sample_rate"] >= 16000
        assert config["audio"]["sample_rate"] <= 48000
        
        # Pitch range should be reasonable for voice
        assert 50 <= config["target_pitch_range"]["min"] <= 200
        assert 150 <= config["target_pitch_range"]["max"] <= 800
        
        # Analysis pitch range should be reasonable
        assert 50 <= config["analysis"]["pitch_min"] <= 200
        assert 400 <= config["analysis"]["pitch_max"] <= 1000


class TestConfigFileOperations:
    """Test configuration file read/write operations."""

    def test_save_config_to_file(self, mock_config_data, setup_test_environment):
        """Test saving configuration to file."""
        from fern.config import save_config
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = Path(f.name)
        
        try:
            save_config(mock_config_data, config_path)
            
            # Verify file was created and contains valid JSON
            assert config_path.exists()
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
            
            assert loaded_config == mock_config_data
        finally:
            if config_path.exists():
                config_path.unlink()

    def test_load_config_from_file(self, mock_config_data, setup_test_environment):
        """Test loading configuration from file."""
        from fern.config import load_config
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(mock_config_data, f)
            config_path = Path(f.name)
        
        try:
            loaded_config = load_config(config_path)
            assert loaded_config == mock_config_data
        finally:
            if config_path.exists():
                config_path.unlink()

    def test_load_nonexistent_config_file(self, setup_test_environment):
        """Test loading configuration from nonexistent file."""
        from fern.config import load_config
        from fern.config import ConfigFileNotFoundError
        
        nonexistent_path = Path("/nonexistent/config.json")
        
        with pytest.raises(ConfigFileNotFoundError):
            load_config(nonexistent_path)

    def test_load_corrupted_config_file(self, setup_test_environment):
        """Test loading configuration from corrupted JSON file."""
        from fern.config import load_config, InvalidConfigFileError
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json")
            config_path = Path(f.name)
        
        try:
            with pytest.raises(InvalidConfigFileError):
                load_config(config_path)
        finally:
            if config_path.exists():
                config_path.unlink()


class TestConfigValidation:
    """Test configuration validation."""

    def test_validate_valid_config(self, mock_config_data):
        """Test validation of valid configuration."""
        from fern.config import validate_config
        
        # Should not raise any exceptions
        validate_config(mock_config_data)

    def test_validate_invalid_config_missing_sections(self):
        """Test validation fails with missing required sections."""
        from fern.config import validate_config, InvalidConfigError
        
        invalid_config = {
            "target_pitch_range": {"min": 80, "max": 250}
            # Missing "audio" and "analysis" sections
        }
        
        with pytest.raises(InvalidConfigError):
            validate_config(invalid_config)

    def test_validate_invalid_pitch_range(self):
        """Test validation fails with invalid pitch range."""
        from fern.config import validate_config, InvalidConfigError
        
        invalid_config = {
            "target_pitch_range": {"min": 300, "max": 250},  # min > max
            "audio": {"sample_rate": 44100, "channels": 1, "device": None},
            "analysis": {"pitch_min": 75, "pitch_max": 600}
        }
        
        with pytest.raises(InvalidConfigError):
            validate_config(invalid_config)

    def test_validate_invalid_sample_rate(self):
        """Test validation fails with invalid sample rate."""
        from fern.config import validate_config, InvalidConfigError
        
        invalid_config = {
            "target_pitch_range": {"min": 80, "max": 250},
            "audio": {"sample_rate": 0, "channels": 1, "device": None},  # Invalid sample rate
            "analysis": {"pitch_min": 75, "pitch_max": 600}
        }
        
        with pytest.raises(InvalidConfigError):
            validate_config(invalid_config)

    def test_validate_invalid_channels(self):
        """Test validation fails with invalid channel count."""
        from fern.config import validate_config, InvalidConfigError
        
        invalid_config = {
            "target_pitch_range": {"min": 80, "max": 250},
            "audio": {"sample_rate": 44100, "channels": 5, "device": None},  # Invalid channels
            "analysis": {"pitch_min": 75, "pitch_max": 600}
        }
        
        with pytest.raises(InvalidConfigError):
            validate_config(invalid_config)


class TestConfigPaths:
    """Test configuration file path handling."""

    def test_get_default_config_path(self, setup_test_environment):
        """Test getting default configuration path."""
        from fern.config import get_default_config_path
        
        config_path = get_default_config_path()
        
        # Should be in .fern directory
        assert ".fern" in str(config_path)
        assert config_path.suffix == ".json"

    def test_create_config_directory(self, setup_test_environment):
        """Test that config directory is created if it doesn't exist."""
        from fern.config import get_default_config_path
        
        config_path = get_default_config_path()
        
        # Directory should exist or be created
        assert config_path.parent.exists() or config_path.parent.mkdir(parents=True)

    def test_config_path_with_env_variable(self, setup_test_environment):
        """Test configuration path respects environment variables."""
        from fern.config import get_default_config_path
        import tempfile

        # Use a temp directory for testing the env variable
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"FERN_CONFIG_DIR": temp_dir}):
                config_path = get_default_config_path()
                assert temp_dir in str(config_path)


class TestConfigUpdates:
    """Test configuration updates and modifications."""

    def test_update_config_section(self, mock_config_data):
        """Test updating a section of the configuration."""
        from fern.config import update_config
        
        new_audio_config = {"sample_rate": 22050, "channels": 2, "device": 1}
        updated_config = update_config(mock_config_data, "audio", new_audio_config)
        
        assert updated_config["audio"] == new_audio_config
        # Other sections should remain unchanged
        assert updated_config["target_pitch_range"] == mock_config_data["target_pitch_range"]

    def test_update_config_invalid_section(self, mock_config_data):
        """Test updating invalid configuration section."""
        from fern.config import update_config, InvalidConfigError
        
        with pytest.raises(InvalidConfigError):
            update_config(mock_config_data, "invalid_section", {})

    def test_merge_configs(self, mock_config_data):
        """Test merging configuration dictionaries."""
        from fern.config import merge_configs
        
        partial_config = {
            "target_pitch_range": {"min": 100, "max": 300},
            "new_section": {"key": "value"}
        }
        
        merged = merge_configs(mock_config_data, partial_config)
        
        # Should update target_pitch_range
        assert merged["target_pitch_range"] == {"min": 100, "max": 300}
        
        # Should add new section
        assert merged["new_section"] == {"key": "value"}
        
        # Should keep unchanged sections
        assert merged["audio"] == mock_config_data["audio"]


class TestConfigIntegration:
    """Test configuration integration with other components."""

    def test_config_integration_with_analysis(self, mock_config_data):
        """Test that configuration works with analysis module."""
        from fern.config import get_analysis_parameters
        
        params = get_analysis_parameters(mock_config_data)
        
        # Should extract analysis-specific parameters
        assert "pitch_min" in params
        assert "pitch_max" in params
        assert "sample_rate" in params
        
        assert params["pitch_min"] == mock_config_data["analysis"]["pitch_min"]
        assert params["pitch_max"] == mock_config_data["analysis"]["pitch_max"]
        assert params["sample_rate"] == mock_config_data["audio"]["sample_rate"]

    def test_config_integration_with_audio(self, mock_config_data):
        """Test that configuration works with audio settings."""
        from fern.config import get_audio_parameters
        
        audio_params = get_audio_parameters(mock_config_data)
        
        # Should extract audio-specific parameters
        assert "sample_rate" in audio_params
        assert "channels" in audio_params
        assert "device" in audio_params
        
        assert audio_params["sample_rate"] == mock_config_data["audio"]["sample_rate"]
        assert audio_params["channels"] == mock_config_data["audio"]["channels"]
        assert audio_params["device"] == mock_config_data["audio"]["device"]


class TestConfigErrorHandling:
    """Test configuration error handling."""

    def test_config_with_type_errors(self, mock_config_data):
        """Test handling of configuration type errors."""
        from fern.config import validate_config, InvalidConfigError
        
        # Replace numeric values with strings
        invalid_config = mock_config_data.copy()
        invalid_config["audio"]["sample_rate"] = "44100"  # Should be int
        
        with pytest.raises(InvalidConfigError):
            validate_config(invalid_config)

    def test_config_with_missing_keys(self, mock_config_data):
        """Test handling of configuration with missing keys."""
        from fern.config import validate_config, InvalidConfigError
        
        # Remove required key
        invalid_config = mock_config_data.copy()
        del invalid_config["audio"]["sample_rate"]
        
        with pytest.raises(InvalidConfigError):
            validate_config(invalid_config)

    def test_config_with_extra_keys(self, mock_config_data):
        """Test that extra keys in config are tolerated."""
        from fern.config import validate_config
        
        # Add extra keys (should be tolerated)
        valid_config = mock_config_data.copy()
        valid_config["extra_section"] = {"extra_key": "extra_value"}
        valid_config["audio"]["extra_audio_key"] = "extra_value"
        
        # Should not raise exception
        validate_config(valid_config)


class TestConfigPersistence:
    """Test configuration persistence across sessions."""

    def test_config_persistence_across_sessions(self, mock_config_data, setup_test_environment):
        """Test that config persists and can be reloaded."""
        from fern.config import save_config, load_config, get_default_config_path
        
        config_path = get_default_config_path()
        
        # Save config
        save_config(mock_config_data, config_path)
        
        # Clear current config and reload
        loaded_config = load_config(config_path)
        
        # Should be identical
        assert loaded_config == mock_config_data

    def test_config_backup_creation(self, mock_config_data, setup_test_environment):
        """Test that config backup is created when saving."""
        from fern.config import save_config_with_backup, get_default_config_path
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            original_config_path = Path(f.name)
            json.dump(mock_config_data, f)
        
        try:
            save_config_with_backup(mock_config_data, original_config_path)
            
            # Should create backup file
            backup_path = Path(str(original_config_path) + ".backup")
            assert backup_path.exists()
            
            # Backup should be identical to original
            with open(backup_path, 'r') as f:
                backup_config = json.load(f)
            
            assert backup_config == mock_config_data
        finally:
            for path in [original_config_path, Path(str(original_config_path) + ".backup")]:
                if path.exists():
                    path.unlink()


class TestConfigEdgeCases:
    """Test configuration edge cases and boundary conditions."""

    def test_empty_config_file(self, setup_test_environment):
        """Test handling of empty configuration file."""
        from fern.config import load_config, InvalidConfigFileError
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("")
            config_path = Path(f.name)
        
        try:
            with pytest.raises(InvalidConfigFileError):
                load_config(config_path)
        finally:
            if config_path.exists():
                config_path.unlink()

    def test_config_with_unicode_characters(self, mock_config_data):
        """Test configuration with Unicode characters."""
        from fern.config import validate_config, save_config
        import tempfile
        
        # Add Unicode characters
        unicode_config = mock_config_data.copy()
        unicode_config["metadata"] = {
            "name": "Fern Config",
            "description": "Configuration for Fern voice training 🎤",
            "author": "José García"
        }
        
        # Should handle Unicode gracefully
        validate_config(unicode_config)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = Path(f.name)
        
        try:
            save_config(unicode_config, config_path)
            
            # Should be able to reload
            from fern.config import load_config
            loaded = load_config(config_path)
            assert loaded["metadata"]["name"] == "Fern Config"
            assert "🎤" in loaded["metadata"]["description"]
        finally:
            if config_path.exists():
                config_path.unlink()

    def test_config_with_very_long_values(self, mock_config_data):
        """Test configuration with very long string values."""
        from fern.config import validate_config
        
        long_value_config = mock_config_data.copy()
        long_value_config["metadata"] = {
            "description": "A" * 10000  # Very long string
        }
        
        # Should handle long values
        validate_config(long_value_config)

    def test_config_with_special_numbers(self, mock_config_data):
        """Test configuration with special numeric values."""
        from fern.config import validate_config
        
        special_numbers_config = mock_config_data.copy()
        special_numbers_config["audio"]["sample_rate"] = 44100.5  # Float sample rate
        special_numbers_config["analysis"]["pitch_min"] = 75.0    # Float pitch
        
        # Should handle float values (might convert to int)
        validate_config(special_numbers_config)