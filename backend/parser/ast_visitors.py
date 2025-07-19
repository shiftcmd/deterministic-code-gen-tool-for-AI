"""
AST Visitors for Python Debug Tool.

This module implements various AST node visitors that extract different
structural elements from Python code, such as classes, functions,
imports, and variables.

# AI-Intent: Core-Domain
# Intent: These visitors implement the core parsing logic to extract structural elements
# Confidence: High
"""

import ast
import logging
from typing import Any, Dict, List, Optional, Set

from .models import ParsedClass, ParsedFunction, ParsedImport, ParsedVariable

logger = logging.getLogger(__name__)


class ClassVisitor(ast.NodeVisitor):
    """
    AST visitor that extracts class definitions from Python code.
    """

    def __init__(self):
        self.classes: List[ParsedClass] = []
        self.current_class = None

    def visit_ClassDef(self, node):
        """Visit a class definition node."""
        # Get base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                # Handle cases like 'module.BaseClass'
                bases.append(f"{self._get_attribute_path(base)}")

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

        # Create parsed class
        class_info = ParsedClass(
            name=node.name,
            bases=bases,
            docstring=ast.get_docstring(node),
            methods=[],
            attributes=[],
            line_start=node.lineno,
            line_end=getattr(node, "end_lineno", node.lineno),
            decorators=decorators,
            inner_classes=[],
        )

        # Handle nested class vs. top-level class
        parent_class = self.current_class
        self.current_class = class_info

        # Visit children (to extract methods, attributes, nested classes)
        self.generic_visit(node)

        # Restore parent context and add to appropriate list
        self.current_class = parent_class

        if parent_class:
            parent_class.inner_classes.append(class_info)
        else:
            self.classes.append(class_info)

    def _get_attribute_path(self, node):
        """Recursively build path for attribute nodes (e.g., module.submodule.Class)."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_attribute_path(node.value)}.{node.attr}"
        return str(node)


class FunctionVisitor(ast.NodeVisitor):
    """
    AST visitor that extracts function and method definitions from Python code.
    """

    def __init__(self):
        self.functions: List[ParsedFunction] = []
        self.current_class = None
        self.current_function = None

    def visit_FunctionDef(self, node):
        """Visit a function definition node."""
        # Extract parameters
        parameters = self._extract_parameters(node.args)

        # Extract decorators
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

        # Create parsed function
        function_info = ParsedFunction(
            name=node.name,
            signature=signature,
            docstring=ast.get_docstring(node),
            parameters=parameters,
            return_type=return_type,
            variables=[],  # Will be filled by VariableVisitor
            nested_functions=[],
            line_start=node.lineno,
            line_end=getattr(node, "end_lineno", node.lineno),
            decorators=decorators,
            is_method=self.current_class is not None,
            is_static=is_static,
            is_class_method=is_class_method,
        )

        # Handle nested function vs. top-level function
        parent_function = self.current_function
        self.current_function = function_info

        # Visit children (to extract nested functions, variables)
        self.generic_visit(node)

        # Restore parent context and add to appropriate list
        self.current_function = parent_function

        if parent_function:
            parent_function.nested_functions.append(function_info)
        elif self.current_class:
            # This is a method, add it to the current class
            pass  # In a real implementation, would add to current class methods
        else:
            self.functions.append(function_info)

    def _extract_parameters(self, args):
        """Extract function parameters from args node."""
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

    def _extract_annotation(self, node):
        """Extract type annotation from AST node."""
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

            # Handle the slice/index part (e.g., the 'str' in List[str])
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
        else:
            return "complex_type"

    def _extract_default_value(self, node):
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

    def _get_attribute_path(self, node):
        """Recursively build path for attribute nodes (e.g., module.submodule.Class)."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_attribute_path(node.value)}.{node.attr}"
        return str(node)


class ImportVisitor(ast.NodeVisitor):
    """
    AST visitor that extracts import statements from Python code.
    """

    def __init__(self):
        self.imports: List[ParsedImport] = []

    def visit_Import(self, node):
        """Visit an import node (e.g., 'import os')."""
        for name in node.names:
            self.imports.append(
                ParsedImport(
                    name=name.name,
                    asname=name.asname,
                    line_start=node.lineno,
                    line_end=getattr(node, "end_lineno", node.lineno),
                )
            )

    def visit_ImportFrom(self, node):
        """Visit an import-from node (e.g., 'from os import path')."""
        for name in node.names:
            if name.name == "*":
                # Handle star imports (from module import *)
                self.imports.append(
                    ParsedImport(
                        name="*",
                        fromname=node.module,
                        line_start=node.lineno,
                        line_end=getattr(node, "end_lineno", node.lineno),
                        is_star=True,
                    )
                )
            else:
                # Regular from-import
                self.imports.append(
                    ParsedImport(
                        name=name.name,
                        asname=name.asname,
                        fromname=node.module,
                        line_start=node.lineno,
                        line_end=getattr(node, "end_lineno", node.lineno),
                    )
                )


class VariableVisitor(ast.NodeVisitor):
    """
    AST visitor that extracts variable assignments from Python code.
    """

    def __init__(self):
        self.variables: List[ParsedVariable] = []
        self.current_scope = "module"  # 'module', 'class', or 'function'

    def visit_Assign(self, node):
        """Visit an assignment node."""
        # Extract the assigned value (simplified representation)
        value_repr = self._extract_value(node.value)

        # Handle multiple assignment targets (a = b = 1)
        for target in node.targets:
            if isinstance(target, ast.Name):
                # Simple variable assignment (x = 1)
                self._add_variable(
                    name=target.id,
                    value_repr=value_repr,
                    line_start=node.lineno,
                    line_end=getattr(node, "end_lineno", node.lineno),
                )
            elif isinstance(target, ast.Tuple) or isinstance(target, ast.List):
                # Multiple assignment (a, b = 1, 2)
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        self._add_variable(
                            name=elt.id,
                            value_repr="[part of multiple assignment]",
                            line_start=node.lineno,
                            line_end=getattr(node, "end_lineno", node.lineno),
                        )
            elif isinstance(target, ast.Attribute) and isinstance(
                target.value, ast.Name
            ):
                # Class attribute assignment (self.x = 1)
                if target.value.id == "self" and self.current_scope == "function":
                    self._add_variable(
                        name=f"self.{target.attr}",
                        value_repr=value_repr,
                        line_start=node.lineno,
                        line_end=getattr(node, "end_lineno", node.lineno),
                        is_class_var=False,  # Instance variable
                    )
                elif self.current_scope == "class":
                    self._add_variable(
                        name=target.attr,
                        value_repr=value_repr,
                        line_start=node.lineno,
                        line_end=getattr(node, "end_lineno", node.lineno),
                        is_class_var=True,  # Class variable
                    )

        # Continue visiting children
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        """Visit an annotated assignment (x: int = 1)."""
        if isinstance(node.target, ast.Name):
            # Extract type annotation
            type_annotation = self._extract_annotation(node.annotation)

            # Extract value if available
            value_repr = self._extract_value(node.value) if node.value else None

            self._add_variable(
                name=node.target.id,
                value_repr=value_repr,
                line_start=node.lineno,
                line_end=getattr(node, "end_lineno", node.lineno),
                inferred_type=type_annotation,
            )

        # Continue visiting children
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        """Update scope when entering a class definition."""
        old_scope = self.current_scope
        self.current_scope = "class"
        self.generic_visit(node)
        self.current_scope = old_scope

    def visit_FunctionDef(self, node):
        """Update scope when entering a function definition."""
        old_scope = self.current_scope
        self.current_scope = "function"
        self.generic_visit(node)
        self.current_scope = old_scope

    def _add_variable(
        self,
        name,
        value_repr,
        line_start,
        line_end,
        inferred_type=None,
        is_class_var=False,
    ):
        """Add a parsed variable to the list."""
        # Check if variable name appears to be a constant (ALL_CAPS)
        is_constant = name.isupper() and "_" in name

        self.variables.append(
            ParsedVariable(
                name=name,
                inferred_type=inferred_type,
                value_repr=value_repr,
                line_start=line_start,
                line_end=line_end,
                is_class_var=is_class_var,
                is_constant=is_constant,
                scope=self.current_scope,
            )
        )

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
        elif isinstance(node, ast.BinOp):
            return "expression"
        elif isinstance(node, ast.UnaryOp):
            return "expression"
        elif isinstance(node, ast.Compare):
            return "comparison"
        elif isinstance(node, ast.ListComp):
            return "[comprehension]"
        elif isinstance(node, ast.DictComp):
            return "{comprehension}"
        elif isinstance(node, ast.SetComp):
            return "{comprehension}"
        elif isinstance(node, ast.Lambda):
            return "lambda"
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
        """Recursively build path for attribute nodes (e.g., module.submodule.Class)."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_attribute_path(node.value)}.{node.attr}"
        return str(node)
