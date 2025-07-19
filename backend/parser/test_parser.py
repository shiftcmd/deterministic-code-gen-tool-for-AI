"""
Test script for the AST Parser Engine.

This script provides a simple way to test the parser engine by parsing a Python file
and printing the extracted information.
"""

import json
import logging
import os
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)

# Add the parent directory to sys.path to allow importing the parser package
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.parser.codebase_parser import CodebaseParser
from backend.parser.config import (
    AnalysisLevel,
    ParserConfig,
    ParserType,
    get_preset_config,
)
from backend.parser.module_parser import ModuleParser


def print_module_info(parsed_module):
    """Print information about a parsed module."""
    print(f"\n{'='*80}")
    print(f"Module: {parsed_module.name}")
    print(f"Path: {parsed_module.path}")
    print(f"Line count: {parsed_module.line_count}")
    print(f"Size: {parsed_module.size_bytes} bytes")
    print(f"Last modified: {parsed_module.last_modified}")

    if parsed_module.docstring:
        print(f"\nDocstring: {parsed_module.docstring[:100]}...")

    print(f"\nImports ({len(parsed_module.imports)}):")
    for imp in parsed_module.imports[:5]:  # Show first 5 imports
        if imp.fromname:
            print(
                f"  from {imp.fromname} import {imp.name}{' as ' + imp.asname if imp.asname else ''}"
            )
        else:
            print(f"  import {imp.name}{' as ' + imp.asname if imp.asname else ''}")
    if len(parsed_module.imports) > 5:
        print(f"  ... and {len(parsed_module.imports) - 5} more")

    print(f"\nClasses ({len(parsed_module.classes)}):")
    for cls in parsed_module.classes:
        print(f"  {cls.name} (bases: {', '.join(cls.bases) if cls.bases else 'None'})")
        print(f"    Methods: {len(cls.methods)}")
        print(f"    Attributes: {len(cls.attributes)}")
        print(f"    Inner classes: {len(cls.inner_classes)}")

    print(f"\nFunctions ({len(parsed_module.functions)}):")
    for func in parsed_module.functions[:5]:  # Show first 5 functions
        print(f"  {func.signature}")
    if len(parsed_module.functions) > 5:
        print(f"  ... and {len(parsed_module.functions) - 5} more")

    print(f"\nVariables ({len(parsed_module.variables)}):")
    for var in parsed_module.variables[:5]:  # Show first 5 variables
        type_info = f": {var.inferred_type}" if var.inferred_type else ""
        value_info = f" = {var.value_repr}" if var.value_repr else ""
        print(f"  {var.name}{type_info}{value_info}")
    if len(parsed_module.variables) > 5:
        print(f"  ... and {len(parsed_module.variables) - 5} more")

    if parsed_module.ast_errors:
        print("\nErrors:")
        for error in parsed_module.ast_errors:
            print(f"  {error['error_type']}: {error['message']}")


def test_module_parser(file_path, config_preset=None):
    """Test the module parser on a single file."""
    if config_preset:
        config = get_preset_config(config_preset)
    else:
        config = ParserConfig()  # Default configuration

    parser = ModuleParser(config)

    print(f"\nParsing {file_path} with preset: {config_preset or 'default'}")
    parsed_module = parser.parse(file_path)
    print_module_info(parsed_module)


def test_codebase_parser(directory_path, config_preset=None):
    """Test the codebase parser on a directory."""
    if config_preset:
        config = get_preset_config(config_preset)
    else:
        config = ParserConfig()  # Default configuration

    parser = CodebaseParser(config)

    print(
        f"\nParsing codebase at {directory_path} with preset: {config_preset or 'default'}"
    )
    parsed_modules = parser.parse(directory_path)
    print(f"Found {len(parsed_modules)} modules")

    # Print summary info for each module
    for module_path, parsed_module in parsed_modules.items():
        print(f"\n{'-'*40}")
        print(f"Module: {parsed_module.name}")
        print(f"Path: {module_path}")
        print(f"Classes: {len(parsed_module.classes)}")
        print(f"Functions: {len(parsed_module.functions)}")
        print(f"Variables: {len(parsed_module.variables)}")
        print(f"Imports: {len(parsed_module.imports)}")

    # Print detailed info for one module as an example
    if parsed_modules:
        example_module = next(iter(parsed_modules.values()))
        print("\nDetailed example of one parsed module:")
        print_module_info(example_module)


def main():
    """Main function to run the test script."""
    if len(sys.argv) < 2:
        print("Usage: python test_parser.py <file_path_or_directory> [config_preset]")
        print("Available presets:")
        for preset in [
            "basic",
            "standard",
            "deep",
            "performance",
            "web_application",
            "data_science",
            "hexagonal_architecture",
        ]:
            print(f"  - {preset}")
        return

    path = sys.argv[1]
    config_preset = sys.argv[2] if len(sys.argv) > 2 else None

    if not os.path.exists(path):
        print(f"Error: Path {path} does not exist.")
        return

    if os.path.isfile(path):
        test_module_parser(path, config_preset)
    else:
        test_codebase_parser(path, config_preset)


if __name__ == "__main__":
    main()
