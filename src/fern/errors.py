"""Fern Error Codes System.

Unique, personalized error codes for easier debugging and user experience.
Each error has a unique code, friendly message, technical details, and suggestions.

Error Code Format: FERN-XXX
    - FERN: Fern project identifier
    - XXX: Three-digit error code

Categories:
    000-099: Core/General errors
    100-199: Audio/Capture errors
    200-299: Analysis errors
    300-399: Database errors
    400-499: Configuration errors
    500-599: CLI/Command errors
    600-699: WebSocket/IPC errors
    700-799: Hammerspoon/GUI errors
    900-999: Fatal/Recovery errors
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from functools import lru_cache
from typing import Optional, Dict, Any, List
import sys
import os


class ErrorSeverity(Enum):
    """Error severity levels."""
    INFO = auto()       # Informational, not an error
    WARNING = auto()    # Warning, operation may be affected
    ERROR = auto()      # Error, operation failed but recoverable
    FATAL = auto()      # Fatal error, cannot continue


class ErrorCategory(Enum):
    """Error categories by system component."""
    CORE = "Core"
    AUDIO = "Audio/Capture"
    ANALYSIS = "Analysis"
    DATABASE = "Database"
    CONFIG = "Configuration"
    CLI = "CLI/Command"
    WEBSOCKET = "WebSocket/IPC"
    GUI = "Hammerspoon/GUI"
    UNKNOWN = "Unknown"


@dataclass
class FernError(Exception):
    """Complete error information."""
    code: str
    message: str
    severity: ErrorSeverity
    category: ErrorCategory
    technical_details: str = ""
    suggestions: List[str] = field(default_factory=list)
    original_exception: Optional[Exception] = None
    context: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """Format error for display."""
        lines = [
            f"[bold red]🌿 Error {self.code}[/bold red]",
            f"[yellow]{self.message}[/yellow]",
        ]

        if self.suggestions:
            lines.append("")
            lines.append("[bold]Suggestions:[/bold]")
            for suggestion in self.suggestions:
                lines.append(f"  • {suggestion}")

        if self.technical_details and os.getenv("FERN_DEBUG"):
            lines.append("")
            lines.append("[dim]Technical Details:[/dim]")
            lines.append(f"  {self.technical_details}")

        return "\n".join(lines)


# Cache for error registry
_error_registry: Dict[str, FernError] = {}


def register_error(error: FernError) -> None:
    """Register an error in the global registry."""
    _error_registry[error.code] = error


def get_error(code: str) -> Optional[FernError]:
    """Get an error by its code."""
    return _error_registry.get(code)


def get_all_errors() -> Dict[str, FernError]:
    """Get all registered errors."""
    return _error_registry.copy()


# =============================================================================
# ERROR DEFINITIONS
# =============================================================================

# -----------------------------------------------------------------------------
# Core/General Errors (000-099)
# -----------------------------------------------------------------------------

register_error(FernError(
    code="FERN-000",
    message="An unknown error occurred",
    severity=ErrorSeverity.ERROR,
    category=ErrorCategory.CORE,
    technical_details="No specific error information available",
    suggestions=[
        "Run with FERN_DEBUG=1 for more details",
        "Check the logs in ~/.fern/fern.log",
        "Report this issue at https://github.com/autumnsgrove/fern/issues"
    ]
))

register_error(FernError(
    code="FERN-001",
    message="Fern is not initialized properly",
    severity=ErrorSeverity.FATAL,
    category=ErrorCategory.CORE,
    technical_details="Core initialization failed",
    suggestions=[
        "Try reinstalling Fern: uv pip install -e .",
        "Check that all dependencies are installed: uv sync",
        "Verify Python version is 3.11+: python3 --version"
    ]
))

register_error(FernError(
    code="FERN-002",
    message="Interrupted by user",
    severity=ErrorSeverity.INFO,
    category=ErrorCategory.CORE,
    technical_details="User sent interrupt signal (Ctrl+C)",
    suggestions=[
        "This is normal behavior when canceling an operation",
        "Your data has been saved up to this point"
    ]
))

register_error(FernError(
    code="FERN-003",
    message="File permission denied",
    severity=ErrorSeverity.ERROR,
    category=ErrorCategory.CORE,
    technical_details="Cannot read or write required file",
    suggestions=[
        "Check file permissions: ls -la <path>",
        "Ensure you have write access to the directory",
        "Try running with sudo (not recommended for regular use)"
    ]
))

register_error(FernError(
    code="FERN-004",
    message="Path does not exist",
    severity=ErrorSeverity.ERROR,
    category=ErrorCategory.CORE,
    technical_details="Required file or directory path is missing",
    suggestions=[
        "Verify the path is correct",
        "Create the required directory: mkdir -p <path>",
        "Run fern status to check your configuration"
    ]
))

# -----------------------------------------------------------------------------
# Audio/Capture Errors (100-199)
# -----------------------------------------------------------------------------

register_error(FernError(
    code="FERN-100",
    message="No microphone found",
    severity=ErrorSeverity.ERROR,
    category=ErrorCategory.AUDIO,
    technical_details="sounddevice could not find any audio input device",
    suggestions=[
        "Check System Settings → Privacy → Microphone",
        "Connect a microphone if none is attached",
        "Try specifying a device: fern test --device 0",
        "List available devices: fern test --list-devices"
    ]
))

register_error(FernError(
    code="FERN-101",
    message="Microphone access denied",
    severity=ErrorSeverity.ERROR,
    category=ErrorCategory.AUDIO,
    technical_details="macOS denied microphone access to Fern",
    suggestions=[
        "Open System Settings → Privacy & Security → Microphone",
        "Enable access for Terminal (or your terminal emulator)",
        "Restart Fern after granting permissions"
    ]
))

register_error(FernError(
    code="FERN-102",
    message="Audio device is already in use",
    severity=ErrorSeverity.ERROR,
    category=ErrorCategory.AUDIO,
    technical_details="The requested audio device is busy with another application",
    suggestions=[
        "Close other applications that might be using the microphone",
        "Select a different device: fern test --device <index>",
        "Wait for the other application to release the device"
    ]
))

register_error(FernError(
    code="FERN-103",
    message="Audio capture failed unexpectedly",
    severity=ErrorSeverity.ERROR,
    category=ErrorCategory.AUDIO,
    technical_details="sounddevice raised an unexpected exception during capture",
    suggestions=[
        "Try closing and reopening Fern",
        "Restart your computer if the issue persists",
        "Check System Settings → Sound → Input for device health"
    ]
))

register_error(FernError(
    code="FERN-104",
    message="Invalid audio sample rate",
    severity=ErrorSeverity.ERROR,
    category=ErrorCategory.AUDIO,
    technical_details="Requested sample rate not supported by device",
    suggestions=[
        "Use the default sample rate: fern test",
        "Check supported rates: fern test --list-devices",
        "Your device may not support the requested rate"
    ]
))

register_error(FernError(
    code="FERN-105",
    message="Audio buffer overflow",
    severity=ErrorSeverity.WARNING,
    category=ErrorCategory.AUDIO,
    technical_details="Audio data was lost due to buffer overflow",
    suggestions=[
        "This may happen with slow computers or high CPU load",
        "Try reducing other system activity during capture",
        "Consider increasing buffer size in config"
    ]
))

register_error(FernError(
    code="FERN-106",
    message="No audio input detected",
    severity=ErrorSeverity.WARNING,
    category=ErrorCategory.AUDIO,
    technical_details="Microphone is recording but no voice detected",
    suggestions=[
        "Check your microphone is not muted",
        "Speak louder or move closer to the microphone",
        "Verify the input level in System Settings → Sound"
    ]
))

# -----------------------------------------------------------------------------
# Analysis Errors (200-299)
# -----------------------------------------------------------------------------

register_error(FernError(
    code="FERN-200",
    message="Praat-parselmouth initialization failed",
    severity=ErrorSeverity.FATAL,
    category=ErrorCategory.ANALYSIS,
    technical_details="Could not load praat-parselmouth library",
    suggestions=[
        "Reinstall parselmouth: uv pip install praat-parselmouth",
        "Ensure you have a compatible Praon installation",
        "Check Python architecture matches (arm64 vs x86_64)"
    ]
))

register_error(FernError(
    code="FERN-201",
    message="No pitch detected in audio",
    severity=ErrorSeverity.WARNING,
    category=ErrorCategory.ANALYSIS,
    technical_details="Pitch analysis found no voiced segments",
    suggestions=[
        "Ensure you're speaking during capture",
        "Check microphone input level",
        "Try adjusting the pitch range in config",
        "This is normal for silence or non-voiced sounds"
    ]
))

register_error(FernError(
    code="FERN-202",
    message="Pitch detection out of range",
    severity=ErrorSeverity.WARNING,
    category=ErrorCategory.ANALYSIS,
    technical_details="Detected pitch is outside expected range",
    suggestions=[
        "Your pitch may be naturally higher or lower than typical",
        "Adjust target range: fern config:set-target <min> <max>",
        "This is not necessarily a problem - pitch varies naturally"
    ]
))

register_error(FernError(
    code="FERN-203",
    message="Resonance analysis failed",
    severity=ErrorSeverity.ERROR,
    category=ErrorCategory.ANALYSIS,
    technical_details="librosa could not extract formants",
    suggestions=[
        "Try capturing audio again with clearer speech",
        "Reduce background noise",
        "Ensure sufficient audio quality"
    ]
))

register_error(FernError(
    code="FERN-204",
    message="Audio file is corrupted or invalid",
    severity=ErrorSeverity.ERROR,
    category=ErrorCategory.ANALYSIS,
    technical_details="Could not decode audio data",
    suggestions=[
        "Try capturing fresh audio",
        "Check the audio file is not damaged",
        "Ensure audio is in a supported format (WAV recommended)"
    ]
))

register_error(FernError(
    code="FERN-205",
    message="Audio too short for analysis",
    severity=ErrorSeverity.WARNING,
    category=ErrorCategory.ANALYSIS,
    technical_details="Audio clip is shorter than minimum required duration",
    suggestions=[
        "Capture longer audio segments",
        "Try the default 5-second capture duration",
        "Short clips may not contain enough data for analysis"
    ]
))

# -----------------------------------------------------------------------------
# Database Errors (300-399)
# -----------------------------------------------------------------------------

register_error(FernError(
    code="FERN-300",
    message="Database connection failed",
    severity=ErrorSeverity.FATAL,
    category=ErrorCategory.DATABASE,
    technical_details="Could not connect to SQLite database",
    suggestions=[
        "Check database file exists: ls ~/.fern/fern.db",
        "Try restoring from backup: cp ~/.fern/fern.db.backup ~/.fern/fern.db",
        "Check file permissions on the database file"
    ]
))

register_error(FernError(
    code="FERN-301",
    message="Database is corrupted",
    severity=ErrorSeverity.FATAL,
    category=ErrorCategory.DATABASE,
    technical_details="SQLite reported corruption or invalid database",
    suggestions=[
        "Restore from backup: cp ~/.fern/fern.db.backup ~/.fern/fern.db",
        "If no backup exists, the database will be rebuilt (data may be lost)",
        "Report this issue if it happens repeatedly"
    ]
))

register_error(FernError(
    code="FERN-302",
    message="Database migration required",
    severity=ErrorSeverity.WARNING,
    category=ErrorCategory.DATABASE,
    technical_details="Database schema version is outdated",
    suggestions=[
        "This is normal after Fern updates",
        "Your data will be preserved during migration",
        "If migration fails, a backup will be created automatically"
    ]
))

register_error(FernError(
    code="FERN-303",
    message="Query returned no results",
    severity=ErrorSeverity.INFO,
    category=ErrorCategory.DATABASE,
    technical_details="Database query executed successfully but found no matching data",
    suggestions=[
        "This is normal for new installations",
        "Try capturing some audio first: fern test",
        "Expand your date range: fern trend --days 30"
    ]
))

register_error(FernError(
    code="FERN-304",
    message="Database constraint violation",
    severity=ErrorSeverity.ERROR,
    category=ErrorCategory.DATABASE,
    technical_details="Insert/update violated database constraints",
    suggestions=[
        "This is usually a programming error",
        "Report this issue at https://github.com/autumnsgrove/fern/issues",
        "Your data has been preserved"
    ]
))

register_error(FernError(
    code="FERN-305",
    message="Database disk is full",
    severity=ErrorSeverity.FATAL,
    category=ErrorCategory.DATABASE,
    technical_details="Cannot write to database - disk full",
    suggestions=[
        "Free up disk space: df -h",
        "Delete old audio clips: rm ~/.fern/clips/*.wav",
        "Consider enabling quarterly archiving"
    ]
))

# -----------------------------------------------------------------------------
# Configuration Errors (400-499)
# -----------------------------------------------------------------------------

register_error(FernError(
    code="FERN-400",
    message="Configuration file not found",
    severity=ErrorSeverity.WARNING,
    category=ErrorCategory.CONFIG,
    technical_details="Could not find config file at expected path",
    suggestions=[
        "A new config will be created with defaults",
        "Set custom path: FERN_CONFIG=/path/to/config fern status",
        "Default config path: ~/.fern/config.yaml"
    ]
))

register_error(FernError(
    code="FERN-401",
    message="Configuration file is corrupted",
    severity=ErrorSeverity.ERROR,
    category=ErrorCategory.CONFIG,
    technical_details="Could not parse YAML configuration",
    suggestions=[
        "Check for syntax errors in the config file",
        "Restore from backup: cp ~/.fern/config.yaml.backup ~/.fern/config.yaml",
        "A new default config will be created"
    ]
))

register_error(FernError(
    code="FERN-402",
    message="Invalid configuration value",
    severity=ErrorSeverity.ERROR,
    category=ErrorCategory.CONFIG,
    technical_details="Configuration value is out of valid range",
    suggestions=[
        "Check the valid range for this setting",
        "Run fern config:show to see current values",
        "Reset to defaults: rm ~/.fern/config.yaml"
    ]
))

register_error(FernError(
    code="FERN-403",
    message="Target pitch range is invalid",
    severity=ErrorSeverity.ERROR,
    category=ErrorCategory.CONFIG,
    technical_details="min_pitch must be less than max_pitch",
    suggestions=[
        "Set a valid range: fern config:set-target 80 250",
        "Minimum pitch should typically be 50-100 Hz",
        "Maximum pitch should typically be 200-400 Hz"
    ]
))

register_error(FernError(
    code="FERN-404",
    message="Unknown configuration key",
    severity=ErrorSeverity.WARNING,
    category=ErrorCategory.CONFIG,
    technical_details="Configuration contains unrecognized keys",
    suggestions=[
        "This may be from an older Fern version",
        "Unknown keys are ignored but may indicate configuration drift",
        "Consider regenerating config: rm ~/.fern/config.yaml"
    ]
))

# -----------------------------------------------------------------------------
# CLI/Command Errors (500-599)
# -----------------------------------------------------------------------------

register_error(FernError(
    code="FERN-500",
    message="Invalid command argument",
    severity=ErrorSeverity.ERROR,
    category=ErrorCategory.CLI,
    technical_details="Command received an invalid argument value",
    suggestions=[
        "Check the command help: fern <command> --help",
        "Verify argument types (numbers, paths, etc.)",
        "See usage examples in README.md"
    ]
))

register_error(FernError(
    code="FERN-501",
    message="Missing required argument",
    severity=ErrorSeverity.ERROR,
    category=ErrorCategory.CLI,
    technical_details="Required command argument was not provided",
    suggestions=[
        "Check the command help: fern <command> --help",
        "Provide all required arguments",
        "Example: fern review <session-id>"
    ]
))

register_error(FernError(
    code="FERN-502",
    message="Unknown command",
    severity=ErrorSeverity.ERROR,
    category=ErrorCategory.CLI,
    technical_details="Specified command does not exist",
    suggestions=[
        "List available commands: fern --help",
        "Check for typos in the command name",
        "Some commands may require plugins"
    ]
))

register_error(FernError(
    code="FERN-503",
    message="Session not found",
    severity=ErrorSeverity.ERROR,
    category=ErrorCategory.CLI,
    technical_details="Requested session ID does not exist",
    suggestions=[
        "List sessions: fern sessions",
        "Check the session ID is correct",
        "Session IDs are shown in fern sessions output"
    ]
))

register_error(FernError(
    code="FERN-504",
    message="Export format not supported",
    severity=ErrorSeverity.ERROR,
    category=ErrorCategory.CLI,
    technical_details="Requested export format is not available",
    suggestions=[
        "Supported formats: csv, json",
        "Try: fern export --format csv",
        "Check fern export --help for more options"
    ]
))

register_error(FernError(
    code="FERN-505",
    message="Output file cannot be written",
    severity=ErrorSeverity.ERROR,
    category=ErrorCategory.CLI,
    technical_details="Cannot create or write to the specified output file",
    suggestions=[
        "Check the file path is valid",
        "Ensure you have write permission in the target directory",
        "Try a different output path"
    ]
))

# -----------------------------------------------------------------------------
# WebSocket/IPC Errors (600-699)
# -----------------------------------------------------------------------------

register_error(FernError(
    code="FERN-600",
    message="WebSocket server not running",
    severity=ErrorSeverity.WARNING,
    category=ErrorCategory.WEBSOCKET,
    technical_details="Cannot connect to Fern WebSocket server",
    suggestions=[
        "Start the Fern server in the background",
        "The server may already be running on another port",
        "Fern will work in polling mode without WebSocket"
    ]
))

register_error(FernError(
    code="FERN-601",
    message="WebSocket connection refused",
    severity=ErrorSeverity.ERROR,
    category=ErrorCategory.WEBSOCKET,
    technical_details="Connection to WebSocket server was refused",
    suggestions=[
        "Check the server is running: ps aux | grep fern",
        "Verify the port is correct (default: 8765)",
        "Restart the server if necessary"
    ]
))

register_error(FernError(
    code="FERN-602",
    message="WebSocket protocol error",
    severity=ErrorSeverity.ERROR,
    category=ErrorCategory.WEBSOCKET,
    technical_details="Received invalid message from WebSocket",
    suggestions=[
        "This may indicate a version mismatch",
        "Try restarting both Fern and Hammerspoon",
        "Report this issue if it persists"
    ]
))

register_error(FernError(
    code="FERN-603",
    message="Signal file communication failed",
    severity=ErrorSeverity.WARNING,
    category=ErrorCategory.WEBSOCKET,
    technical_details="Could not read/write signal files for IPC",
    suggestions=[
        "Check /tmp directory permissions",
        "Ensure no other process is locking the signal files",
        "Fern will retry automatically"
    ]
))

# -----------------------------------------------------------------------------
# Hammerspoon/GUI Errors (700-799)
# -----------------------------------------------------------------------------

register_error(FernError(
    code="FERN-700",
    message="Hammerspoon not installed",
    severity=ErrorSeverity.FATAL,
    category=ErrorCategory.GUI,
    technical_details="Required Hammerspoon application not found",
    suggestions=[
        "Install Hammerspoon: brew install hammerspoon",
        "Or download from https://www.hammerspoon.org/",
        "Fern CLI will work without Hammerspoon"
    ]
))

register_error(FernError(
    code="FERN-701",
    message="Fern Lua module not found",
    severity=ErrorSeverity.ERROR,
    category=ErrorCategory.GUI,
    technical_details="Hammerspoon cannot find Fern Lua files",
    suggestions=[
        "Run ./install.sh to set up Hammerspoon",
        "Or manually: ln -s $(pwd)/hammerspoon ~/.hammerspoon/fern.lua",
        "Ensure all .lua files are in ~/.hammerspoon/"
    ]
))

register_error(FernError(
    code="FERN-702",
    message="Hammerspoon overlay failed to display",
    severity=ErrorSeverity.WARNING,
    category=ErrorCategory.GUI,
    technical_details="Could not create or show the overlay canvas",
    suggestions=[
        "Try reloading Hammerspoon: Ctrl+Cmd+R",
        "Check Hammerspoon console for errors (Window → Console)",
        "Ensure no other overlay is blocking the screen"
    ]
))

register_error(FernError(
    code="FERN-703",
    message="Chart data not available",
    severity=ErrorSeverity.INFO,
    category=ErrorCategory.GUI,
    technical_details="No chart data has been sent to Hammerspoon",
    suggestions=[
        "Run: fern chart --send",
        "Then toggle chart view: Ctrl+Alt+Shift+C",
        "Capture some audio first to generate data"
    ]
))

# -----------------------------------------------------------------------------
# Fatal/Recovery Errors (900-999)
# -----------------------------------------------------------------------------

register_error(FernError(
    code="FERN-900",
    message="Critical system error",
    severity=ErrorSeverity.FATAL,
    category=ErrorCategory.UNKNOWN,
    technical_details="A critical error occurred that prevents continued operation",
    suggestions=[
        "Check logs at ~/.fern/fern.log",
        "Try restarting Fern",
        "If this persists, please report this issue",
        "Your data has been preserved"
    ]
))

register_error(FernError(
    code="FERN-901",
    message="Out of memory",
    severity=ErrorSeverity.FATAL,
    category=ErrorCategory.UNKNOWN,
    technical_details="System ran out of available memory",
    suggestions=[
        "Close other applications to free memory",
        "Reduce audio buffer size in configuration",
        "Consider capturing shorter sessions"
    ]
))

register_error(FernError(
    code="FERN-902",
    message="Incompatible Python version",
    severity=ErrorSeverity.FATAL,
    category=ErrorCategory.UNKNOWN,
    technical_details="Python version does not meet requirements",
    suggestions=[
        "Fern requires Python 3.11 or later",
        "Your version: " + ".".join(map(str, sys.version_info[:3])),
        "Install a newer Python version from python.org or pyenv"
    ]
))


# =============================================================================
# ERROR FACTORY FUNCTIONS
# =============================================================================

def create_error(
    code: str,
    message: Optional[str] = None,
    severity: Optional[ErrorSeverity] = None,
    category: Optional[ErrorCategory] = None,
    technical_details: str = "",
    suggestions: Optional[List[str]] = None,
    original_exception: Optional[Exception] = None,
    context: Optional[Dict[str, Any]] = None,
) -> FernError:
    """Create a FernError from a registered error code.

    Args:
        code: The error code (e.g., "FERN-100")
        message: Optional override for the default message
        severity: Optional override for severity
        category: Optional override for category
        technical_details: Additional technical details
        suggestions: Additional suggestions
        original_exception: The original exception that caused this error
        context: Additional context information

    Returns:
        A FernError instance
    """
    # Look up base error from registry
    base_error = _error_registry.get(code)

    if base_error is None:
        # Unknown error code - create generic error
        return FernError(
            code=code,
            message=message or f"Unknown error: {code}",
            severity=severity or ErrorSeverity.ERROR,
            category=category or ErrorCategory.UNKNOWN,
            technical_details=technical_details,
            suggestions=suggestions or ["Report this error at https://github.com/autumnsgrove/fern/issues"],
            original_exception=original_exception,
            context=context or {}
        )

    # Create error with overrides
    return FernError(
        code=base_error.code,
        message=message or base_error.message,
        severity=severity or base_error.severity,
        category=category or base_error.category,
        technical_details=technical_details or base_error.technical_details,
        suggestions=suggestions or base_error.suggestions,
        original_exception=original_exception,
        context=context or {}
    )


def wrap_exception(
    exception: Exception,
    code: str,
    context: Optional[Dict[str, Any]] = None,
    extra_suggestions: Optional[List[str]] = None,
) -> FernError:
    """Wrap an exception in a FernError.

    Args:
        exception: The original exception
        code: The error code to use
        context: Additional context about where the error occurred
        extra_suggestions: Additional suggestions to prepend

    Returns:
        A FernError wrapping the exception
    """
    suggestions = extra_suggestions.copy() if extra_suggestions else []

    # Add suggestions based on exception type
    if isinstance(exception, PermissionError):
        suggestions.append("Check file permissions")
    elif isinstance(exception, FileNotFoundError):
        suggestions.append("Verify the file path is correct")
    elif isinstance(exception, ValueError):
        suggestions.append("Check the value being used is valid")

    error = create_error(
        code=code,
        technical_details=str(exception),
        original_exception=exception,
        context=context or {}
    )

    if suggestions:
        error.suggestions = suggestions + error.suggestions

    return error


def fern_assert(condition: bool, code: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Assert a condition and raise a FernError if false.

    Args:
        condition: The condition to check
        code: Error code to use if assertion fails
        context: Context about the assertion

    Raises:
        FernError: If condition is False
    """
    if not condition:
        raise create_error(code, context=context)


# =============================================================================
# ERROR HANDLING
# =============================================================================

def handle_errors(func):
    """Decorator to wrap functions with Fern error handling.

    Catches exceptions and converts them to FernError with appropriate codes.
    """
    import functools
    import traceback

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FernError:
            # Re-raise FernErrors as-is
            raise
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            raise create_error("FERN-002")
        except PermissionError as e:
            raise wrap_exception(e, "FERN-003", {"operation": func.__name__})
        except FileNotFoundError as e:
            raise wrap_exception(e, "FERN-004", {"path": str(e.filename)})
        except ValueError as e:
            raise wrap_exception(e, "FERN-500", {"value": str(e)})
        except Exception as e:
            # Wrap unknown exceptions
            if os.getenv("FERN_DEBUG"):
                traceback.print_exc()
            raise wrap_exception(e, "FERN-000", {"function": func.__name__})

    return wrapper


# =============================================================================
# ERROR DISPLAY
# =============================================================================

def display_error(error: FernError, console=None) -> None:
    """Display a FernError to the user.

    Args:
        error: The error to display
        console: Rich console instance (creates one if not provided)
    """
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.box import ROUNDED

    if console is None:
        console = Console()

    # Color based on severity
    severity_colors = {
        ErrorSeverity.INFO: "blue",
        ErrorSeverity.WARNING: "yellow",
        ErrorSeverity.ERROR: "red",
        ErrorSeverity.FATAL: "red",
    }

    color = severity_colors.get(error.severity, "red")

    # Build content
    content = Text()
    content.append(f"🌿 Error {error.code}\n", style=f"bold {color}")
    content.append(f"\n{error.message}\n", style=color)

    if error.suggestions:
        content.append("\nSuggestions:\n", style="bold")
        for suggestion in error.suggestions:
            content.append(f"  • {suggestion}\n", style="dim")

    if error.technical_details and os.getenv("FERN_DEBUG"):
        content.append(f"\nTechnical Details: {error.technical_details}", style="dim")

    panel = Panel(
        content,
        title=f" {error.category.value} Error ",
        border_style=color,
        box=ROUNDED
    )

    console.print(panel)


def display_fatal_error(error: FernError) -> None:
    """Display a fatal error and exit.

    Args:
        error: The fatal error
    """
    from rich.console import Console

    console = Console()
    display_error(error, console)

    # Log to file
    log_error(error)

    # Exit with error code
    # Extract numeric part of error code for exit code
    try:
        exit_code = int(error.code.split("-")[1])
    except (IndexError, ValueError):
        exit_code = 1

    sys.exit(min(exit_code, 125))  # Max exit code is 125


def log_error(error: FernError) -> None:
    """Log an error to the log file.

    Args:
        error: The error to log
    """
    import logging
    from datetime import datetime

    log_path = os.path.expanduser("~/.fern/fern.log")

    # Create logger
    logger = logging.getLogger("fern")
    logger.setLevel(logging.ERROR)

    # Add file handler if not already present
    if not logger.handlers:
        handler = logging.FileHandler(log_path)
        handler.setLevel(logging.ERROR)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Log the error
    log_message = f"{error.code}: {error.message}"
    if error.original_exception:
        log_message += f" (Exception: {error.original_exception})"

    logger.error(log_message)
