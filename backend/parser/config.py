"""
Parser configuration system for the Python Debug Tool.

This module defines the configuration options and presets for the AST parser engine,
allowing users to select and combine different parsing tools for various use cases.

# AI-Intent: Application
# Intent: This module configures how the parsing system operates
# Confidence: High
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class ParserType(Enum):
    """Available parser types for different code elements."""

    BUILT_IN_AST = "built_in_ast"  # Python's built-in AST module
    ASTROID = "astroid"  # For enhanced type inference and OOP analysis
    INSPECT4PY = "inspect4py"  # For module structure and comprehensive analysis
    PYAN = "pyan"  # For call graphs and control flow
    CUSTOM = "custom"  # For custom AST visitors


class AnalysisLevel(Enum):
    """Analysis depth levels."""

    BASIC = "basic"  # Basic structure, minimal analysis
    STANDARD = "standard"  # Standard detailed analysis (default)
    DEEP = "deep"  # Deep analysis with all available tools
    PERFORMANCE = "performance"  # Optimized for performance with large codebases


@dataclass
class ParserConfig:
    """Configuration for the AST parser engine."""

    # Basic configuration
    max_file_size: int = 1024 * 1024  # Default 1MB max file size
    skip_external_libs: bool = True  # Skip external libraries by default
    cache_results: bool = True  # Cache parsing results
    parallel_processing: bool = False  # Process files in parallel

    # Module parsing configuration
    module_parser: ParserType = ParserType.BUILT_IN_AST
    extract_imports: bool = True
    extract_module_docstring: bool = True
    analyze_import_graph: bool = False  # More expensive operation

    # Class parsing configuration
    class_parser: ParserType = ParserType.BUILT_IN_AST
    extract_class_methods: bool = True
    extract_class_attributes: bool = True
    extract_inheritance_tree: bool = False  # More expensive operation

    # Function parsing configuration
    function_parser: ParserType = ParserType.BUILT_IN_AST
    extract_function_calls: bool = False  # More expensive, requires astroid
    extract_return_types: bool = False  # More expensive, requires type analysis
    extract_decorators: bool = True

    # Variable parsing configuration
    variable_parser: ParserType = ParserType.BUILT_IN_AST
    infer_variable_types: bool = False  # More expensive, requires astroid
    track_variable_usage: bool = False  # Track where variables are used

    # Advanced analysis options
    detect_design_patterns: bool = False  # Architectural pattern detection
    domain_classification: bool = False  # Use AI to classify code domain

    # Tools to enable
    enabled_tools: Set[str] = field(default_factory=set)

    # Additional tool-specific configuration
    tool_options: Dict[str, Dict[str, Any]] = field(default_factory=dict)


def get_parser_config(preset: str) -> ParserConfig:
    """
    Get a preconfigured parser configuration.

    Available presets:
    - "minimal": Fastest parsing with basic structure only
    - "standard": Balanced parsing with reasonable detail
    - "comprehensive": Detailed parsing with all available analysis
    - "performance": Optimized for large codebases

    Args:
        preset: Name of the configuration preset

    Returns:
        Configured ParserConfig instance

    Raises:
        ValueError: If the preset is not recognized
    """
    if preset == "minimal":
        return ParserConfig(
            parallel_processing=False,
            extract_module_docstring=False,
            extract_class_methods=False,
            extract_class_attributes=False,
            extract_decorators=False,
            tool_options={
                "parallel": {
                    "max_memory_mb": 256,
                    "strategy": "thread",
                    "max_workers": 2
                }
            }
        )
    elif preset == "standard":
        return ParserConfig(
            parallel_processing=True,
            tool_options={
                "parallel": {
                    "max_memory_mb": 1024,
                    "strategy": "adaptive", 
                    "max_workers": 0,  # Auto-detect
                    "retry_failed": True,
                    "progress_tracking": True
                }
            }
        )
    elif preset == "comprehensive":
        return ParserConfig(
            parallel_processing=True,
            analyze_import_graph=True,
            extract_inheritance_tree=True,
            extract_function_calls=True,
            extract_return_types=True,
            infer_variable_types=True,
            track_variable_usage=True,
            detect_design_patterns=True,
            domain_classification=True,
            enabled_tools={"astroid", "inspect4py"},
            tool_options={
                "parallel": {
                    "max_memory_mb": 2048,
                    "strategy": "hybrid",
                    "max_workers": 0,  # Auto-detect
                    "retry_failed": True,
                    "progress_tracking": True,
                    "memory_monitoring": True,
                    "dependency_resolution": True
                }
            }
        )
    elif preset == "performance":
        return ParserConfig(
            parallel_processing=True,
            max_file_size=2 * 1024 * 1024,  # 2MB
            skip_external_libs=True,
            cache_results=True,
            # Disable expensive operations
            analyze_import_graph=False,
            extract_inheritance_tree=False,
            extract_function_calls=False,
            extract_return_types=False,
            infer_variable_types=False,
            track_variable_usage=False,
            detect_design_patterns=False,
            domain_classification=False,
            tool_options={
                "parallel": {
                    "max_memory_mb": 4096,
                    "strategy": "thread",  # Faster for I/O bound
                    "max_workers": 0,  # Use all available cores
                    "retry_failed": False,  # Skip failed files for speed
                    "progress_tracking": False,  # Reduce overhead
                    "memory_monitoring": True,
                    "batch_size": 50  # Process in larger batches
                }
            }
        )
    else:
        raise ValueError(f"Unknown configuration preset: {preset}")


def create_custom_config(**kwargs) -> ParserConfig:
    """
    Create a custom parser configuration by overriding default values.

    Args:
        **kwargs: Configuration options to override

    Returns:
        A customized ParserConfig object
    """
    config = get_parser_config("standard")  # Start with standard config

    # Update with provided values
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            raise ValueError(f"Unknown configuration option: {key}")

    return config
