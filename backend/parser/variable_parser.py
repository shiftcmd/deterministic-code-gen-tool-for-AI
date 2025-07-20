"""
Variable Parser for Python Debug Tool.

This module implements the parser for Python variables and constants,
extracting their assignments, type annotations, and usage patterns.

# AI-Intent: Core-Domain
# Intent: This parser implements the core domain logic for Python variable parsing
# Confidence: High
"""

import ast
import logging
from typing import Any, Dict, List, Optional, Set, Union

from .config import ParserConfig, ParserType
from .models import ParsedVariable

logger = logging.getLogger(__name__)


class VariableParser:
    """
    Parser for Python variables and constants.

    This class extracts comprehensive information about variable definitions,
    including type annotations, assigned values, and usage patterns.
    """

    def __init__(self, config: ParserConfig):
        """
        Initialize the variable parser with configuration.

        Args:
            config: Configuration for the parser
        """
        self.config = config

    def parse(
        self, node: Union[ast.Assign, ast.AnnAssign], scope: str = "module"
    ) -> List[ParsedVariable]:
        """
        Parse a variable assignment AST node.

        Args:
            node: Assignment AST node (Assign or AnnAssign)
            scope: Variable scope (module, class, function)

        Returns:
            List of ParsedVariable objects with extracted information
        """
        # Parse based on selected parser type
        if self.config.variable_parser == ParserType.BUILT_IN_AST:
            return self._parse_with_ast(node, scope)
        elif self.config.variable_parser == ParserType.ASTROID:
            return self._parse_with_astroid(node, scope)
        else:
            # Fallback to built-in AST
            logger.warning(
                f"Unsupported parser type {self.config.variable_parser}, "
                "falling back to built-in AST"
            )
            return self._parse_with_ast(node, scope)

    def _parse_with_ast(
        self, node: Union[ast.Assign, ast.AnnAssign], scope: str
    ) -> List[ParsedVariable]:
        """
        Parse a variable assignment using Python's built-in AST module.

        Args:
            node: Assignment AST node
            scope: Variable scope

        Returns:
            List of ParsedVariable objects
        """
        variables = []

        if isinstance(node, ast.AnnAssign):
            # Handle annotated assignment (x: int = 5)
            if isinstance(node.target, ast.Name):
                type_annotation = self._extract_annotation(node.annotation)
                value_repr = self._extract_value(node.value) if node.value else None
                is_constant = node.target.id.isupper() and "_" in node.target.id

                variables.append(
                    ParsedVariable(
                        name=node.target.id,
                        inferred_type=type_annotation,
                        value_repr=value_repr,
                        line_start=node.lineno,
                        line_end=getattr(node, "end_lineno", node.lineno),
                        is_class_var=(scope == "class"),
                        is_constant=is_constant,
                        scope=scope,
                    )
                )

        elif isinstance(node, ast.Assign):
            # Handle regular assignment (x = 5)
            value_repr = self._extract_value(node.value)

            for target in node.targets:
                if isinstance(target, ast.Name):
                    # Simple variable assignment
                    is_constant = target.id.isupper() and "_" in target.id

                    variables.append(
                        ParsedVariable(
                            name=target.id,
                            value_repr=value_repr,
                            line_start=node.lineno,
                            line_end=getattr(node, "end_lineno", node.lineno),
                            is_class_var=(scope == "class"),
                            is_constant=is_constant,
                            scope=scope,
                        )
                    )

                elif isinstance(target, ast.Tuple) or isinstance(target, ast.List):
                    # Handle unpacking assignment (a, b = 1, 2)
                    if isinstance(node.value, ast.Tuple) or isinstance(
                        node.value, ast.List
                    ):
                        # Try to match elements in the assignment
                        for idx, elt in enumerate(target.elts):
                            if isinstance(elt, ast.Name):
                                # Only handle simple name targets in unpacking
                                is_constant = elt.id.isupper() and "_" in elt.id
                                val_repr = "unknown"
                                if idx < len(node.value.elts):
                                    val_repr = self._extract_value(node.value.elts[idx])

                                variables.append(
                                    ParsedVariable(
                                        name=elt.id,
                                        value_repr=val_repr,
                                        line_start=node.lineno,
                                        line_end=getattr(
                                            node, "end_lineno", node.lineno
                                        ),
                                        is_class_var=(scope == "class"),
                                        is_constant=is_constant,
                                        scope=scope,
                                    )
                                )
                    else:
                        # Handle case like a, b = some_function()
                        for elt in target.elts:
                            if isinstance(elt, ast.Name):
                                is_constant = elt.id.isupper() and "_" in elt.id

                                variables.append(
                                    ParsedVariable(
                                        name=elt.id,
                                        value_repr="unpacked_value",
                                        line_start=node.lineno,
                                        line_end=getattr(
                                            node, "end_lineno", node.lineno
                                        ),
                                        is_class_var=(scope == "class"),
                                        is_constant=is_constant,
                                        scope=scope,
                                    )
                                )

                elif isinstance(target, ast.Attribute):
                    # Handle attribute assignment (self.x = 5)
                    if scope == "function":
                        # This is likely an instance attribute
                        if (
                            isinstance(target.value, ast.Name)
                            and target.value.id == "self"
                        ):
                            is_constant = target.attr.isupper() and "_" in target.attr

                            variables.append(
                                ParsedVariable(
                                    name=target.attr,
                                    value_repr=value_repr,
                                    line_start=node.lineno,
                                    line_end=getattr(node, "end_lineno", node.lineno),
                                    is_class_var=False,  # This is an instance variable
                                    is_constant=is_constant,
                                    scope="instance",  # Special scope for instance variables
                                )
                            )

        # Try to infer type from value if enabled
        if (
            self.config.infer_variable_types
            and variables
            and not variables[0].inferred_type
        ):
            inferred_type = self._infer_type_from_value(node.value)
            if inferred_type:
                for var in variables:
                    var.inferred_type = inferred_type

        return variables

    def _parse_with_astroid(self, node, scope: str) -> List[ParsedVariable]:
        """
        Parse a variable assignment using astroid for enhanced type inference.

        This implementation would depend on the actual astroid API.
        For now, it's a placeholder that would be implemented once
        astroid integration is added.

        Args:
            node: astroid.AssignName or astroid.AnnAssign node
            scope: Variable scope

        Returns:
            List of ParsedVariable objects
        """
        # This is a placeholder for astroid integration
        # In a real implementation, this would process an astroid node instead of ast
        logger.warning(
            "astroid variable parsing not implemented yet, falling back to AST"
        )

        # Convert astroid node to AST (this is a placeholder)
        # In reality, we would directly process the astroid node
        return self._parse_with_ast(node, scope)

    def _extract_value(self, node):
        """Extract a simplified string representation of the assigned value."""
        if isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.List):
            return "[...]"
        elif isinstance(node, ast.Dict):
            return "{...}"
        elif isinstance(node, ast.Tuple):
            return "(...)"
        elif isinstance(node, ast.Set):
            return "{...}"
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return f"{node.func.id}(...)"
            elif isinstance(node.func, ast.Attribute):
                return f"{self._get_attribute_path(node.func)}(...)"
        return "complex_value"

    def _extract_annotation(self, node):
        """Extract type annotation string from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_attribute_path(node)
        elif isinstance(node, ast.Subscript):
            # Handle generic types like List[str]
            if isinstance(node.value, ast.Name):
                container = node.value.id
            elif isinstance(node.value, ast.Attribute):
                container = self._get_attribute_path(node.value)
            else:
                return "complex_type"

            # Handle the slice/index part
            if isinstance(node.slice, ast.Name):
                param = node.slice.id
            elif isinstance(node.slice, ast.Tuple):
                params = []
                for elt in node.slice.elts:
                    if isinstance(elt, ast.Name):
                        params.append(elt.id)
                    else:
                        params.append("complex_type")
                param = ", ".join(params)
            else:
                param = "complex_type"

            return f"{container}[{param}]"
        return "complex_type"

    def _get_attribute_path(self, node):
        """Recursively build path for attribute nodes (e.g., module.submodule.attribute)."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_attribute_path(node.value)}.{node.attr}"
        return str(node)

    def _infer_type_from_value(self, node) -> Optional[str]:
        """
        Attempt to infer the type of a variable from its assigned value.

        Args:
            node: The AST node representing the assigned value

        Returns:
            Inferred type name as string, or None if unable to infer
        """
        if isinstance(node, ast.Constant):
            # Map Python types to their string names
            if isinstance(node.value, str):
                return "str"
            elif isinstance(node.value, int):
                return "int"
            elif isinstance(node.value, float):
                return "float"
            elif isinstance(node.value, bool):
                return "bool"
            elif node.value is None:
                return "None"
            else:
                return type(node.value).__name__
        elif isinstance(node, ast.List):
            return "list"
        elif isinstance(node, ast.Dict):
            return "dict"
        elif isinstance(node, ast.Set):
            return "set"
        elif isinstance(node, ast.Tuple):
            return "tuple"
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                # For simple constructor calls like list(), dict(), etc.
                return node.func.id
            # For other calls, we can't reliably infer the type

        return None
