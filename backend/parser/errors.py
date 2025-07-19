"""
Error handling utilities for the parser system.

This module provides a comprehensive error handling system for the parser,
including custom exception classes and error collectors.

# AI-Intent: Core-Domain
# Intent: These error classes represent the core domain entities for error handling
# They encapsulate the essential error types and behaviors
# Confidence: High
"""

import os
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union


class ErrorSeverity(Enum):
    """Severity levels for parser errors."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ParserErrorCode(Enum):
    """Error codes for parser errors."""

    # General errors
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    TIMEOUT = "TIMEOUT"

    # Syntax errors
    SYNTAX_ERROR = "SYNTAX_ERROR"
    INDENTATION_ERROR = "INDENTATION_ERROR"

    # AST parsing errors
    AST_PARSE_ERROR = "AST_PARSE_ERROR"
    MODULE_PARSE_ERROR = "MODULE_PARSE_ERROR"
    CLASS_PARSE_ERROR = "CLASS_PARSE_ERROR"
    FUNCTION_PARSE_ERROR = "FUNCTION_PARSE_ERROR"
    VARIABLE_PARSE_ERROR = "VARIABLE_PARSE_ERROR"

    # Plugin errors
    PLUGIN_LOAD_ERROR = "PLUGIN_LOAD_ERROR"
    PLUGIN_EXECUTION_ERROR = "PLUGIN_EXECUTION_ERROR"
    PLUGIN_NOT_FOUND = "PLUGIN_NOT_FOUND"

    # Exporter errors
    EXPORT_ERROR = "EXPORT_ERROR"
    NEO4J_CONNECTION_ERROR = "NEO4J_CONNECTION_ERROR"
    NEO4J_QUERY_ERROR = "NEO4J_QUERY_ERROR"

    # Serialization errors
    SERIALIZATION_ERROR = "SERIALIZATION_ERROR"
    CIRCULAR_REFERENCE_ERROR = "CIRCULAR_REFERENCE_ERROR"


@dataclass
class ParserError:
    """Represents an error that occurred during parsing."""

    code: ParserErrorCode
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    column: Optional[int] = None
    severity: ErrorSeverity = ErrorSeverity.ERROR
    traceback_str: Optional[str] = None
    exception: Optional[Exception] = None
    context: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize additional fields after main initialization."""
        if self.exception and not self.traceback_str:
            self.traceback_str = "".join(
                traceback.format_exception(
                    type(self.exception), self.exception, self.exception.__traceback__
                )
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary for serialization."""
        return {
            "code": self.code.value,
            "message": self.message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column": self.column,
            "severity": self.severity.value,
            "traceback": self.traceback_str,
            "context": self.context,
        }


class ParserException(Exception):
    """Base exception class for parser errors."""

    def __init__(
        self,
        message: str,
        code: ParserErrorCode = ParserErrorCode.UNKNOWN_ERROR,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        column: Optional[int] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.code = code
        self.file_path = file_path
        self.line_number = line_number
        self.column = column
        self.severity = severity
        self.context = context or {}

    def to_error(self) -> ParserError:
        """Convert this exception to a ParserError object."""
        return ParserError(
            code=self.code,
            message=str(self),
            file_path=self.file_path,
            line_number=self.line_number,
            column=self.column,
            severity=self.severity,
            exception=self,
            context=self.context,
        )


class SyntaxParserException(ParserException):
    """Exception for syntax errors in Python code."""

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        column: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code=ParserErrorCode.SYNTAX_ERROR,
            file_path=file_path,
            line_number=line_number,
            column=column,
            severity=ErrorSeverity.ERROR,
            context=context,
        )


class ASTParseException(ParserException):
    """Exception for AST parsing errors."""

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        column: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code=ParserErrorCode.AST_PARSE_ERROR,
            file_path=file_path,
            line_number=line_number,
            column=column,
            severity=ErrorSeverity.ERROR,
            context=context,
        )


class PluginException(ParserException):
    """Exception for plugin-related errors."""

    def __init__(
        self,
        message: str,
        plugin_name: str,
        code: ParserErrorCode = ParserErrorCode.PLUGIN_EXECUTION_ERROR,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        column: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        context = context or {}
        context["plugin_name"] = plugin_name
        super().__init__(
            message=message,
            code=code,
            file_path=file_path,
            line_number=line_number,
            column=column,
            severity=ErrorSeverity.ERROR,
            context=context,
        )


class ExporterException(ParserException):
    """Exception for exporter-related errors."""

    def __init__(
        self,
        message: str,
        exporter_name: str,
        code: ParserErrorCode = ParserErrorCode.EXPORT_ERROR,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        column: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        context = context or {}
        context["exporter_name"] = exporter_name
        super().__init__(
            message=message,
            code=code,
            file_path=file_path,
            line_number=line_number,
            column=column,
            severity=ErrorSeverity.ERROR,
            context=context,
        )


class SerializationException(ParserException):
    """Exception for serialization-related errors."""

    def __init__(
        self,
        message: str,
        code: ParserErrorCode = ParserErrorCode.SERIALIZATION_ERROR,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        column: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code=code,
            file_path=file_path,
            line_number=line_number,
            column=column,
            severity=ErrorSeverity.ERROR,
            context=context,
        )


T = TypeVar("T")


@dataclass
class Result(Generic[T]):
    """
    A result type that can contain either a value or an error.

    This is used to handle operations that might fail without using exceptions.
    """

    value: Optional[T] = None
    error: Optional[ParserError] = None

    @property
    def is_success(self) -> bool:
        """Check if the result is successful."""
        return self.error is None

    @property
    def is_error(self) -> bool:
        """Check if the result is an error."""
        return self.error is not None

    @classmethod
    def success(cls, value: T) -> "Result[T]":
        """Create a successful result with the given value."""
        return cls(value=value)

    @classmethod
    def failure(cls, error: ParserError) -> "Result[T]":
        """Create a failed result with the given error."""
        return cls(error=error)

    @classmethod
    def from_exception(cls, exception: Exception, **kwargs) -> "Result[T]":
        """Create a failed result from an exception."""
        if isinstance(exception, ParserException):
            error = exception.to_error()
        else:
            error = ParserError(
                code=ParserErrorCode.UNKNOWN_ERROR,
                message=str(exception),
                exception=exception,
                **kwargs,
            )
        return cls.failure(error)


@dataclass
class ErrorCollector:
    """Collects and aggregates errors during parsing."""

    errors: List[ParserError] = field(default_factory=list)

    def add_error(self, error: ParserError) -> None:
        """Add an error to the collector."""
        self.errors.append(error)

    def add_exception(self, exception: Exception, **kwargs) -> None:
        """Add an exception to the collector."""
        if isinstance(exception, ParserException):
            self.add_error(exception.to_error())
        else:
            self.add_error(
                ParserError(
                    code=ParserErrorCode.UNKNOWN_ERROR,
                    message=str(exception),
                    exception=exception,
                    **kwargs,
                )
            )

    def has_errors(self) -> bool:
        """Check if the collector has any errors."""
        return len(self.errors) > 0

    def has_critical_errors(self) -> bool:
        """Check if the collector has any critical errors."""
        return any(e.severity == ErrorSeverity.CRITICAL for e in self.errors)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the error collector to a dictionary for serialization."""
        return {
            "has_errors": self.has_errors(),
            "error_count": len(self.errors),
            "has_critical_errors": self.has_critical_errors(),
            "errors": [error.to_dict() for error in self.errors],
        }

    def clear(self) -> None:
        """Clear all errors from the collector."""
        self.errors.clear()


def safe_parse_file(parse_func, file_path: str, **kwargs) -> Result:
    """
    Safely parse a file using the given parse function.

    Args:
        parse_func: The function to use for parsing.
        file_path: The path to the file to parse.
        **kwargs: Additional arguments to pass to the parse function.

    Returns:
        A Result object containing either the parsed result or an error.
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return Result.failure(
                ParserError(
                    code=ParserErrorCode.FILE_NOT_FOUND,
                    message=f"File not found: {file_path}",
                    file_path=file_path,
                )
            )

        # Check if file is readable
        if not os.access(file_path, os.R_OK):
            return Result.failure(
                ParserError(
                    code=ParserErrorCode.PERMISSION_DENIED,
                    message=f"Permission denied: {file_path}",
                    file_path=file_path,
                )
            )

        # Parse the file
        result = parse_func(file_path, **kwargs)
        return Result.success(result)
    except SyntaxError as e:
        return Result.failure(
            ParserError(
                code=ParserErrorCode.SYNTAX_ERROR,
                message=f"Syntax error: {str(e)}",
                file_path=file_path,
                line_number=e.lineno,
                column=e.offset,
            )
        )
    except Exception as e:
        return Result.from_exception(e, file_path=file_path)
