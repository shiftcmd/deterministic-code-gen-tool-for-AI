"""
Class Parser for Python Debug Tool.

This module implements the parser for Python class definitions,
extracting their methods, attributes, inheritance, and metadata.

# AI-Intent: Core-Domain
# Intent: This parser implements the core domain logic for Python class parsing
# Confidence: High
"""

import ast
import logging
from typing import Any, Dict, List, Optional, Set

from .ast_visitors import ClassVisitor
from .config import ParserConfig, ParserType
from .models import ParsedClass, ParsedFunction, ParsedVariable

logger = logging.getLogger(__name__)


class ClassParser:
    """
    Parser for Python class definitions.

    This class extracts comprehensive information about class definitions,
    including inheritance hierarchies, methods, class variables, and relationships.
    """

    def __init__(self, config: ParserConfig):
        """
        Initialize the class parser with configuration.

        Args:
            config: Configuration for the parser
        """
        self.config = config

    def parse(self, node: ast.ClassDef) -> ParsedClass:
        """
        Parse a class definition AST node.

        Args:
            node: ClassDef AST node

        Returns:
            ParsedClass object with extracted information
        """
        # Parse based on selected parser type
        if self.config.class_parser == ParserType.BUILT_IN_AST:
            return self._parse_with_ast(node)
        elif self.config.class_parser == ParserType.ASTROID:
            return self._parse_with_astroid(node)
        else:
            # Fallback to built-in AST
            logger.warning(
                f"Unsupported parser type {self.config.class_parser}, "
                "falling back to built-in AST"
            )
            return self._parse_with_ast(node)

    def _parse_with_ast(self, node: ast.ClassDef) -> ParsedClass:
        """
        Parse a class definition using Python's built-in AST module.

        Args:
            node: ClassDef AST node

        Returns:
            ParsedClass object
        """
        # Extract base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                # Handle cases like 'module.BaseClass'
                bases.append(self._get_attribute_path(base))

        # Extract decorators
        decorators = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            elif isinstance(decorator, ast.Call) and isinstance(
                decorator.func, ast.Name
            ):
                decorators.append(f"{decorator.func.id}(...)")
            elif isinstance(decorator, ast.Attribute):
                decorators.append(self._get_attribute_path(decorator))

        # Extract docstring
        docstring = None
        if self.config.extract_class_docstring:
            docstring = ast.get_docstring(node)

        # Create parsed class
        parsed_class = ParsedClass(
            name=node.name,
            bases=bases,
            docstring=docstring,
            methods=[],  # Will be filled by processing class body
            attributes=[],  # Will be filled by processing class body
            line_start=node.lineno,
            line_end=getattr(node, "end_lineno", node.lineno),
            decorators=decorators,
            inner_classes=[],  # Will be filled by processing class body
        )

        # Process class body
        self._process_class_body(node, parsed_class)

        return parsed_class

    def _parse_with_astroid(self, node) -> ParsedClass:
        """
        Parse a class definition using astroid for enhanced type inference.

        This implementation would depend on the actual astroid API.
        For now, it's a placeholder that would be implemented once
        astroid integration is added.

        Args:
            node: astroid.ClassDef node

        Returns:
            ParsedClass object
        """
        # This is a placeholder for astroid integration
        # In a real implementation, this would process an astroid node instead of ast
        logger.warning("astroid class parsing not implemented yet, falling back to AST")

        # Convert astroid node to AST (this is a placeholder)
        # In reality, we would directly process the astroid node
        return self._parse_with_ast(node)

    def _process_class_body(self, node: ast.ClassDef, parsed_class: ParsedClass):
        """
        Process the body of a class definition to extract methods, attributes, and nested classes.

        Args:
            node: ClassDef AST node
            parsed_class: Partially populated ParsedClass object
        """
        from .function_parser import FunctionParser

        function_parser = FunctionParser(self.config)

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                # Process method
                method = function_parser.parse(item)
                method.is_method = True
                parsed_class.methods.append(method)

            elif isinstance(item, ast.ClassDef):
                # Process nested class
                nested_class = self.parse(item)
                parsed_class.inner_classes.append(nested_class)

            elif isinstance(item, ast.Assign):
                # Process class variable
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        # Simple class variable (X = 1)
                        value_repr = self._extract_value(item.value)
                        is_constant = target.id.isupper() and "_" in target.id

                        parsed_class.attributes.append(
                            ParsedVariable(
                                name=target.id,
                                value_repr=value_repr,
                                line_start=item.lineno,
                                line_end=getattr(item, "end_lineno", item.lineno),
                                is_class_var=True,
                                is_constant=is_constant,
                                scope="class",
                            )
                        )

            elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                # Process annotated class variable (X: int = 1)
                type_annotation = self._extract_annotation(item.annotation)
                value_repr = self._extract_value(item.value) if item.value else None
                is_constant = item.target.id.isupper() and "_" in item.target.id

                parsed_class.attributes.append(
                    ParsedVariable(
                        name=item.target.id,
                        inferred_type=type_annotation,
                        value_repr=value_repr,
                        line_start=item.lineno,
                        line_end=getattr(item, "end_lineno", item.lineno),
                        is_class_var=True,
                        is_constant=is_constant,
                        scope="class",
                    )
                )

    def _get_attribute_path(self, node):
        """Recursively build path for attribute nodes (e.g., module.submodule.Class)."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_attribute_path(node.value)}.{node.attr}"
        return str(node)

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
