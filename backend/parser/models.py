"""
Data models for parsed Python code elements.

This module defines the data structures used to represent parsed Python code
elements such as modules, classes, functions, variables, and imports.
All models are designed to be serializable to JSON for downstream processing.

# AI-Intent: Core-Domain
# Intent: These models represent the core domain entities of the parser system
# They encapsulate the essential structure of Python code elements
# Confidence: High
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union


@dataclass
class ParsedImport:
    """Represents an import statement in Python code."""

    name: str  # The module being imported
    asname: Optional[str] = None  # Alias if using 'import x as y'
    fromname: Optional[str] = None  # Module if using 'from x import y'
    line_start: int = 0
    line_end: int = 0
    is_star: bool = False  # True for 'from x import *'
    symbols: List[Dict[str, str]] = field(
        default_factory=list
    )  # For 'from x import y, z'

    def to_dict(self) -> Dict[str, Any]:
        """Convert the import to a dictionary for JSON serialization."""
        return {
            "name": self.name,
            "asname": self.asname,
            "fromname": self.fromname,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "is_star": self.is_star,
            "symbols": self.symbols,
        }


@dataclass
class ParsedVariable:
    """Represents a variable assignment in Python code."""

    name: str
    inferred_type: Optional[str] = None
    value_repr: Optional[str] = None  # String representation of the assigned value
    line_start: int = 0
    line_end: int = 0
    is_class_var: bool = False  # True if class variable, False if instance variable
    is_constant: bool = False  # Determined by naming convention (e.g., ALL_CAPS)
    scope: str = "module"  # 'module', 'class', or 'function'

    def to_dict(self) -> Dict[str, Any]:
        """Convert the variable to a dictionary for JSON serialization."""
        return {
            "name": self.name,
            "inferred_type": self.inferred_type,
            "value_repr": self.value_repr,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "is_class_var": self.is_class_var,
            "is_constant": self.is_constant,
            "scope": self.scope,
        }


@dataclass
class ParsedFunction:
    """Represents a function or method definition in Python code."""

    name: str
    signature: str  # Full function signature
    docstring: Optional[str] = None
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    return_type: Optional[str] = None
    variables: List[ParsedVariable] = field(default_factory=list)
    nested_functions: List["ParsedFunction"] = field(default_factory=list)
    line_start: int = 0
    line_end: int = 0
    decorators: List[str] = field(default_factory=list)
    is_method: bool = False  # True if method of a class
    is_static: bool = False  # True if static method
    is_class_method: bool = False  # True if class method
    complexity: int = 0  # Cyclomatic complexity
    imports: List[ParsedImport] = field(default_factory=list)  # Function-local imports

    def to_dict(self) -> Dict[str, Any]:
        """Convert the function to a dictionary for JSON serialization."""
        return {
            "name": self.name,
            "signature": self.signature,
            "docstring": self.docstring,
            "parameters": self.parameters,
            "return_type": self.return_type,
            "variables": [var.to_dict() for var in self.variables],
            "nested_functions": [func.to_dict() for func in self.nested_functions],
            "line_start": self.line_start,
            "line_end": self.line_end,
            "decorators": self.decorators,
            "is_method": self.is_method,
            "is_static": self.is_static,
            "is_class_method": self.is_class_method,
            "complexity": self.complexity,
            "imports": [imp.to_dict() for imp in self.imports],
        }


@dataclass
class ParsedClass:
    """Represents a class definition in Python code."""

    name: str
    bases: List[str] = field(default_factory=list)  # Base classes
    docstring: Optional[str] = None
    methods: List[ParsedFunction] = field(default_factory=list)
    attributes: List[ParsedVariable] = field(default_factory=list)
    line_start: int = 0
    line_end: int = 0
    decorators: List[str] = field(default_factory=list)
    inner_classes: List["ParsedClass"] = field(default_factory=list)
    imported_types: List[str] = field(default_factory=list)  # Types used in this class
    metaclass: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the class to a dictionary for JSON serialization."""
        return {
            "name": self.name,
            "bases": self.bases,
            "docstring": self.docstring,
            "methods": [method.to_dict() for method in self.methods],
            "attributes": [attr.to_dict() for attr in self.attributes],
            "line_start": self.line_start,
            "line_end": self.line_end,
            "decorators": self.decorators,
            "inner_classes": [cls.to_dict() for cls in self.inner_classes],
            "imported_types": self.imported_types,
            "metaclass": self.metaclass,
        }


@dataclass
class ParsedModule:
    """Represents a Python module file."""

    name: str  # Module name (usually filename without extension)
    path: str  # Absolute file path
    docstring: Optional[str] = None
    imports: List[ParsedImport] = field(default_factory=list)
    classes: List[ParsedClass] = field(default_factory=list)
    functions: List[ParsedFunction] = field(default_factory=list)
    variables: List[ParsedVariable] = field(default_factory=list)
    line_count: int = 0
    size_bytes: int = 0
    ast_errors: List[Dict[str, Any]] = field(default_factory=list)
    last_modified: Optional[str] = None
    md5_hash: Optional[str] = None  # For caching and detecting changes

    def to_dict(self) -> Dict[str, Any]:
        """Convert the parsed module to a dictionary for JSON serialization."""
        # This method is implemented to handle recursive dataclasses
        return {
            "name": self.name,
            "path": self.path,
            "docstring": self.docstring,
            "imports": [imp.to_dict() for imp in self.imports],
            "classes": [cls.to_dict() for cls in self.classes],
            "functions": [func.to_dict() for func in self.functions],
            "variables": [var.to_dict() for var in self.variables],
            "line_count": self.line_count,
            "size_bytes": self.size_bytes,
            "ast_errors": self.ast_errors,
            "last_modified": self.last_modified,
            "md5_hash": self.md5_hash,
        }
