"""
Module Parser for Python Debug Tool - Production Version.

This module implements the parser for Python module files, extracting
key elements like imports, classes, functions, and variables.

Key improvements:
- Uses CombinedVisitor for proper method-to-class linking
- Integrated status reporting
- Cleaner separation between AST parsing and element extraction
"""

import ast
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ast_visitors import CombinedVisitor
from config import ParserConfig, ParserType
from models import ParsedModule
from communication import StatusReporter, NullStatusReporter

logger = logging.getLogger(__name__)


class ModuleParser:
    """
    Parser for Python module files.
    
    This class is responsible for parsing Python modules and extracting their
    structural elements using the CombinedVisitor for proper element linking.
    """

    def __init__(self, config: ParserConfig):
        """
        Initialize the module parser.

        Args:
            config: Configuration for the parser
        """
        self.config = config

    def parse(
        self, 
        file_path: str,
        status_reporter: Optional[StatusReporter] = None
    ) -> ParsedModule:
        """
        Parse a Python module file.

        Args:
            file_path: Path to the Python file
            status_reporter: Optional status reporter for progress updates

        Returns:
            ParsedModule object with extracted information

        Raises:
            ValueError: If the file doesn't exist or isn't a Python file
            SyntaxError: If the file contains syntax errors
        """
        file_path = os.path.abspath(file_path)
        
        # Use null reporter if none provided
        if not status_reporter:
            status_reporter = NullStatusReporter()

        # Validate file
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")

        if not file_path.endswith(".py"):
            raise ValueError(f"Not a Python file: {file_path}")

        # Report module parsing start
        status_reporter.report_status(
            phase="extraction",
            status="parsing_module",
            message=f"Parsing module: {os.path.basename(file_path)}"
        )

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
            return self._parse_with_ast(file_path, content, parsed_module, status_reporter)
        elif self.config.module_parser == ParserType.ASTROID:
            return self._parse_with_astroid(file_path, parsed_module, status_reporter)
        elif self.config.module_parser == ParserType.INSPECT4PY:
            return self._parse_with_inspect4py(file_path, parsed_module, status_reporter)
        else:
            # Fallback to built-in AST
            logger.warning(
                f"Unsupported parser type {self.config.module_parser}, "
                "falling back to built-in AST"
            )
            return self._parse_with_ast(file_path, content, parsed_module, status_reporter)

    def _parse_with_ast(
        self, 
        file_path: str, 
        content: str, 
        parsed_module: ParsedModule,
        status_reporter: StatusReporter
    ) -> ParsedModule:
        """
        Parse a module using Python's built-in AST module.

        Args:
            file_path: Path to the Python file
            content: File content as string
            parsed_module: Partially populated ParsedModule object
            status_reporter: Status reporter for progress updates

        Returns:
            Completed ParsedModule object
        """
        try:
            # Parse the file into an AST
            tree = ast.parse(content, file_path)

            # Extract docstring if configured
            if self.config.extract_module_docstring:
                parsed_module.docstring = ast.get_docstring(tree)

            # Use CombinedVisitor to extract all elements with proper linking
            status_reporter.report_status(
                phase="extraction",
                status="extracting_elements",
                message=f"Extracting code elements from {parsed_module.name}"
            )
            
            combined_visitor = CombinedVisitor(status_reporter)
            extracted_elements = combined_visitor.visit(tree)
            
            # Populate module with extracted elements
            parsed_module.imports = extracted_elements["imports"]
            parsed_module.classes = extracted_elements["classes"]
            parsed_module.functions = extracted_elements["functions"]
            parsed_module.variables = extracted_elements["variables"]
            
            # Report completion
            status_reporter.report_status(
                phase="extraction",
                status="module_parsed",
                message=f"Successfully parsed module: {parsed_module.name}",
                metadata={
                    "classes": len(parsed_module.classes),
                    "functions": len(parsed_module.functions),
                    "imports": len(parsed_module.imports),
                    "variables": len(parsed_module.variables)
                }
            )

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
            
            status_reporter.report_status(
                phase="extraction",
                status="syntax_error",
                message=f"Syntax error in {os.path.basename(file_path)}: {e}"
            )
            
            return parsed_module

        except Exception as e:
            # Handle other errors
            parsed_module.ast_errors.append(
                {"error_type": type(e).__name__, "message": str(e)}
            )
            logger.warning(f"Error parsing {file_path}: {e}")
            
            status_reporter.report_status(
                phase="extraction",
                status="parse_error",
                message=f"Error parsing {os.path.basename(file_path)}: {e}"
            )
            
            return parsed_module

    def _parse_with_astroid(
        self, 
        file_path: str, 
        parsed_module: ParsedModule,
        status_reporter: StatusReporter
    ) -> ParsedModule:
        """
        Parse a module using astroid for enhanced type inference.

        Args:
            file_path: Path to the Python file
            parsed_module: Partially populated ParsedModule object
            status_reporter: Status reporter for progress updates

        Returns:
            Completed ParsedModule object
        """
        try:
            # Import astroid here to avoid dependency if not used
            import astroid

            status_reporter.report_status(
                phase="extraction",
                status="parsing_with_astroid",
                message=f"Using astroid to parse {os.path.basename(file_path)}"
            )

            # Parse with astroid
            module = astroid.parse(file_path)

            # Extract module docstring
            if self.config.extract_module_docstring:
                parsed_module.docstring = module.doc

            # For now, we'll convert astroid AST to standard AST and use our visitor
            # In a future enhancement, we could create AstroidVisitor classes
            content = module.as_string()
            tree = ast.parse(content, file_path)
            
            combined_visitor = CombinedVisitor(status_reporter)
            extracted_elements = combined_visitor.visit(tree)
            
            parsed_module.imports = extracted_elements["imports"]
            parsed_module.classes = extracted_elements["classes"]
            parsed_module.functions = extracted_elements["functions"]
            parsed_module.variables = extracted_elements["variables"]

            return parsed_module

        except ImportError:
            logger.warning("astroid not installed, falling back to built-in AST")
            status_reporter.report_status(
                phase="extraction",
                status="fallback",
                message="astroid not available, using built-in AST"
            )
            
            # Read file content and fall back to built-in AST
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return self._parse_with_ast(file_path, content, parsed_module, status_reporter)
            
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
            return self._parse_with_ast(file_path, content, parsed_module, status_reporter)

    def _parse_with_inspect4py(
        self, 
        file_path: str, 
        parsed_module: ParsedModule,
        status_reporter: StatusReporter
    ) -> ParsedModule:
        """
        Parse a module using inspect4py for comprehensive module analysis.

        Args:
            file_path: Path to the Python file
            parsed_module: Partially populated ParsedModule object
            status_reporter: Status reporter for progress updates

        Returns:
            Completed ParsedModule object
        """
        try:
            # Import inspect4py here to avoid dependency if not used
            # Note: This is a placeholder as inspect4py might require special handling
            
            logger.warning(
                "inspect4py integration not implemented yet, falling back to astroid"
            )
            status_reporter.report_status(
                phase="extraction",
                status="fallback",
                message="inspect4py not implemented, trying astroid"
            )
            
            return self._parse_with_astroid(file_path, parsed_module, status_reporter)

        except ImportError:
            logger.warning("inspect4py not installed, falling back to astroid")
            return self._parse_with_astroid(file_path, parsed_module, status_reporter)