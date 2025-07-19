"""
Logging configuration and setup for the Generic Hexagonal Architecture Tagging System.

This module provides centralized logging configuration using loguru,
with support for console and file logging, structured output, and performance monitoring.
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger

from .settings import LoggingConfig, get_settings


class LoggingManager:
    """
    Manager for configuring and controlling logging throughout the system.

    Provides centralized logging setup with support for multiple outputs,
    structured logging, and performance monitoring.
    """

    def __init__(self, config: Optional[LoggingConfig] = None) -> None:
        self.config = config or get_settings().logging
        self._configured = False
        self._handlers: Dict[str, int] = {}

    def setup_logging(self) -> None:
        """Set up logging configuration based on settings."""
        if self._configured:
            return

        # Remove default handler
        logger.remove()

        # Add console handler if enabled
        if self.config.enable_console:
            handler_id = logger.add(
                sys.stderr,
                level=self.config.level.value,
                format=self.config.format,
                colorize=True,
                backtrace=True,
                diagnose=True,
            )
            self._handlers["console"] = handler_id

        # Add file handler if enabled
        if self.config.enable_file and self.config.file_path:
            log_path = self._get_log_file_path()
            if log_path:
                handler_id = logger.add(
                    str(log_path),
                    level=self.config.level.value,
                    format=self.config.format,
                    rotation=self.config.max_file_size,
                    retention=self.config.backup_count,
                    compression="gz",
                    backtrace=True,
                    diagnose=True,
                )
                self._handlers["file"] = handler_id

        # Add structured JSON handler for analysis logs
        analysis_log_path = self._get_analysis_log_path()
        if analysis_log_path:
            handler_id = logger.add(
                str(analysis_log_path),
                level="INFO",
                format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {extra}",
                filter=lambda record: "analysis" in record["extra"],
                rotation="1 day",
                retention="30 days",
                serialize=True,  # JSON format
            )
            self._handlers["analysis"] = handler_id

        self._configured = True
        logger.info(
            "Logging system initialized",
            console_enabled=self.config.enable_console,
            file_enabled=self.config.enable_file,
            level=self.config.level.value,
        )

    def get_logger(self, name: str) -> Any:
        """Get a logger instance with the specified name."""
        if not self._configured:
            self.setup_logging()

        return logger.bind(component=name)

    def log_analysis_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Log a structured analysis event."""
        logger.bind(analysis=True, event_type=event_type).info("Analysis event", **data)

    def log_performance(self, operation: str, duration: float, **kwargs) -> None:
        """Log performance metrics."""
        logger.bind(performance=True).info(
            f"Performance: {operation}",
            operation=operation,
            duration_ms=round(duration * 1000, 2),
            **kwargs,
        )

    def log_error_with_context(self, error: Exception, context: Dict[str, Any]) -> None:
        """Log an error with additional context."""
        logger.bind(error_context=context).error(
            f"Error occurred: {type(error).__name__}: {error}",
            error_type=type(error).__name__,
            error_message=str(error),
            **context,
        )

    def shutdown(self) -> None:
        """Shutdown logging and clean up handlers."""
        if self._configured:
            for handler_name, handler_id in self._handlers.items():
                try:
                    logger.remove(handler_id)
                except ValueError:
                    # Handler already removed
                    pass

            self._handlers.clear()
            self._configured = False
            logger.info("Logging system shutdown")

    def _get_log_file_path(self) -> Optional[Path]:
        """Get the main log file path."""
        if not self.config.file_path:
            return None

        log_path = Path(self.config.file_path)
        if not log_path.is_absolute():
            log_path = Path.cwd() / log_path

        # Ensure parent directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)
        return log_path

    def _get_analysis_log_path(self) -> Optional[Path]:
        """Get the analysis log file path."""
        if not self.config.enable_file:
            return None

        # Create analysis log in same directory as main log
        main_log_path = self._get_log_file_path()
        if not main_log_path:
            return None

        analysis_log_path = main_log_path.parent / "analysis.log"
        return analysis_log_path


# Global logging manager instance
_logging_manager: Optional[LoggingManager] = None


def get_logging_manager() -> LoggingManager:
    """Get the global logging manager instance."""
    global _logging_manager
    if _logging_manager is None:
        _logging_manager = LoggingManager()
        _logging_manager.setup_logging()
    return _logging_manager


def get_logger(name: str) -> Any:
    """Get a logger instance for the specified component."""
    return get_logging_manager().get_logger(name)


def log_analysis_event(event_type: str, **data) -> None:
    """Log a structured analysis event."""
    get_logging_manager().log_analysis_event(event_type, data)


def log_performance(operation: str, duration: float, **kwargs) -> None:
    """Log performance metrics."""
    get_logging_manager().log_performance(operation, duration, **kwargs)


def log_error_with_context(error: Exception, **context) -> None:
    """Log an error with additional context."""
    get_logging_manager().log_error_with_context(error, context)


def setup_logging() -> None:
    """Initialize the logging system."""
    get_logging_manager().setup_logging()


def shutdown_logging() -> None:
    """Shutdown the logging system."""
    global _logging_manager
    if _logging_manager:
        _logging_manager.shutdown()
        _logging_manager = None
