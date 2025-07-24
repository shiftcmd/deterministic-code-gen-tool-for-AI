"""
AST Visitors for Python Debug Tool - Refactored for Production.

This module implements various AST node visitors that extract different
structural elements from Python code, such as classes, functions,
imports, and variables.

Key improvements:
- Uses shared ast_utils to eliminate duplicate code
- Properly links methods to their parent classes
- Integrated with status reporting
"""

import ast
import logging
from typing import Any, Dict, List, Optional, Set

from models import ParsedClass, ParsedFunction, ParsedImport, ParsedVariable
from ast_utils import (
    get_attribute_path,
    extract_annotation,
    extract_value,
    get_decorators,
    get_base_classes,
    get_function_arguments,
    get_docstring,
    is_dunder_method,
    is_private
)

logger = logging.getLogger(__name__)


class ClassVisitor(ast.NodeVisitor):
    """
    AST visitor that extracts class definitions from Python code.
    
    This visitor properly handles nested classes and ensures methods
    are correctly linked to their parent classes.
    """

    def __init__(self, status_reporter=None):
        self.classes: List[ParsedClass] = []
        self.current_class: Optional[ParsedClass] = None
        self.status_reporter = status_reporter
        
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit a class definition node."""
        # Report progress
        if self.status_reporter:
            self.status_reporter.report_status(
                phase="extraction",
                status="parsing_class",
                message=f"Parsing class: {node.name}"
            )
            
        # Extract class information using shared utilities
        class_info = ParsedClass(
            name=node.name,
            bases=get_base_classes(node),
            docstring=get_docstring(node),
            methods=[],
            attributes=[],
            line_start=node.lineno,
            line_end=getattr(node, "end_lineno", node.lineno),
            decorators=get_decorators(node),
            inner_classes=[],
        )
        
        # Handle nested class vs. top-level class
        parent_class = self.current_class
        self.current_class = class_info
        
        # Visit children - this will populate methods and inner classes
        self.generic_visit(node)
        
        # Restore parent context and add to appropriate list
        self.current_class = parent_class
        
        if parent_class:
            parent_class.inner_classes.append(class_info)
        else:
            self.classes.append(class_info)
            
            
class FunctionVisitor(ast.NodeVisitor):
    """
    AST visitor that extracts function and method definitions from Python code.
    
    This visitor properly handles nested functions and correctly adds methods
    to their parent classes.
    """
    
    def __init__(self, status_reporter=None):
        self.functions: List[ParsedFunction] = []
        self.current_class: Optional[ParsedClass] = None
        self.current_function: Optional[ParsedFunction] = None
        self.status_reporter = status_reporter
        
    def set_current_class(self, class_obj: Optional[ParsedClass]) -> None:
        """Set the current class context for method extraction."""
        self.current_class = class_obj
        
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit a function definition node."""
        # Report progress
        if self.status_reporter:
            self.status_reporter.report_status(
                phase="extraction",
                status="parsing_function",
                message=f"Parsing function: {node.name}"
            )
            
        # Extract function information
        parameters = get_function_arguments(node)
        return_type = extract_annotation(node) if node.returns else None
        decorators = get_decorators(node)
        
        # Check for special decorators
        is_static = "staticmethod" in decorators
        is_class_method = "classmethod" in decorators
        
        # Build signature
        signature = self._build_signature(node.name, parameters, return_type)
        
        # Create parsed function
        function_info = ParsedFunction(
            name=node.name,
            signature=signature,
            docstring=get_docstring(node),
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
        
        # Handle nested function vs. top-level function/method
        parent_function = self.current_function
        self.current_function = function_info
        
        # Visit children to extract nested functions and variables
        self.generic_visit(node)
        
        # Restore parent context
        self.current_function = parent_function
        
        # Add to appropriate container
        if parent_function:
            # This is a nested function
            parent_function.nested_functions.append(function_info)
        elif self.current_class:
            # This is a method - add it to the current class
            self.current_class.methods.append(function_info)
        else:
            # This is a top-level function
            self.functions.append(function_info)
            
    def _build_signature(
        self, 
        name: str, 
        parameters: List[dict], 
        return_type: Optional[str]
    ) -> str:
        """Build a function signature string."""
        param_strs = []
        for param in parameters:
            param_str = param["name"]
            if param.get("type"):
                param_str += f": {param['type']}"
            if param.get("default") is not None:
                param_str += f" = {param['default']}"
            param_strs.append(param_str)
            
        signature = f"def {name}({', '.join(param_strs)})"
        if return_type:
            signature += f" -> {return_type}"
            
        return signature


class ImportVisitor(ast.NodeVisitor):
    """
    AST visitor that extracts import statements from Python code.
    """

    def __init__(self, status_reporter=None):
        self.imports: List[ParsedImport] = []
        self.status_reporter = status_reporter

    def visit_Import(self, node: ast.Import) -> None:
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

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit an import-from node (e.g., 'from os import path')."""
        for name in node.names:
            if name.name == "*":
                # Handle star imports
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

    def __init__(self, status_reporter=None):
        self.variables: List[ParsedVariable] = []
        self.current_scope = "module"  # 'module', 'class', or 'function'
        self.status_reporter = status_reporter

    def visit_Assign(self, node: ast.Assign) -> None:
        """Visit an assignment node."""
        # Extract the assigned value
        value_repr = extract_value(node.value)

        # Handle multiple assignment targets
        for target in node.targets:
            if isinstance(target, ast.Name):
                # Simple variable assignment
                self._add_variable(
                    name=target.id,
                    value_repr=value_repr,
                    line_start=node.lineno,
                    line_end=getattr(node, "end_lineno", node.lineno),
                )
            elif isinstance(target, (ast.Tuple, ast.List)):
                # Multiple assignment (a, b = 1, 2)
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        self._add_variable(
                            name=elt.id,
                            value_repr="[part of multiple assignment]",
                            line_start=node.lineno,
                            line_end=getattr(node, "end_lineno", node.lineno),
                        )
            elif isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                # Attribute assignment (self.x = 1 or Class.x = 1)
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

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Visit an annotated assignment (x: int = 1)."""
        if isinstance(node.target, ast.Name):
            # Extract type annotation
            type_annotation = extract_annotation(node)

            # Extract value if available
            value_repr = extract_value(node.value) if node.value else None

            self._add_variable(
                name=node.target.id,
                value_repr=value_repr,
                line_start=node.lineno,
                line_end=getattr(node, "end_lineno", node.lineno),
                inferred_type=type_annotation,
            )

        # Continue visiting children
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Update scope when entering a class definition."""
        old_scope = self.current_scope
        self.current_scope = "class"
        self.generic_visit(node)
        self.current_scope = old_scope

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Update scope when entering a function definition."""
        old_scope = self.current_scope
        self.current_scope = "function"
        self.generic_visit(node)
        self.current_scope = old_scope

    def _add_variable(
        self,
        name: str,
        value_repr: str,
        line_start: int,
        line_end: int,
        inferred_type: Optional[str] = None,
        is_class_var: bool = False,
    ) -> None:
        """Add a parsed variable to the list."""
        # Check if variable name appears to be a constant
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


class CombinedVisitor(ast.NodeVisitor):
    """
    A combined visitor that properly handles the interaction between
    class and function visitors to ensure methods are linked to classes.
    """
    
    def __init__(self, status_reporter=None):
        self.class_visitor = ClassVisitor(status_reporter)
        self.function_visitor = FunctionVisitor(status_reporter)
        self.import_visitor = ImportVisitor(status_reporter)
        self.variable_visitor = VariableVisitor(status_reporter)
        self.status_reporter = status_reporter
        
    def visit(self, node: ast.AST) -> Dict[str, List]:
        """
        Visit the AST and extract all structural elements.
        
        Returns:
            Dictionary containing classes, functions, imports, and variables
        """
        # First pass: Extract classes and imports
        self.class_visitor.visit(node)
        self.import_visitor.visit(node)
        
        # Second pass: Extract functions with class context
        self._extract_functions_with_context(node)
        
        # Third pass: Extract variables
        self.variable_visitor.visit(node)
        
        return {
            "classes": self.class_visitor.classes,
            "functions": self.function_visitor.functions,
            "imports": self.import_visitor.imports,
            "variables": self.variable_visitor.variables
        }
        
    def _extract_functions_with_context(self, node: ast.AST) -> None:
        """Extract functions while maintaining class context."""
        for child in ast.walk(node):
            if isinstance(child, ast.ClassDef):
                # Find the corresponding ParsedClass
                parsed_class = self._find_parsed_class(child.name)
                if parsed_class:
                    # Set class context and visit methods
                    self.function_visitor.set_current_class(parsed_class)
                    for item in child.body:
                        if isinstance(item, ast.FunctionDef):
                            self.function_visitor.visit(item)
                    self.function_visitor.set_current_class(None)
            elif isinstance(child, ast.FunctionDef):
                # Top-level function (not in a class)
                if not self._is_method(child):
                    self.function_visitor.visit(child)
                    
    def _find_parsed_class(self, name: str) -> Optional[ParsedClass]:
        """Find a parsed class by name."""
        for cls in self.class_visitor.classes:
            if cls.name == name:
                return cls
            # Check inner classes
            found = self._find_inner_class(cls, name)
            if found:
                return found
        return None
        
    def _find_inner_class(self, parent: ParsedClass, name: str) -> Optional[ParsedClass]:
        """Recursively find an inner class by name."""
        for inner in parent.inner_classes:
            if inner.name == name:
                return inner
            found = self._find_inner_class(inner, name)
            if found:
                return found
        return None
        
    def _is_method(self, node: ast.FunctionDef) -> bool:
        """Check if a function node is inside a class."""
        for parent in ast.walk(node):
            if isinstance(parent, ast.ClassDef):
                return True
        return False