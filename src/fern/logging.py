"""Fern Logging System.

Structured logging with levels, file output, and rich console display.
"""

from __future__ import annotations

import logging
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from functools import wraps
import threading


class FernLogger:
    """Fern logging manager with structured output."""

    def __init__(
        self,
        name: str = "fern",
        log_file: Optional[str] = None,
        level: int = logging.INFO,
        console: bool = True,
        rich_console: bool = True
    ):
        """Initialize the Fern logger.

        Args:
            name: Logger name (usually "fern")
            log_file: Path to log file (default: ~/.fern/fern.log)
            level: Minimum log level
            console: Whether to log to console
            rich_console: Whether to use Rich for console output
        """
        self.name = name
        self.log_file = log_file or os.path.expanduser("~/.fern/fern.log")
        self.level = level
        self.console_output = console
        self.rich_console = rich_console

        self._logger: Optional[logging.Logger] = None
        self._initialized = False
        self._lock = threading.Lock()

    def _ensure_logger(self) -> logging.Logger:
        """Ensure the logger is initialized."""
        if self._logger is not None:
            return self._logger

        with self._lock:
            if self._logger is not None:
                return self._logger

            self._logger = logging.getLogger(self.name)
            self._logger.setLevel(self.level)

            # Clear existing handlers
            self._logger.handlers.clear()

            # Create formatter
            formatter = logging.Formatter(
                "%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )

            # File handler
            if self.log_file:
                Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
                file_handler.setLevel(self.level)
                file_handler.setFormatter(formatter)
                self._logger.addHandler(file_handler)

            # Console handler
            if self.console_output:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(self.level)
                console_handler.setFormatter(formatter)
                self._logger.addHandler(console_handler)

            self._initialized = True
            return self._logger

    @property
    def logger(self) -> logging.Logger:
        """Get the underlying logger instance."""
        return self._ensure_logger()

    def set_level(self, level: int) -> None:
        """Set the log level.

        Args:
            level: Log level (logging.DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.level = level
        if self._logger:
            self._logger.setLevel(level)

    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message."""
        self.logger.debug(self._format_message(message, kwargs))

    def info(self, message: str, **kwargs) -> None:
        """Log an info message."""
        self.logger.info(self._format_message(message, kwargs))

    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message."""
        self.logger.warning(self._format_message(message, kwargs))

    def error(self, message: str, error_code: Optional[str] = None, **kwargs) -> None:
        """Log an error message.

        Args:
            message: Error message
            error_code: Optional error code (e.g., "FERN-100")
            **kwargs: Additional context
        """
        context = kwargs.copy()
        if error_code:
            context["error_code"] = error_code
        self.logger.error(self._format_message(message, context))

    def critical(self, message: str, **kwargs) -> None:
        """Log a critical message."""
        self.logger.critical(self._format_message(message, kwargs))

    def exception(self, message: str, exc: Exception, **kwargs) -> None:
        """Log an exception with traceback.

        Args:
            message: Description of what happened
            exc: The exception
            **kwargs: Additional context
        """
        self.logger.exception(
            self._format_message(message, {"exception": str(exc), **kwargs})
        )

    def log_operation(
        self,
        operation: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ) -> None:
        """Log an operation status.

        Args:
            operation: Name of the operation
            status: Status (started, completed, failed)
            details: Additional details
            error_code: Error code if failed
        """
        status_emojis = {
            "started": "🚀",
            "completed": "✅",
            "failed": "❌",
            "running": "⏳",
            "skipped": "⏭️"
        }
        emoji = status_emojis.get(status, "📝")

        message = f"{emoji} {operation}: {status}"
        if details:
            message += f" | {details}"

        if status == "failed":
            self.error(message, error_code=error_code)
        elif status in ("completed", "started"):
            self.info(message)
        else:
            self.debug(message)

    def _format_message(self, message: str, kwargs: Dict[str, Any]) -> str:
        """Format message with context.

        Args:
            message: Base message
            kwargs: Context key-value pairs

        Returns:
            Formatted message
        """
        if not kwargs:
            return message

        context_parts = []
        for key, value in kwargs.items():
            if value is not None:
                context_parts.append(f"{key}={value}")

        if context_parts:
            message = f"{message} | {' | '.join(context_parts)}"

        return message

    def log_session(
        self,
        session_id: int,
        action: str,
        duration: Optional[float] = None,
        readings: Optional[int] = None
    ) -> None:
        """Log session activity.

        Args:
            session_id: Session ID
            action: Action (started, stopped, analyzed)
            duration: Session duration in seconds
            readings: Number of readings
        """
        details = {"session_id": session_id}
        if duration:
            details["duration"] = f"{duration:.1f}s"
        if readings:
            details["readings"] = readings

        self.log_operation(
            operation=f"Session #{session_id}",
            status=action,
            details=details
        )

    def log_capture(
        self,
        action: str,
        device: Optional[str] = None,
        sample_rate: Optional[int] = None
    ) -> None:
        """Log audio capture activity.

        Args:
            action: Action (started, stopped, failed)
            device: Audio device name
            sample_rate: Sample rate in Hz
        """
        details = {}
        if device:
            details["device"] = device
        if sample_rate:
            details["sample_rate"] = f"{sample_rate}Hz"

        self.log_operation(
            operation="Audio Capture",
            status=action,
            details=details
        )

    def log_analysis(
        self,
        session_id: int,
        pitch: float,
        f1: Optional[float] = None,
        f2: Optional[float] = None,
        f3: Optional[float] = None
    ) -> None:
        """Log analysis result.

        Args:
            session_id: Session ID
            pitch: Median pitch in Hz
            f1: F1 formant (optional)
            f2: F2 formant (optional)
            f3: F3 formant (optional)
        """
        message = f"Analysis complete | pitch={pitch:.1f}Hz"
        if all(v is not None for v in (f1, f2, f3)):
            message += f" | formants={f1:.0f}/{f2:.0f}/{f3:.0f}"

        self.info(message, session_id=session_id)


# Global logger instance
_default_logger: Optional[FernLogger] = None


def get_logger(
    name: str = "fern",
    log_file: Optional[str] = None,
    level: int = logging.INFO
) -> FernLogger:
    """Get the default Fern logger or create a new one.

    Args:
        name: Logger name
        log_file: Log file path
        level: Log level

    Returns:
        FernLogger instance
    """
    global _default_logger

    if _default_logger is None:
        _default_logger = FernLogger(
            name=name,
            log_file=log_file,
            level=level
        )

    return _default_logger


def log_function(func):
    """Decorator to log function calls.

    Args:
        func: Function to decorate

    Returns:
        Wrapped function with logging
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger()
        logger.log_operation(
            operation=func.__name__,
            status="started"
        )
        try:
            result = func(*args, **kwargs)
            logger.log_operation(
                operation=func.__name__,
                status="completed"
            )
            return result
        except Exception as e:
            logger.exception(
                f"Function {func.__name__} failed",
                exc=e
            )
            logger.log_operation(
                operation=func.__name__,
                status="failed"
            )
            raise

    return wrapper


def configure_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    verbose: bool = False,
    quiet: bool = False
) -> None:
    """Configure Fern logging from command line.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Log file path
        verbose: Enable verbose (debug) logging
        quiet: Suppress most output
    """
    import logging as log_module

    level_map = {
        "DEBUG": log_module.DEBUG,
        "INFO": log_module.INFO,
        "WARNING": log_module.WARNING,
        "ERROR": log_module.ERROR,
        "CRITICAL": log_module.CRITICAL
    }

    log_level = level_map.get(level.upper(), log_module.INFO)

    if verbose:
        log_level = log_module.DEBUG

    if quiet:
        log_level = log_module.WARNING

    logger = get_logger()
    logger.set_level(log_level)

    if verbose:
        os.environ["FERN_DEBUG"] = "1"


# Create default logger for convenience
default_logger = get_logger()

# Convenience functions that use the default logger
def debug(message: str, **kwargs) -> None:
    """Log a debug message."""
    default_logger.debug(message, **kwargs)


def info(message: str, **kwargs) -> None:
    """Log an info message."""
    default_logger.info(message, **kwargs)


def warning(message: str, **kwargs) -> None:
    """Log a warning message."""
    default_logger.warning(message, **kwargs)


def error(message: str, **kwargs) -> None:
    """Log an error message."""
    default_logger.error(message, **kwargs)


def critical(message: str, **kwargs) -> None:
    """Log a critical message."""
    default_logger.critical(message, **kwargs)


def log_session(session_id: int, action: str, **kwargs) -> None:
    """Log session activity."""
    default_logger.log_session(session_id, action, **kwargs)


def log_capture(action: str, **kwargs) -> None:
    """Log audio capture activity."""
    default_logger.log_capture(action, **kwargs)


def log_analysis(session_id: int, pitch: float, **kwargs) -> None:
    """Log analysis result."""
    default_logger.log_analysis(session_id, pitch, **kwargs)
