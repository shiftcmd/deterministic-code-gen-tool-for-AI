"""
Module Parser for Python Debug Tool.

This module implements the parser for Python module files, extracting
key elements like imports, classes, functions, and variables.

# AI-Intent: Core-Domain
# Intent: This parser implements the core domain logic for Python module parsing
# Confidence: High
"""

import ast
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from .ast_visitors import ImportVisitor
from .class_parser import ClassParser
from .config import ParserConfig, ParserType
from .function_parser import FunctionParser
from .models import (
    ParsedClass,
    ParsedFunction,
    ParsedImport,
    ParsedModule,
    ParsedVariable,
)
from .variable_parser import VariableParser

logger = logging.getLogger(__name__)


class ModuleParser:
    """
    Parser for Python module files.

    This class is responsible for parsing Python modules and extracting their
    structural elements based on the provided configuration.
    """

    def __init__(self, config: ParserConfig):
        """
        Initialize the module parser.

        Args:
            config: Configuration for the parser
        """
        self.config = config

        # Dynamically select parsers based on configuration
        self._initialize_parsers()

    def _initialize_parsers(self):
        """Initialize the component parsers based on configuration."""
        self.class_parser = ClassParser(self.config)
        self.function_parser = FunctionParser(self.config)
        self.variable_parser = VariableParser(self.config)

    def parse(self, file_path: str) -> ParsedModule:
        """
        Parse a Python module file.

        Args:
            file_path: Path to the Python file

        Returns:
            ParsedModule object with extracted information

        Raises:
            ValueError: If the file doesn't exist or isn't a Python file
            SyntaxError: If the file contains syntax errors
        """
        file_path = os.path.abspath(file_path)

        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")

        if not file_path.endswith(".py"):
            raise ValueError(f"Not a Python file: {file_path}")

        # Read file content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Basic file metadata
        stat = os.stat(file_path)
        file_size = stat.st_size
        last_modified = datetime.fromtimestamp(stat.st_mtime).isoformat()

        # Get module name from the file path
        module_name = Path(file_path).stem

        # Create an initial parsed module object
        parsed_module = ParsedModule(
            name=module_name,
            path=file_path,
            line_count=len(content.splitlines()),
            size_bytes=file_size,
            last_modified=last_modified,
            ast_errors=[],
        )

        # Parse based on selected parser type
        if self.config.module_parser == ParserType.BUILT_IN_AST:
            return self._parse_with_ast(file_path, content, parsed_module)
        elif self.config.module_parser == ParserType.ASTROID:
            return self._parse_with_astroid(file_path, parsed_module)
        elif self.config.module_parser == ParserType.INSPECT4PY:
            return self._parse_with_inspect4py(file_path, parsed_module)
        else:
            # Fallback to built-in AST
            logger.warning(
                f"Unsupported parser type {self.config.module_parser}, "
                "falling back to built-in AST"
            )
            return self._parse_with_ast(file_path, content, parsed_module)

    def _parse_with_ast(
        self, file_path: str, content: str, parsed_module: ParsedModule
    ) -> ParsedModule:
        """
        Parse a module using Python's built-in AST module.

        Args:
            file_path: Path to the Python file
            content: File content as string
            parsed_module: Partially populated ParsedModule object

        Returns:
            Completed ParsedModule object
        """
        try:
            # Parse the file into an AST
            tree = ast.parse(content, file_path)

            # Extract docstring if configured
            if self.config.extract_module_docstring:
                parsed_module.docstring = ast.get_docstring(tree)

            # Process imports using the import visitor
            import_visitor = ImportVisitor()
            import_visitor.visit(tree)
            parsed_module.imports = import_visitor.imports

            # Process classes using specialized class parser
            parsed_classes = []
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    parsed_class = self.class_parser.parse(node)
                    parsed_classes.append(parsed_class)

            parsed_module.classes = parsed_classes

            # Process top-level functions using specialized function parser
            parsed_functions = []
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    parsed_function = self.function_parser.parse(node)
                    parsed_functions.append(parsed_function)

            parsed_module.functions = parsed_functions

            # Process top-level variables using specialized variable parser
            parsed_variables = []
            for node in tree.body:
                if isinstance(node, ast.Assign) or isinstance(node, ast.AnnAssign):
                    variables = self.variable_parser.parse(node, scope="module")
                    if variables:
                        parsed_variables.extend(variables)

            parsed_module.variables = parsed_variables

            return parsed_module

        except SyntaxError as e:
            # Handle syntax errors
            parsed_module.ast_errors.append(
                {
                    "error_type": "SyntaxError",
                    "message": str(e),
                    "line": getattr(e, "lineno", None),
                    "offset": getattr(e, "offset", None),
                }
            )
            logger.warning(f"Syntax error parsing {file_path}: {e}")
            return parsed_module

        except Exception as e:
            # Handle other errors
            parsed_module.ast_errors.append(
                {"error_type": type(e).__name__, "message": str(e)}
            )
            logger.warning(f"Error parsing {file_path}: {e}")
            return parsed_module

    def _parse_with_astroid(
        self, file_path: str, parsed_module: ParsedModule
    ) -> ParsedModule:
        """
        Parse a module using astroid for enhanced type inference.

        Args:
            file_path: Path to the Python file
            parsed_module: Partially populated ParsedModule object

        Returns:
            Completed ParsedModule object
        """
        try:
            # Import astroid here to avoid dependency if not used
            import astroid

            # Parse with astroid
            module = astroid.parse(file_path)

            # Extract module docstring
            if self.config.extract_module_docstring:
                parsed_module.docstring = module.doc

            # Process imports
            if self.config.extract_imports:
                parsed_module.imports = self._extract_astroid_imports(module)

            # Process classes
            parsed_module.classes = self._extract_astroid_classes(module)

            # Process functions
            parsed_module.functions = self._extract_astroid_functions(module)

            # Process variables
            parsed_module.variables = self._extract_astroid_variables(module)

            return parsed_module

        except ImportError:
            logger.warning("astroid not installed, falling back to built-in AST")
            # Read file content and fall back to built-in AST
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return self._parse_with_ast(file_path, content, parsed_module)
        except Exception as e:
            parsed_module.ast_errors.append(
                {
                    "error_type": type(e).__name__,
                    "message": str(e),
                }
            )
            logger.warning(f"Error parsing {file_path} with astroid: {e}")
            # Read file content and fall back to built-in AST
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return self._parse_with_ast(file_path, content, parsed_module)

    def _parse_with_inspect4py(
        self, file_path: str, parsed_module: ParsedModule
    ) -> ParsedModule:
        """
        Parse a module using inspect4py for comprehensive module analysis.

        Args:
            file_path: Path to the Python file
            parsed_module: Partially populated ParsedModule object

        Returns:
            Completed ParsedModule object
        """
        try:
            # Import inspect4py here to avoid dependency if not used
            # Note: This is a placeholder as inspect4py might require special handling
            # Actual implementation would depend on inspect4py's API

            logger.warning(
                "inspect4py integration not implemented yet, " "falling back to astroid"
            )
            return self._parse_with_astroid(file_path, parsed_module)

        except ImportError:
            logger.warning("inspect4py not installed, falling back to astroid")
            return self._parse_with_astroid(file_path, parsed_module)

    def _extract_astroid_imports(self, module) -> List[ParsedImport]:
        """Extract imports using astroid."""
        imports = []

        for node in module.body:
            if isinstance(node, astroid.Import):
                for name, alias in node.names:
                    imports.append(
                        ParsedImport(
                            name=name,
                            asname=alias,
                            line_start=node.lineno,
                            line_end=node.lineno,
                        )
                    )

            elif isinstance(node, astroid.ImportFrom):
                for name, alias in node.names:
                    if name == "*":
                        imports.append(
                            ParsedImport(
                                name="*",
                                fromname=node.modname,
                                line_start=node.lineno,
                                line_end=node.lineno,
                                is_star=True,
                            )
                        )
                    else:
                        imports.append(
                            ParsedImport(
                                name=name,
                                asname=alias,
                                fromname=node.modname,
                                line_start=node.lineno,
                                line_end=node.lineno,
                            )
                        )

        return imports

    def _extract_astroid_classes(self, module) -> List[ParsedClass]:
        """Extract classes using astroid."""
        parsed_classes = []

        # Find all class definitions in the module
        for node in module.body:
            if isinstance(node, astroid.ClassDef):
                # Convert astroid node to AST for now
                # In a more complete implementation, the class parser would
                # handle astroid nodes directly
                try:
                    parsed_class = self.class_parser._parse_with_astroid(node)
                    parsed_classes.append(parsed_class)
                except Exception as e:
                    logger.warning(f"Error parsing class {node.name} with astroid: {e}")

        return parsed_classes

    def _extract_astroid_functions(self, module) -> List[ParsedFunction]:
        """Extract functions using astroid."""
        parsed_functions = []

        # Find all function definitions in the module
        for node in module.body:
            if isinstance(node, astroid.FunctionDef):
                # Convert astroid node to AST for now
                # In a more complete implementation, the function parser would
                # handle astroid nodes directly
                try:
                    parsed_function = self.function_parser._parse_with_astroid(node)
                    parsed_functions.append(parsed_function)
                except Exception as e:
                    logger.warning(
                        f"Error parsing function {node.name} with astroid: {e}"
                    )

        return parsed_functions

    def _extract_astroid_variables(self, module) -> List[ParsedVariable]:
        """Extract variables using astroid."""
        parsed_variables = []

        # Find all assignments in the module
        for node in module.body:
            if isinstance(node, astroid.Assign) or isinstance(node, astroid.AnnAssign):
                # Convert astroid node to AST for now
                # In a more complete implementation, the variable parser would
                # handle astroid nodes directly
                try:
                    variables = self.variable_parser._parse_with_astroid(
                        node, scope="module"
                    )
                    if variables:
                        parsed_variables.extend(variables)
                except Exception as e:
                    logger.warning(
                        f"Error parsing variable assignment with astroid: {e}"
                    )

        return parsed_variables
