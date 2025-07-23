"""
Function Parser for Python Debug Tool.

This module implements the parser for Python function and method definitions,
extracting their parameters, return types, decorators, and other metadata.

# AI-Intent: Core-Domain
# Intent: This parser implements the core domain logic for Python function parsing
# Confidence: High
"""

import ast
import logging
from typing import Any, Dict, List, Optional, Set, Union

from .config import ParserConfig, ParserType
from .models import ParsedFunction, ParsedVariable

logger = logging.getLogger(__name__)


class FunctionParser:
    """
    Parser for Python function and method definitions.

    This class extracts comprehensive information about function definitions,
    including parameters, return types, decorators, and complexity metrics.
    """

    def __init__(self, config: ParserConfig):
        """
        Initialize the function parser with configuration.

        Args:
            config: Configuration for the parser
        """
        self.config = config

    def parse(self, node: ast.FunctionDef) -> ParsedFunction:
        """
        Parse a function definition AST node.

        Args:
            node: FunctionDef AST node

        Returns:
            ParsedFunction object with extracted information
        """
        # Parse based on selected parser type
        if self.config.function_parser == ParserType.BUILT_IN_AST:
            return self._parse_with_ast(node)
        elif self.config.function_parser == ParserType.ASTROID:
            return self._parse_with_astroid(node)
        else:
            # Fallback to built-in AST
            logger.warning(
                f"Unsupported parser type {self.config.function_parser}, "
                "falling back to built-in AST"
            )
            return self._parse_with_ast(node)

    def _parse_with_ast(self, node: ast.FunctionDef) -> ParsedFunction:
        """
        Parse a function definition using Python's built-in AST module.

        Args:
            node: FunctionDef AST node

        Returns:
            ParsedFunction object
        """
        # Extract parameters
        parameters = self._extract_parameters(node.args)

        # Extract decorators and check for special method decorators
        decorators = []
        is_static = False
        is_class_method = False

        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                dec_name = decorator.id
                decorators.append(dec_name)
                is_static = is_static or dec_name == "staticmethod"
                is_class_method = is_class_method or dec_name == "classmethod"
            elif isinstance(decorator, ast.Call) and isinstance(
                decorator.func, ast.Name
            ):
                decorators.append(f"{decorator.func.id}(...)")
            elif isinstance(decorator, ast.Attribute):
                attr_path = self._get_attribute_path(decorator)
                decorators.append(attr_path)
                is_static = is_static or attr_path == "staticmethod"
                is_class_method = is_class_method or attr_path == "classmethod"

        # Extract return type if available
        return_type = None
        if node.returns:
            if isinstance(node.returns, ast.Name):
                return_type = node.returns.id
            elif isinstance(node.returns, ast.Attribute):
                return_type = self._get_attribute_path(node.returns)
            elif isinstance(node.returns, ast.Subscript):
                # Handle generic types like List[str]
                return_type = self._extract_annotation(node.returns)

        # Build signature
        signature_parts = []
        signature_parts.append(f"def {node.name}(")

        # Add parameters to signature
        param_strs = []
        for param in parameters:
            param_str = param["name"]
            if param.get("annotation"):
                param_str += f": {param['annotation']}"
            if param.get("default"):
                param_str += f" = {param['default']}"
            param_strs.append(param_str)

        signature_parts.append(", ".join(param_strs))
        signature_parts.append(")")

        if return_type:
            signature_parts.append(f" -> {return_type}")

        signature = "".join(signature_parts)

        # Extract docstring
        docstring = None
        if self.config.extract_function_docstring:
            docstring = ast.get_docstring(node)

        # Calculate complexity metrics if configured
        complexity = 0
        if self.config.compute_complexity:
            complexity = self._calculate_complexity(node)

        # Create parsed function
        function = ParsedFunction(
            name=node.name,
            signature=signature,
            docstring=docstring,
            parameters=parameters,
            return_type=return_type,
            variables=[],  # Will be filled by a variable visitor
            nested_functions=[],  # Will be filled by processing function body
            line_start=node.lineno,
            line_end=getattr(node, "end_lineno", node.lineno),
            decorators=decorators,
            is_method=False,  # Will be set by caller
            is_static=is_static,
            is_class_method=is_class_method,
            complexity=complexity,
        )

        # Process function body to extract nested functions and local variables
        if not self._is_abstract_method(node):
            self._process_function_body(node, function)

        return function

    def _parse_with_astroid(self, node) -> ParsedFunction:
        """
        Parse a function definition using astroid for enhanced type inference.

        This implementation would depend on the actual astroid API.
        For now, it's a placeholder that would be implemented once
        astroid integration is added.

        Args:
            node: astroid.FunctionDef node

        Returns:
            ParsedFunction object
        """
        # This is a placeholder for astroid integration
        # In a real implementation, this would process an astroid node instead of ast
        logger.warning(
            "astroid function parsing not implemented yet, falling back to AST"
        )

        # Convert astroid node to AST (this is a placeholder)
        # In reality, we would directly process the astroid node
        return self._parse_with_ast(node)

    def _extract_parameters(self, args: ast.arguments) -> List[Dict[str, Any]]:
        """
        Extract function parameters from arguments node.

        Args:
            args: Function arguments AST node

        Returns:
            List of parameter dictionaries with name, position, kind, annotation, default
        """
        parameters = []

        # Process positional arguments
        for i, arg in enumerate(args.args):
            param = {"name": arg.arg, "position": i, "kind": "positional"}

            # Extract type annotation if available
            if arg.annotation:
                param["annotation"] = self._extract_annotation(arg.annotation)

            # Extract default value if available
            if i >= len(args.args) - len(args.defaults):
                default_idx = i - (len(args.args) - len(args.defaults))
                param["default"] = self._extract_default_value(
                    args.defaults[default_idx]
                )

            parameters.append(param)

        # Process keyword-only arguments
        for i, arg in enumerate(args.kwonlyargs):
            param = {"name": arg.arg, "kind": "keyword_only"}

            # Extract type annotation if available
            if arg.annotation:
                param["annotation"] = self._extract_annotation(arg.annotation)

            # Extract default value if available
            if i < len(args.kw_defaults) and args.kw_defaults[i] is not None:
                param["default"] = self._extract_default_value(args.kw_defaults[i])

            parameters.append(param)

        # Process *args
        if args.vararg:
            parameters.append(
                {
                    "name": f"*{args.vararg.arg}",
                    "kind": "vararg",
                    "annotation": (
                        self._extract_annotation(args.vararg.annotation)
                        if args.vararg.annotation
                        else None
                    ),
                }
            )

        # Process **kwargs
        if args.kwarg:
            parameters.append(
                {
                    "name": f"**{args.kwarg.arg}",
                    "kind": "kwarg",
                    "annotation": (
                        self._extract_annotation(args.kwarg.annotation)
                        if args.kwarg.annotation
                        else None
                    ),
                }
            )

        return parameters

    def _process_function_body(
        self, node: ast.FunctionDef, parsed_function: ParsedFunction
    ):
        """
        Process the body of a function to extract nested functions and local variables.

        Args:
            node: FunctionDef AST node
            parsed_function: Partially populated ParsedFunction object
        """
        from .variable_parser import VariableParser

        variable_parser = VariableParser(self.config)

        # Track imported modules within this function scope
        local_imports = []

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                # Process nested function
                nested_function = self.parse(item)
                parsed_function.nested_functions.append(nested_function)
            elif isinstance(item, ast.Assign) or isinstance(item, ast.AnnAssign):
                # Process local variables
                vars = variable_parser.parse(item, scope="function")
                if vars:
                    parsed_function.variables.extend(vars)
            elif isinstance(item, ast.Import) or isinstance(item, ast.ImportFrom):
                # Process local imports
                pass  # Simplified version, would extract local imports in a full implementation

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """
        Calculate the cyclomatic complexity of a function.

        This is a simplified version that counts branching statements.
        A more accurate implementation would use McCabe's algorithm.

        Args:
            node: FunctionDef AST node

        Returns:
            Estimated cyclomatic complexity
        """
        complexity = 1  # Base complexity

        class ComplexityVisitor(ast.NodeVisitor):
            def __init__(self):
                self.complexity = 0

            def visit_If(self, node):
                self.complexity += 1
                self.generic_visit(node)

            def visit_For(self, node):
                self.complexity += 1
                self.generic_visit(node)

            def visit_While(self, node):
                self.complexity += 1
                self.generic_visit(node)

            def visit_Try(self, node):
                # Count each except clause
                self.complexity += len(node.handlers)
                self.generic_visit(node)

            def visit_ExceptHandler(self, node):
                self.generic_visit(node)

            def visit_With(self, node):
                self.complexity += 1
                self.generic_visit(node)

            def visit_Assert(self, node):
                self.complexity += 1
                self.generic_visit(node)

            def visit_BoolOp(self, node):
                # Count boolean operators (and, or)
                if isinstance(node.op, ast.And) or isinstance(node.op, ast.Or):
                    self.complexity += len(node.values) - 1
                self.generic_visit(node)

        visitor = ComplexityVisitor()
        visitor.visit(node)

        return complexity + visitor.complexity

    def _is_abstract_method(self, node: ast.FunctionDef) -> bool:
        """
        Check if a function is an abstract method (only pass/ellipsis).

        Args:
            node: FunctionDef AST node

        Returns:
            True if the function is an abstract method, False otherwise
        """
        if len(node.body) == 1:
            stmt = node.body[0]
            if isinstance(stmt, ast.Pass) or (
                isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Constant)
                and stmt.value.value is Ellipsis
            ):
                return True
        return False

    def _extract_annotation(self, node) -> str:
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

    def _extract_default_value(self, node) -> str:
        """Extract default parameter value from AST node."""
        if isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.List):
            return "[]"  # Simplified representation
        elif isinstance(node, ast.Dict):
            return "{}"  # Simplified representation
        elif isinstance(node, ast.Tuple):
            return "()"  # Simplified representation
        elif isinstance(node, ast.Set):
            return "set()"  # Simplified representation
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return f"{node.func.id}(...)"
            elif isinstance(node.func, ast.Attribute):
                return f"{self._get_attribute_path(node.func)}(...)"
        return "complex_value"

    def _get_attribute_path(self, node) -> str:
        """Recursively build path for attribute nodes (e.g., module.submodule.Class)."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_attribute_path(node.value)}.{node.attr}"
        return str(node)
