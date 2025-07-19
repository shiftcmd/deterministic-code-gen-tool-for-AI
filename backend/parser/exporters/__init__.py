"""
Parser exporters for Python Debug Tool.

This module implements exporters to convert parsed code information
into different formats and destinations, like databases and files.
"""

import logging
from typing import Any, Dict, List, Optional, Type

logger = logging.getLogger(__name__)

# Global registry of exporters
_exporters = {}


class ParserExporter:
    """Base class for parser exporters."""

    # Class variables
    name: str = "base"
    description: str = "Base exporter"
    version: str = "0.1.0"

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """
        Initialize the exporter.

        Args:
            options: Configuration options for this exporter
        """
        self.options = options or {}

    def export(self, data: Dict[str, Any]) -> bool:
        """
        Export parsed data to the target destination.

        Args:
            data: Parsed code data to export

        Returns:
            True if export succeeded, False otherwise
        """
        raise NotImplementedError("Subclasses must implement export")

    def connect(self) -> bool:
        """
        Connect to the export target.

        Returns:
            True if connection succeeded, False otherwise
        """
        return True

    def disconnect(self) -> None:
        """Disconnect from the export target."""
        pass

    def get_schema(self) -> Dict[str, Any]:
        """
        Get the schema of the exported data.

        Returns:
            Dictionary describing the schema
        """
        return {"type": "object", "properties": {}}


def register_exporter(exporter_class: Type[ParserExporter]) -> None:
    """
    Register a parser exporter.

    Args:
        exporter_class: Exporter class to register
    """
    if not issubclass(exporter_class, ParserExporter):
        raise TypeError("Exporter must be a subclass of ParserExporter")

    _exporters[exporter_class.name] = exporter_class
    logger.debug(f"Registered parser exporter: {exporter_class.name}")


def get_exporter(name: str, options: Optional[Dict[str, Any]] = None) -> ParserExporter:
    """
    Get a parser exporter instance.

    Args:
        name: Name of the exporter
        options: Configuration options for the exporter

    Returns:
        An instance of the requested exporter

    Raises:
        ValueError: If the exporter is not found
    """
    if name not in _exporters:
        raise ValueError(f"Exporter not found: {name}")

    exporter_class = _exporters[name]
    return exporter_class(options)


def list_exporters() -> Dict[str, Dict[str, str]]:
    """
    List all registered exporters.

    Returns:
        Dictionary mapping exporter names to metadata
    """
    exporters = {}
    for name, exporter_class in _exporters.items():
        exporters[name] = {
            "name": exporter_class.name,
            "description": exporter_class.description,
            "version": exporter_class.version,
        }
    return exporters
