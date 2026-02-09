"""Configuration management.

Handles Fern configuration, target ranges, and user preferences.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigError(Exception):
    """Base exception for configuration errors."""
    pass


class ConfigFileNotFoundError(ConfigError):
    """Raised when configuration file is not found."""
    pass


class InvalidConfigFileError(ConfigError):
    """Raised when configuration file is invalid."""
    pass


class InvalidConfigError(ConfigError):
    """Raised when configuration validation fails."""
    pass


def get_default_config() -> Dict[str, Any]:
    """Get the default configuration for Fern.

    Returns:
        Dictionary containing default configuration values.
    """
    return {
        "target_pitch_range": {
            "min": 80.0,
            "max": 250.0
        },
        "audio": {
            "sample_rate": 44100,
            "channels": 1,
            "device": None
        },
        "analysis": {
            "pitch_min": 75.0,
            "pitch_max": 600.0
        }
    }


def get_default_config_path() -> Path:
    """Get the default path for the configuration file.

    Returns:
        Path to the default configuration file location.
    """
    # Check for environment variable override
    if "FERN_CONFIG_DIR" in os.environ:
        config_dir = Path(os.environ["FERN_CONFIG_DIR"])
    else:
        config_dir = Path.home() / ".fern"

    # Ensure directory exists
    config_dir.mkdir(parents=True, exist_ok=True)

    return config_dir / "config.json"


def save_config(config: Dict[str, Any], path: Path) -> None:
    """Save configuration to a JSON file.

    Args:
        config: Configuration dictionary to save.
        path: Path to the output file.
    """
    # Validate before saving
    validate_config(config)

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def save_config_with_backup(config: Dict[str, Any], path: Path) -> None:
    """Save configuration with a backup of the existing file.

    Args:
        config: Configuration dictionary to save.
        path: Path to the configuration file.
    """
    # Create backup if file exists
    if path.exists():
        backup_path = Path(str(path) + ".backup")
        backup_path.unlink(missing_ok=True)
        path.rename(backup_path)

    save_config(config, path)


def load_config(path: Path) -> Dict[str, Any]:
    """Load configuration from a JSON file.

    Args:
        path: Path to the configuration file.

    Returns:
        Parsed configuration dictionary.

    Raises:
        ConfigFileNotFoundError: If the file doesn't exist.
        InvalidConfigFileError: If the file contains invalid JSON.
    """
    if not path.exists():
        raise ConfigFileNotFoundError(f"Configuration file not found: {path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                raise InvalidConfigFileError("Configuration file is empty")
            config = json.loads(content)
    except json.JSONDecodeError as e:
        raise InvalidConfigFileError(f"Invalid JSON in configuration file: {e}")

    return config


def validate_config(config: Dict[str, Any]) -> None:
    """Validate configuration dictionary.

    Args:
        config: Configuration to validate.

    Raises:
        InvalidConfigError: If validation fails.
    """
    required_sections = ["target_pitch_range", "audio", "analysis"]

    # Check required sections
    for section in required_sections:
        if section not in config:
            raise InvalidConfigError(f"Missing required section: {section}")

    # Validate target_pitch_range
    target = config["target_pitch_range"]
    if "min" not in target or "max" not in target:
        raise InvalidConfigError("target_pitch_range must have 'min' and 'max' keys")
    if not isinstance(target["min"], (int, float)) or not isinstance(target["max"], (int, float)):
        raise InvalidConfigError("target_pitch_range min/max must be numeric")
    if target["min"] >= target["max"]:
        raise InvalidConfigError("target_pitch_range min must be less than max")

    # Validate audio settings
    audio = config["audio"]
    if "sample_rate" not in audio:
        raise InvalidConfigError("audio must have 'sample_rate' key")
    if not isinstance(audio["sample_rate"], (int, float)) or audio["sample_rate"] <= 0:
        raise InvalidConfigError("audio.sample_rate must be a positive number")
    if "channels" not in audio:
        raise InvalidConfigError("audio must have 'channels' key")
    if audio["channels"] not in [1, 2]:
        raise InvalidConfigError("audio.channels must be 1 or 2")

    # Validate analysis settings
    analysis = config["analysis"]
    if "pitch_min" not in analysis or "pitch_max" not in analysis:
        raise InvalidConfigError("analysis must have 'pitch_min' and 'pitch_max' keys")
    if not isinstance(analysis["pitch_min"], (int, float)) or not isinstance(analysis["pitch_max"], (int, float)):
        raise InvalidConfigError("analysis pitch_min/pitch_max must be numeric")
    if analysis["pitch_min"] >= analysis["pitch_max"]:
        raise InvalidConfigError("analysis pitch_min must be less than pitch_max")


def update_config(config: Dict[str, Any], section: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update a section of the configuration.

    Args:
        config: Original configuration.
        section: Section to update.
        updates: Dictionary of updates for the section.

    Returns:
        Updated configuration dictionary.

    Raises:
        InvalidConfigError: If section doesn't exist.
    """
    if section not in config:
        raise InvalidConfigError(f"Invalid configuration section: {section}")

    new_config = config.copy()
    new_config[section] = {**config[section], **updates}

    return new_config


def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two configuration dictionaries.

    Args:
        base: Base configuration.
        override: Configuration values to override.

    Returns:
        Merged configuration.
    """
    merged = base.copy()
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = merge_configs(merged[key], value)
        else:
            merged[key] = value
    return merged


def get_analysis_parameters(config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract analysis parameters from configuration.

    Args:
        config: Full configuration dictionary.

    Returns:
        Dictionary with analysis-specific parameters.
    """
    return {
        "pitch_min": config["analysis"]["pitch_min"],
        "pitch_max": config["analysis"]["pitch_max"],
        "sample_rate": config["audio"]["sample_rate"]
    }


def get_audio_parameters(config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract audio parameters from configuration.

    Args:
        config: Full configuration dictionary.

    Returns:
        Dictionary with audio-specific parameters.
    """
    return {
        "sample_rate": config["audio"]["sample_rate"],
        "channels": config["audio"]["channels"],
        "device": config["audio"]["device"]
    }
