"""
Inspect4py parser plugin for Python Debug Tool.

This module implements a parser plugin using the inspect4py library,
providing comprehensive module analysis and package inspection.

# AI-Intent: Core-Domain
# Intent: Provides comprehensive module analysis using inspect4py
# Confidence: High
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Set, Union

from ..models import (
    ParsedClass,
    ParsedFunction,
    ParsedImport,
    ParsedModule,
    ParsedVariable,
)
from . import ParserPlugin, register_plugin

logger = logging.getLogger(__name__)


class Inspect4PyPlugin(ParserPlugin):
    """Parser plugin using the inspect4py library."""

    name = "inspect4py"
    description = (
        "Comprehensive module analyzer using inspect4py for package inspection"
    )
    version = "1.0.0"
    supported_types = {"module"}  # inspect4py is primarily a module/package analyzer
    requires_dependencies = ["inspect4py"]
    default_options = {
        "extract_dependencies": True,
        "analyze_file_structure": True,
        "include_tests": False,
        "extract_docstrings": True,
        "max_depth": 3,  # Maximum depth for package exploration
    }

    def parse_module(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Parse a Python module file using inspect4py.

        Args:
            file_path: Path to the Python file
            content: Content of the file

        Returns:
            Dictionary with parsed module information
        """
        try:
            # Dynamically import inspect4py to avoid hard dependency
            from inspect4py.inspector import Inspector

            # Determine if we're analyzing a file or directory
            is_directory = os.path.isdir(file_path)
            target_path = file_path

            # If it's a file, use the parent directory and filter for just this file
            if not is_directory:
                target_path = os.path.dirname(file_path)
                file_name = os.path.basename(file_path)

            # Create an inspector object
            inspector = Inspector(directory=target_path, verbose=False)

            # Analyze the target
            inspector.inspect()

            # Get the results
            inspection_results = inspector.get_results()

            # Process the results
            if is_directory:
                # For directories, process the entire package
                result = self._process_package_results(inspection_results, target_path)
            else:
                # For single files, extract just that file's info
                result = self._process_file_results(inspection_results, file_path)

            # Add basic imports from the AST scan (inspect4py might miss some)
            if "imports" not in result or not result["imports"]:
                import ast

                try:
                    tree = ast.parse(content, filename=file_path)
                    result["imports"] = self._extract_basic_imports(tree)
                except Exception as e:
                    logger.warning(f"Could not parse imports with AST: {e}")

            return result

        except ImportError:
            logger.error(
                "inspect4py not installed. Install with 'pip install inspect4py'"
            )
            raise
        except Exception as e:
            logger.error(f"Error parsing {file_path} with inspect4py: {e}")
            raise

    def _process_package_results(
        self, results: Dict[str, Any], package_path: str
    ) -> Dict[str, Any]:
        """
        Process inspect4py results for a package.

        Args:
            results: inspect4py results
            package_path: Path to the package

        Returns:
            Processed package information
        """
        package_info = {
            "name": os.path.basename(package_path),
            "path": package_path,
            "is_package": True,
            "modules": [],
            "dependencies": [],
            "imports": [],
            "ast_type": "package",
        }

        # Extract dependencies if available and requested
        if self.options["extract_dependencies"] and "dependencies" in results:
            for dep_type, deps in results["dependencies"].items():
                if isinstance(deps, list):
                    for dep in deps:
                        package_info["dependencies"].append(
                            {"name": dep, "type": dep_type}
                        )
                elif isinstance(deps, dict):
                    for dep_name, dep_details in deps.items():
                        package_info["dependencies"].append(
                            {"name": dep_name, "type": dep_type, "details": dep_details}
                        )

        # Process file structure if requested
        if self.options["analyze_file_structure"] and "files" in results:
            package_info["file_structure"] = results["files"]

        # Process modules
        if "modules" in results:
            for module_name, module_info in results["modules"].items():
                # Skip test files if configured to do so
                if not self.options["include_tests"] and (
                    "test" in module_name.lower() or module_name.startswith("_test")
                ):
                    continue

                # Process the module
                module_data = self._process_module_info(module_name, module_info)
                package_info["modules"].append(module_data)

                # Collect all imports across modules
                if "imports" in module_data:
                    package_info["imports"].extend(module_data["imports"])

        return package_info

    def _process_file_results(
        self, results: Dict[str, Any], file_path: str
    ) -> Dict[str, Any]:
        """
        Process inspect4py results for a single file.

        Args:
            results: inspect4py results
            file_path: Path to the file

        Returns:
            Processed file information
        """
        file_name = os.path.basename(file_path)
        module_name = file_name.replace(".py", "")

        # Basic module info
        module_info = {
            "name": module_name,
            "path": file_path,
            "is_package": False,
            "classes": [],
            "functions": [],
            "variables": [],
            "imports": [],
            "ast_type": "module",
        }

        # Try to find this specific file in the results
        if "modules" in results:
            for potential_name, potential_info in results["modules"].items():
                if potential_name == module_name or potential_name.endswith(
                    f".{module_name}"
                ):
                    # Found the module, process it
                    module_data = self._process_module_info(module_name, potential_info)

                    # Update the basic info with the processed data
                    module_info.update(module_data)
                    break

        # If no specific module info found, return the basic info
        return module_info

    def _process_module_info(
        self, module_name: str, module_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process module information from inspect4py.

        Args:
            module_name: Name of the module
            module_info: Module information from inspect4py

        Returns:
            Processed module information
        """
        result = {
            "name": module_name,
            "classes": [],
            "functions": [],
            "variables": [],
            "imports": [],
            "ast_type": "module",
        }

        # Extract docstring if available
        if "docstring" in module_info and self.options["extract_docstrings"]:
            result["docstring"] = module_info["docstring"]

        # Process classes
        if "classes" in module_info:
            for class_name, class_info in module_info["classes"].items():
                class_data = {
                    "name": class_name,
                    "methods": [],
                    "docstring": class_info.get("docstring", "")
                    if self.options["extract_docstrings"]
                    else "",
                    "line_start": class_info.get("line", 0),
                    "line_end": class_info.get("end_line", 0),
                    "ast_type": "class",
                }

                # Process class methods
                if "methods" in class_info:
                    for method_name, method_info in class_info["methods"].items():
                        method_data = {
                            "name": method_name,
                            "docstring": method_info.get("docstring", "")
                            if self.options["extract_docstrings"]
                            else "",
                            "line_start": method_info.get("line", 0),
                            "line_end": method_info.get("end_line", 0),
                            "is_method": True,
                            "class_name": class_name,
                            "ast_type": "function",
                        }

                        # Add parameter information if available
                        if "args" in method_info:
                            method_data["parameters"] = [
                                {"name": param} for param in method_info["args"]
                            ]

                        class_data["methods"].append(method_data)

                result["classes"].append(class_data)

        # Process functions
        if "functions" in module_info:
            for func_name, func_info in module_info["functions"].items():
                func_data = {
                    "name": func_name,
                    "docstring": func_info.get("docstring", "")
                    if self.options["extract_docstrings"]
                    else "",
                    "line_start": func_info.get("line", 0),
                    "line_end": func_info.get("end_line", 0),
                    "is_method": False,
                    "ast_type": "function",
                }

                # Add parameter information if available
                if "args" in func_info:
                    func_data["parameters"] = [
                        {"name": param} for param in func_info["args"]
                    ]

                result["functions"].append(func_data)

        # Process imports
        if "imports" in module_info:
            for import_info in module_info["imports"]:
                if isinstance(import_info, dict):
                    # Process detailed import info
                    import_data = {
                        "name": import_info.get("name", "unknown"),
                        "line_start": import_info.get("line", 0),
                        "type": "import",
                    }

                    # Handle from imports
                    if "from" in import_info:
                        import_data["fromname"] = import_info["from"]
                        import_data["type"] = "importfrom"

                    # Handle as imports
                    if "as" in import_info:
                        import_data["asname"] = import_info["as"]

                    result["imports"].append(import_data)
                elif isinstance(import_info, str):
                    # Simple import string
                    result["imports"].append({"name": import_info, "type": "import"})

        return result

    def _extract_basic_imports(self, tree) -> List[Dict[str, Any]]:
        """
        Extract basic imports from an AST tree.

        Args:
            tree: AST tree

        Returns:
            List of import information dictionaries
        """
        import ast

        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.append(
                        {
                            "name": name.name,
                            "asname": name.asname,
                            "line_start": node.lineno,
                            "type": "import",
                        }
                    )
            elif isinstance(node, ast.ImportFrom):
                for name in node.names:
                    if name.name == "*":
                        imports.append(
                            {
                                "name": "*",
                                "fromname": node.module,
                                "line_start": node.lineno,
                                "is_star": True,
                                "type": "importfrom",
                            }
                        )
                    else:
                        imports.append(
                            {
                                "name": name.name,
                                "asname": name.asname,
                                "fromname": node.module,
                                "line_start": node.lineno,
                                "type": "importfrom",
                            }
                        )

        return imports

    def parse_class(self, node: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a Python class definition using inspect4py.
        Note: This is not really used directly with inspect4py, which processes
        at the module level. This is included for API completeness.

        Args:
            node: AST node representing the class
            context: Parsing context

        Returns:
            Dictionary with parsed class information
        """
        logger.warning("inspect4py doesn't directly support class-level parsing")
        return {"ast_type": "class", "name": "unknown", "error": "Not supported"}

    def parse_function(self, node: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a Python function definition using inspect4py.
        Note: This is not really used directly with inspect4py, which processes
        at the module level. This is included for API completeness.

        Args:
            node: AST node representing the function
            context: Parsing context

        Returns:
            Dictionary with parsed function information
        """
        logger.warning("inspect4py doesn't directly support function-level parsing")
        return {"ast_type": "function", "name": "unknown", "error": "Not supported"}

    def parse_variable(
        self, node: Any, context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Parse a Python variable assignment using inspect4py.
        Note: This is not really used directly with inspect4py, which processes
        at the module level. This is included for API completeness.

        Args:
            node: AST node representing the variable assignment
            context: Parsing context

        Returns:
            List of dictionaries with parsed variable information
        """
        logger.warning("inspect4py doesn't directly support variable-level parsing")
        return [{"ast_type": "variable", "name": "unknown", "error": "Not supported"}]


# Register the plugin
register_plugin(Inspect4PyPlugin)
