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
    extract_inheritance: bool = True
    extract_class_docstring: bool = True
    infer_class_types: bool = False  # More expensive, requires astroid

    # Function parsing configuration
    function_parser: ParserType = ParserType.BUILT_IN_AST
    extract_function_docstring: bool = True
    analyze_parameters: bool = True
    infer_return_types: bool = False  # More expensive, requires astroid
    compute_complexity: bool = False  # Calculate cyclomatic complexity

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


# Built-in configuration presets
PARSER_PRESETS = {
    "default": ParserConfig(
        # Default configuration with reasonable defaults
    ),
    "basic": ParserConfig(
        module_parser=ParserType.BUILT_IN_AST,
        class_parser=ParserType.BUILT_IN_AST,
        function_parser=ParserType.BUILT_IN_AST,
        variable_parser=ParserType.BUILT_IN_AST,
        extract_imports=True,
        extract_class_docstring=True,
        extract_function_docstring=True,
        extract_module_docstring=True,
        infer_class_types=False,
        infer_return_types=False,
        infer_variable_types=False,
        compute_complexity=False,
        enabled_tools={"ast"},
    ),
    "standard": ParserConfig(
        module_parser=ParserType.BUILT_IN_AST,
        class_parser=ParserType.ASTROID,
        function_parser=ParserType.BUILT_IN_AST,
        variable_parser=ParserType.BUILT_IN_AST,
        extract_imports=True,
        extract_class_docstring=True,
        extract_function_docstring=True,
        extract_module_docstring=True,
        infer_class_types=True,
        infer_return_types=True,
        infer_variable_types=False,
        compute_complexity=True,
        enabled_tools={"ast", "astroid"},
    ),
    "deep": ParserConfig(
        module_parser=ParserType.INSPECT4PY,
        class_parser=ParserType.ASTROID,
        function_parser=ParserType.ASTROID,
        variable_parser=ParserType.ASTROID,
        extract_imports=True,
        extract_class_docstring=True,
        extract_function_docstring=True,
        extract_module_docstring=True,
        analyze_import_graph=True,
        infer_class_types=True,
        infer_return_types=True,
        infer_variable_types=True,
        compute_complexity=True,
        detect_design_patterns=True,
        domain_classification=True,
        enabled_tools={"ast", "astroid", "inspect4py", "pyan"},
    ),
    "performance": ParserConfig(
        module_parser=ParserType.BUILT_IN_AST,
        class_parser=ParserType.BUILT_IN_AST,
        function_parser=ParserType.BUILT_IN_AST,
        variable_parser=ParserType.BUILT_IN_AST,
        extract_imports=True,
        extract_class_docstring=False,
        extract_function_docstring=False,
        extract_module_docstring=False,
        infer_class_types=False,
        infer_return_types=False,
        infer_variable_types=False,
        compute_complexity=False,
        cache_results=True,
        parallel_processing=True,
        enabled_tools={"ast"},
    ),
    "web_application": ParserConfig(
        module_parser=ParserType.BUILT_IN_AST,
        class_parser=ParserType.ASTROID,
        function_parser=ParserType.BUILT_IN_AST,
        variable_parser=ParserType.BUILT_IN_AST,
        extract_imports=True,
        extract_class_docstring=True,
        extract_function_docstring=True,
        extract_module_docstring=True,
        infer_class_types=True,
        infer_return_types=True,
        compute_complexity=True,
        domain_classification=True,
        tool_options={
            "custom": {
                "detect_web_frameworks": True,
                "extract_api_endpoints": True,
                "security_checks": True,
            }
        },
        enabled_tools={"ast", "astroid", "bandit"},
    ),
    "data_science": ParserConfig(
        module_parser=ParserType.BUILT_IN_AST,
        class_parser=ParserType.ASTROID,
        function_parser=ParserType.BUILT_IN_AST,
        variable_parser=ParserType.ASTROID,
        extract_imports=True,
        extract_class_docstring=True,
        extract_function_docstring=True,
        extract_module_docstring=True,
        infer_class_types=True,
        infer_return_types=True,
        infer_variable_types=True,
        tool_options={
            "custom": {
                "detect_data_transforms": True,
                "identify_numerical_operations": True,
                "track_dataframe_operations": True,
            }
        },
        enabled_tools={"ast", "astroid"},
    ),
    "hexagonal_architecture": ParserConfig(
        module_parser=ParserType.INSPECT4PY,
        class_parser=ParserType.ASTROID,
        function_parser=ParserType.ASTROID,
        variable_parser=ParserType.ASTROID,
        extract_imports=True,
        extract_class_docstring=True,
        extract_function_docstring=True,
        extract_module_docstring=True,
        analyze_import_graph=True,
        infer_class_types=True,
        infer_return_types=True,
        infer_variable_types=True,
        detect_design_patterns=True,
        domain_classification=True,
        tool_options={
            "custom": {
                "detect_ports_adapters": True,
                "identify_domain_logic": True,
                "check_architecture_violations": True,
            }
        },
        enabled_tools={"ast", "astroid", "inspect4py"},
    ),
}


def get_parser_config(preset: str = "standard") -> ParserConfig:
    """
    Get a parser configuration based on a preset name.

    Args:
        preset: Name of the configuration preset to use

    Returns:
        A ParserConfig object with the specified preset

    Raises:
        ValueError: If the preset name is not recognized
    """
    if preset not in PARSER_PRESETS:
        raise ValueError(
            f"Unknown parser preset: {preset}. "
            f"Available presets: {', '.join(PARSER_PRESETS.keys())}"
        )

    return PARSER_PRESETS[preset]


def create_custom_config(**kwargs) -> ParserConfig:
    """
    Create a custom parser configuration by overriding default values.

    Args:
        **kwargs: Configuration options to override

    Returns:
        A customized ParserConfig object
    """
    config = PARSER_PRESETS["standard"]  # Start with standard config

    # Update with provided values
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            raise ValueError(f"Unknown configuration option: {key}")

    return config
