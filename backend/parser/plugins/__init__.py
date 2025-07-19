"""
Parser plugin system for Python Debug Tool.

This module implements a plugin architecture for parsers, allowing different
parsing tools to be registered, configured, and selected by users.
"""

import abc
import logging
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type, TypeVar, Union

from ..errors import (
    ErrorCollector,
    ParserError,
    ParserErrorCode,
    PluginException,
    Result,
    safe_parse_file,
)
from ..serialization import serialize, serialize_to_dict

logger = logging.getLogger(__name__)

# Global registry of parser plugins
_PARSER_PLUGINS = {}


class ParserPlugin(abc.ABC):
    """Base class for all parser plugins."""

    def __init__(self):
        """Initialize the parser plugin."""
        self.error_collector = ErrorCollector()

    @abc.abstractmethod
    def get_name(self) -> str:
        """Get the name of the plugin."""
        pass

    @abc.abstractmethod
    def get_description(self) -> str:
        """Get the description of the plugin."""
        pass

    @abc.abstractmethod
    def parse_module(self, file_path: str, **kwargs) -> Result:
        """Parse a Python module."""
        pass

    @abc.abstractmethod
    def parse_class(self, node: Any, **kwargs) -> Result:
        """Parse a Python class."""
        pass

    @abc.abstractmethod
    def parse_function(self, node: Any, **kwargs) -> Result:
        """Parse a Python function."""
        pass

    @abc.abstractmethod
    def parse_variable(self, node: Any, **kwargs) -> Result:
        """Parse a Python variable."""
        pass

    @abc.abstractmethod
    def get_ui_schema(self) -> Dict[str, Any]:
        """Get the UI schema for plugin configuration."""
        pass

    def safe_parse(self, parse_func, *args, **kwargs) -> Result:
        """Safely execute a parsing function and handle exceptions."""
        try:
            result = parse_func(*args, **kwargs)
            return Result.success(result)
        except Exception as e:
            # Record the error in the collector
            self.error_collector.add_exception(e, **kwargs)
            return Result.from_exception(e, **kwargs)

    def get_errors(self) -> List[ParserError]:
        """Get all errors collected during parsing."""
        return self.error_collector.errors

    def has_errors(self) -> bool:
        """Check if there were any errors during parsing."""
        return self.error_collector.has_errors()

    def clear_errors(self) -> None:
        """Clear all collected errors."""
        self.error_collector.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the plugin to a dictionary for serialization."""
        return {
            "name": self.get_name(),
            "description": self.get_description(),
            "errors": self.error_collector.to_dict() if self.has_errors() else None,
        }


def register_parser_plugin(plugin_class: Type[ParserPlugin]) -> None:
    """Register a parser plugin."""
    try:
        _PARSER_PLUGINS[plugin_class.__name__] = plugin_class
    except Exception as e:
        from ..errors import ParserErrorCode, PluginException

        raise PluginException(
            message=f"Failed to register plugin {plugin_class.__name__}: {str(e)}",
            plugin_name=plugin_class.__name__,
            code=ParserErrorCode.PLUGIN_LOAD_ERROR,
        ) from e


def get_plugin(name: str, options: Optional[Dict[str, Any]] = None) -> ParserPlugin:
    """
    Get a parser plugin instance.

    Args:
        name: Name of the plugin
        options: Configuration options for the plugin

    Returns:
        An instance of the requested parser plugin

    Raises:
        PluginException: If the plugin is not found or cannot be initialized
    """
    try:
        if name not in _PARSER_PLUGINS:
            raise PluginException(
                message=f"Parser plugin not found: {name}",
                plugin_name=name,
                code=ParserErrorCode.PLUGIN_NOT_FOUND,
            )

        plugin_class = _PARSER_PLUGINS[name]
        plugin_instance = plugin_class()

        # Apply options if provided
        if options and hasattr(plugin_instance, "configure"):
            plugin_instance.configure(options)

        return plugin_instance
    except Exception as e:
        if isinstance(e, PluginException):
            raise
        raise PluginException(
            message=f"Failed to initialize plugin {name}: {str(e)}",
            plugin_name=name,
            code=ParserErrorCode.PLUGIN_LOAD_ERROR,
        ) from e


def list_plugins() -> Dict[str, Dict[str, Any]]:
    """
    List all registered parser plugins.

    Returns:
        Dictionary mapping plugin names to metadata
    """
    plugins = {}
    for name, plugin_class in _PARSER_PLUGINS.items():
        try:
            # Create a temporary instance to get metadata
            instance = plugin_class()
            plugins[name] = {
                "name": instance.get_name(),
                "description": instance.get_description(),
                "ui_schema": instance.get_ui_schema(),
            }
        except Exception as e:
            logger.warning(f"Error getting metadata for plugin {name}: {e}")
            plugins[name] = {
                "name": name,
                "description": "Error loading plugin metadata",
                "error": str(e),
            }
    return plugins


def get_available_plugins() -> Dict[str, Dict[str, Any]]:
    """
    Get all available parser plugins (with dependencies installed).

    Returns:
        Dictionary mapping plugin names to metadata
    """
    plugins = {}
    for name, plugin_class in _PARSER_PLUGINS.items():
        try:
            # Try to create an instance - this will fail if dependencies are missing
            instance = plugin_class()
            plugins[name] = {
                "name": instance.get_name(),
                "description": instance.get_description(),
                "ui_schema": instance.get_ui_schema(),
                "available": True,
            }
        except Exception as e:
            logger.info(f"Plugin {name} is not available: {e}")
            # Include the plugin but mark it as unavailable
            plugins[name] = {
                "name": name,
                "description": f"Plugin not available: {str(e)}",
                "available": False,
                "error": str(e),
            }
    return plugins
