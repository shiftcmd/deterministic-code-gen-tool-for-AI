"""
Utility functions for checking parser plugin availability.

# AI-Intent: Application
# Intent: This module provides application services for checking plugin availability
# It connects the core domain (plugins) with the outside world
# Confidence: High
"""

import logging
from typing import Dict, List, Optional, Set

from . import _PARSER_PLUGINS

logger = logging.getLogger(__name__)


def check_plugin_availability(plugin_name: str) -> bool:
    """
    Check if a plugin is available (registered and initializable).

    Args:
        plugin_name: Name of the plugin to check

    Returns:
        True if the plugin is available, False otherwise
    """
    if plugin_name not in _PARSER_PLUGINS:
        return False

    try:
        plugin_class = _PARSER_PLUGINS[plugin_name]
        plugin_class()  # Try to instantiate it
        return True
    except Exception as e:
        logger.info(f"Plugin {plugin_name} is not available: {e}")
        return False


def get_available_plugin_names() -> Set[str]:
    """
    Get the names of all available plugins.

    Returns:
        A set of available plugin names
    """
    return {name for name in _PARSER_PLUGINS if check_plugin_availability(name)}


def check_required_plugins(required_plugins: List[str]) -> Dict[str, bool]:
    """
    Check if a list of required plugins are available.

    Args:
        required_plugins: List of plugin names to check

    Returns:
        Dictionary mapping plugin names to availability status
    """
    results = {}
    for plugin_name in required_plugins:
        results[plugin_name] = check_plugin_availability(plugin_name)
    return results
