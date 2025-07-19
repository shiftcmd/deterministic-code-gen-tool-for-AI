"""
Built-in AST parser plugin for Python Debug Tool.

This module implements a parser plugin using Python's built-in AST module,
providing basic parsing capabilities for Python code.
"""

import ast
import logging
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


class ASTVisitor(ast.NodeVisitor):
    """AST visitor for extracting elements from Python code."""

    def __init__(self):
        self.imports = []
        self.classes = []
        self.functions = []
        self.variables = []
        self.module_docstring = None

    def visit_Import(self, node: ast.Import):
        """Process import statements."""
        for name in node.names:
            self.imports.append(
                {
                    "name": name.name,
                    "asname": name.asname,
                    "line_start": node.lineno,
                    "line_end": node.lineno,
                    "type": "import",
                }
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Process from ... import ... statements."""
        for name in node.names:
            if name.name == "*":
                self.imports.append(
                    {
                        "name": "*",
                        "fromname": node.module,
                        "line_start": node.lineno,
                        "line_end": node.lineno,
                        "is_star": True,
                        "type": "importfrom",
                    }
                )
            else:
                self.imports.append(
                    {
                        "name": name.name,
                        "asname": name.asname,
                        "fromname": node.module,
                        "line_start": node.lineno,
                        "line_end": node.lineno,
                        "type": "importfrom",
                    }
                )
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        """Process class definitions."""
        docstring = ast.get_docstring(node)

        # Extract base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                # Handle cases like module.Class
                bases.append(
                    f"{base.value.id}.{base.attr}"
                    if isinstance(base.value, ast.Name)
                    else base.attr
                )

        # Extract class methods and attributes
        methods = []
        attributes = []

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(item.name)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attributes.append(target.id)

        self.classes.append(
            {
                "name": node.name,
                "docstring": docstring or "",
                "bases": bases,
                "methods": methods,
                "attributes": attributes,
                "line_start": node.lineno,
                "line_end": getattr(node, "end_lineno", node.lineno) or node.lineno,
                "decorators": [
                    d.id for d in node.decorator_list if isinstance(d, ast.Name)
                ],
                "type": "class",
            }
        )

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Process function definitions."""
        docstring = ast.get_docstring(node)

        # Extract parameters
        parameters = []
        default_values = {}

        # Handle default values for arguments
        defaults_offset = len(node.args.args) - len(node.args.defaults)
        for i, default in enumerate(node.args.defaults):
            arg_pos = i + defaults_offset
            if arg_pos < len(node.args.args):
                arg_name = node.args.args[arg_pos].arg
                if isinstance(default, ast.Constant):
                    default_values[arg_name] = default.value
                else:
                    default_values[arg_name] = "..."

        # Process all argument types
        for arg in node.args.args:
            param = {
                "name": arg.arg,
                "annotation": None,
                "has_default": arg.arg in default_values,
                "default_value": default_values.get(arg.arg, None),
            }

            # Extract type annotation if available (Python 3.6+)
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    param["annotation"] = arg.annotation.id
                elif isinstance(arg.annotation, ast.Constant) and isinstance(
                    arg.annotation.value, str
                ):
                    param["annotation"] = arg.annotation.value
                else:
                    param["annotation"] = "complex"

            parameters.append(param)

        # Handle *args and **kwargs
        if node.args.vararg:
            parameters.append(
                {
                    "name": f"*{node.args.vararg.arg}",
                    "annotation": None,
                    "has_default": False,
                    "default_value": None,
                }
            )

        if node.args.kwarg:
            parameters.append(
                {
                    "name": f"**{node.args.kwarg.arg}",
                    "annotation": None,
                    "has_default": False,
                    "default_value": None,
                }
            )

        # Extract return type annotation if available
        return_annotation = None
        if node.returns:
            if isinstance(node.returns, ast.Name):
                return_annotation = node.returns.id
            elif isinstance(node.returns, ast.Constant) and isinstance(
                node.returns.value, str
            ):
                return_annotation = node.returns.value
            else:
                return_annotation = "complex"

        self.functions.append(
            {
                "name": node.name,
                "docstring": docstring or "",
                "parameters": parameters,
                "return_annotation": return_annotation,
                "line_start": node.lineno,
                "line_end": getattr(node, "end_lineno", node.lineno) or node.lineno,
                "decorators": [
                    d.id for d in node.decorator_list if isinstance(d, ast.Name)
                ],
                "is_method": False,  # Will be updated later for class methods
                "is_static": "staticmethod"
                in [d.id for d in node.decorator_list if isinstance(d, ast.Name)],
                "is_class": "classmethod"
                in [d.id for d in node.decorator_list if isinstance(d, ast.Name)],
                "complexity": 1,  # Basic complexity, will be calculated later if needed
                "type": "function",
            }
        )

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        """Process variable assignments."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                # Handle simple assignments like x = 1
                self.variables.append(
                    {
                        "name": target.id,
                        "line_start": node.lineno,
                        "line_end": getattr(node, "end_lineno", node.lineno)
                        or node.lineno,
                        "inferred_type": self._infer_basic_type(node.value),
                        "is_constant": target.id.isupper(),
                        "type": "variable",
                    }
                )
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Process annotated assignments (Python 3.6+)."""
        if isinstance(node.target, ast.Name):
            annotation = None
            if isinstance(node.annotation, ast.Name):
                annotation = node.annotation.id
            elif isinstance(node.annotation, ast.Constant) and isinstance(
                node.annotation.value, str
            ):
                annotation = node.annotation.value

            self.variables.append(
                {
                    "name": node.target.id,
                    "line_start": node.lineno,
                    "line_end": getattr(node, "end_lineno", node.lineno) or node.lineno,
                    "inferred_type": annotation or self._infer_basic_type(node.value)
                    if node.value
                    else None,
                    "is_constant": node.target.id.isupper(),
                    "type": "variable",
                }
            )
        self.generic_visit(node)

    def visit_Module(self, node: ast.Module):
        """Process module-level elements."""
        self.module_docstring = ast.get_docstring(node) or ""
        self.generic_visit(node)

    def _infer_basic_type(self, node):
        """Infer basic types from AST nodes."""
        if isinstance(node, ast.Constant):
            return type(node.value).__name__
        elif isinstance(node, ast.Dict):
            return "dict"
        elif isinstance(node, ast.List):
            return "list"
        elif isinstance(node, ast.Tuple):
            return "tuple"
        elif isinstance(node, ast.Set):
            return "set"
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return node.func.id
        return "unknown"


class BuiltInASTPlugin(ParserPlugin):
    """Parser plugin using Python's built-in AST module."""

    name = "ast"
    description = "Basic parser using Python's built-in AST module"
    version = "1.0.0"
    supported_types = {"module", "class", "function", "variable"}
    requires_dependencies = []
    default_options = {"extract_docstrings": True, "infer_basic_types": True}

    def parse_module(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Parse a Python module file using the built-in AST.

        Args:
            file_path: Path to the Python file
            content: Content of the file

        Returns:
            Dictionary with parsed module information
        """
        try:
            tree = ast.parse(content, filename=file_path)
            visitor = ASTVisitor()
            visitor.visit(tree)

            result = {
                "imports": visitor.imports,
                "classes": visitor.classes,
                "functions": visitor.functions,
                "variables": visitor.variables,
                "docstring": visitor.module_docstring
                if self.options["extract_docstrings"]
                else "",
                "ast_type": "module",
            }

            # Update methods with is_method flag
            class_methods = set()
            for cls in visitor.classes:
                class_methods.update(cls.get("methods", []))

            for func in result["functions"]:
                if func["name"] in class_methods:
                    func["is_method"] = True

            return result

        except SyntaxError as e:
            logger.error(f"Syntax error in {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error parsing {file_path} with AST: {e}")
            raise

    def parse_class(
        self, node: ast.ClassDef, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Parse a Python class definition using the built-in AST.

        Args:
            node: AST node representing the class
            context: Parsing context

        Returns:
            Dictionary with parsed class information
        """
        docstring = (
            ast.get_docstring(node) if self.options["extract_docstrings"] else ""
        )

        # Extract base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(
                    f"{base.value.id}.{base.attr}"
                    if isinstance(base.value, ast.Name)
                    else base.attr
                )

        # Parse methods and class variables
        methods = []
        class_vars = []

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method = self.parse_function(
                    item, {"in_class": True, "class_name": node.name}
                )
                methods.append(method)
            elif isinstance(item, ast.Assign):
                for var in self.parse_variable(
                    item, {"scope": "class", "class_name": node.name}
                ):
                    class_vars.append(var)

        return {
            "name": node.name,
            "docstring": docstring,
            "bases": bases,
            "methods": methods,
            "variables": class_vars,
            "line_start": node.lineno,
            "line_end": getattr(node, "end_lineno", node.lineno) or node.lineno,
            "decorators": [
                d.id for d in node.decorator_list if isinstance(d, ast.Name)
            ],
            "ast_type": "class",
        }

    def parse_function(
        self, node: ast.FunctionDef, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Parse a Python function definition using the built-in AST.

        Args:
            node: AST node representing the function
            context: Parsing context

        Returns:
            Dictionary with parsed function information
        """
        docstring = (
            ast.get_docstring(node) if self.options["extract_docstrings"] else ""
        )

        # Handle parameters similarly to the ASTVisitor
        parameters = []
        default_values = {}

        defaults_offset = len(node.args.args) - len(node.args.defaults)
        for i, default in enumerate(node.args.defaults):
            arg_pos = i + defaults_offset
            if arg_pos < len(node.args.args):
                arg_name = node.args.args[arg_pos].arg
                if isinstance(default, ast.Constant):
                    default_values[arg_name] = default.value
                else:
                    default_values[arg_name] = "..."

        for arg in node.args.args:
            param = {
                "name": arg.arg,
                "annotation": None,
                "has_default": arg.arg in default_values,
                "default_value": default_values.get(arg.arg, None),
            }

            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    param["annotation"] = arg.annotation.id
                elif isinstance(arg.annotation, ast.Constant) and isinstance(
                    arg.annotation.value, str
                ):
                    param["annotation"] = arg.annotation.value
                else:
                    param["annotation"] = "complex"

            parameters.append(param)

        # Handle *args and **kwargs
        if node.args.vararg:
            parameters.append(
                {
                    "name": f"*{node.args.vararg.arg}",
                    "annotation": None,
                    "has_default": False,
                    "default_value": None,
                }
            )

        if node.args.kwarg:
            parameters.append(
                {
                    "name": f"**{node.args.kwarg.arg}",
                    "annotation": None,
                    "has_default": False,
                    "default_value": None,
                }
            )

        # Extract return type annotation
        return_annotation = None
        if node.returns:
            if isinstance(node.returns, ast.Name):
                return_annotation = node.returns.id
            elif isinstance(node.returns, ast.Constant) and isinstance(
                node.returns.value, str
            ):
                return_annotation = node.returns.value
            else:
                return_annotation = "complex"

        is_in_class = context.get("in_class", False)
        decorators = [d.id for d in node.decorator_list if isinstance(d, ast.Name)]

        return {
            "name": node.name,
            "docstring": docstring,
            "parameters": parameters,
            "return_annotation": return_annotation,
            "line_start": node.lineno,
            "line_end": getattr(node, "end_lineno", node.lineno) or node.lineno,
            "decorators": decorators,
            "is_method": is_in_class,
            "is_static": "staticmethod" in decorators,
            "is_class": "classmethod" in decorators,
            "class_name": context.get("class_name") if is_in_class else None,
            "complexity": 1,  # Basic complexity calculation
            "ast_type": "function",
        }

    def parse_variable(
        self, node: Union[ast.Assign, ast.AnnAssign], context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Parse a Python variable assignment using the built-in AST.

        Args:
            node: AST node representing the variable assignment
            context: Parsing context

        Returns:
            List of dictionaries with parsed variable information
        """
        variables = []

        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    variables.append(
                        {
                            "name": target.id,
                            "line_start": node.lineno,
                            "line_end": getattr(node, "end_lineno", node.lineno)
                            or node.lineno,
                            "inferred_type": self._infer_basic_type(node.value)
                            if self.options["infer_basic_types"]
                            else "unknown",
                            "is_constant": target.id.isupper(),
                            "scope": context.get("scope", "module"),
                            "class_name": context.get("class_name"),
                            "ast_type": "variable",
                        }
                    )
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                annotation = None
                if isinstance(node.annotation, ast.Name):
                    annotation = node.annotation.id
                elif isinstance(node.annotation, ast.Constant) and isinstance(
                    node.annotation.value, str
                ):
                    annotation = node.annotation.value

                variables.append(
                    {
                        "name": node.target.id,
                        "line_start": node.lineno,
                        "line_end": getattr(node, "end_lineno", node.lineno)
                        or node.lineno,
                        "inferred_type": annotation
                        or (
                            self._infer_basic_type(node.value)
                            if node.value and self.options["infer_basic_types"]
                            else "unknown"
                        ),
                        "is_constant": node.target.id.isupper(),
                        "scope": context.get("scope", "module"),
                        "class_name": context.get("class_name"),
                        "ast_type": "variable",
                    }
                )

        return variables

    def _infer_basic_type(self, node):
        """Infer basic types from AST nodes."""
        if isinstance(node, ast.Constant):
            return type(node.value).__name__
        elif isinstance(node, ast.Dict):
            return "dict"
        elif isinstance(node, ast.List):
            return "list"
        elif isinstance(node, ast.Tuple):
            return "tuple"
        elif isinstance(node, ast.Set):
            return "set"
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return node.func.id
        return "unknown"


# Register the plugin
register_plugin(BuiltInASTPlugin)
