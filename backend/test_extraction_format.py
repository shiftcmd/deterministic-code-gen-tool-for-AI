#!/usr/bin/env python3
"""
Test script to understand the Phase 1 extraction format.
This script parses a simple Python file and shows the data structure that Phase 1 produces.
"""

import ast
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Import the models directly to avoid dependency issues
@dataclass
class ParsedImport:
    """Represents an import statement in Python code."""
    name: str
    asname: Optional[str] = None
    fromname: Optional[str] = None
    line_start: int = 0
    line_end: int = 0
    is_star: bool = False
    symbols: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
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
    value_repr: Optional[str] = None
    line_start: int = 0
    line_end: int = 0
    is_class_var: bool = False
    is_constant: bool = False
    scope: str = "module"

    def to_dict(self) -> Dict[str, Any]:
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
    signature: str
    docstring: Optional[str] = None
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    return_type: Optional[str] = None
    variables: List[ParsedVariable] = field(default_factory=list)
    nested_functions: List["ParsedFunction"] = field(default_factory=list)
    line_start: int = 0
    line_end: int = 0
    decorators: List[str] = field(default_factory=list)
    is_method: bool = False
    is_static: bool = False
    is_class_method: bool = False
    complexity: int = 0
    imports: List[ParsedImport] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
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
    bases: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    methods: List[ParsedFunction] = field(default_factory=list)
    attributes: List[ParsedVariable] = field(default_factory=list)
    line_start: int = 0
    line_end: int = 0
    decorators: List[str] = field(default_factory=list)
    inner_classes: List["ParsedClass"] = field(default_factory=list)
    imported_types: List[str] = field(default_factory=list)
    metaclass: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
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
    name: str
    path: str
    docstring: Optional[str] = None
    imports: List[ParsedImport] = field(default_factory=list)
    classes: List[ParsedClass] = field(default_factory=list)
    functions: List[ParsedFunction] = field(default_factory=list)
    variables: List[ParsedVariable] = field(default_factory=list)
    line_count: int = 0
    size_bytes: int = 0
    ast_errors: List[Dict[str, Any]] = field(default_factory=list)
    last_modified: Optional[str] = None
    md5_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
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

def simple_parse_module(file_path: str) -> ParsedModule:
    """Simple parser to create sample Phase 1 output."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Parse AST
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        return ParsedModule(
            name=Path(file_path).stem,
            path=file_path,
            ast_errors=[{"error_type": "SyntaxError", "message": str(e)}]
        )
    
    # Extract basic information
    imports = []
    functions = []
    classes = []
    variables = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(ParsedImport(
                    name=alias.name,
                    asname=alias.asname,
                    line_start=node.lineno,
                    line_end=node.lineno
                ))
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imports.append(ParsedImport(
                    name=alias.name,
                    asname=alias.asname,
                    fromname=node.module,
                    line_start=node.lineno,
                    line_end=node.lineno
                ))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Get function signature
            args = [arg.arg for arg in node.args.args]
            is_async = isinstance(node, ast.AsyncFunctionDef)
            sig = f"{'async ' if is_async else ''}{node.name}({', '.join(args)})"
            
            # Get return type annotation if present
            return_type = None
            if node.returns:
                if isinstance(node.returns, ast.Name):
                    return_type = node.returns.id
                elif isinstance(node.returns, ast.Subscript):
                    return_type = ast.unparse(node.returns)
                else:
                    return_type = ast.unparse(node.returns)
            
            functions.append(ParsedFunction(
                name=node.name,
                signature=sig,
                docstring=ast.get_docstring(node),
                line_start=node.lineno,
                line_end=node.end_lineno or node.lineno,
                return_type=return_type,
                decorators=[ast.unparse(dec) for dec in node.decorator_list]
            ))
        elif isinstance(node, ast.ClassDef):
            bases = [ast.unparse(base) for base in node.bases]
            classes.append(ParsedClass(
                name=node.name,
                bases=bases,
                docstring=ast.get_docstring(node),
                line_start=node.lineno,
                line_end=node.end_lineno or node.lineno,
                decorators=[ast.unparse(dec) for dec in node.decorator_list]
            ))
    
    return ParsedModule(
        name=Path(file_path).stem,
        path=file_path,
        docstring=ast.get_docstring(tree),
        imports=imports,
        functions=functions,
        classes=classes,
        variables=variables,
        line_count=len(content.splitlines()),
        size_bytes=len(content.encode('utf-8'))
    )

def test_extraction_format():
    """Test the extraction format by parsing a simple health.py file."""
    
    # Use the test_sample_module.py file as our test subject (comprehensive test case)
    test_file = Path(__file__).parent / "test_sample_module.py"
    
    if not test_file.exists():
        print(f"Error: Test file {test_file} does not exist")
        return
    
    print(f"Parsing file: {test_file}")
    print("=" * 60)
    
    # Parse the file
    parsed_module = simple_parse_module(str(test_file))
    
    # Convert to dictionary for JSON serialization (this is Phase 1 output format)
    module_dict = parsed_module.to_dict()
    
    # Pretty print the structure
    print("PHASE 1 OUTPUT FORMAT:")
    print("=" * 60)
    print(json.dumps(module_dict, indent=2, default=str))
    
    # Also save to file for further inspection
    output_file = Path(__file__).parent / "sample_phase1_output.json"
    with open(output_file, "w") as f:
        json.dump(module_dict, f, indent=2, default=str)
    
    print(f"\nSample output saved to: {output_file}")
    
    # Print summary
    print("\nSUMMARY OF EXTRACTED DATA:")
    print("=" * 60)
    print(f"Module name: {parsed_module.name}")
    print(f"Functions: {len(parsed_module.functions)}")
    print(f"Classes: {len(parsed_module.classes)}")
    print(f"Variables: {len(parsed_module.variables)}")
    print(f"Imports: {len(parsed_module.imports)}")
    
    return module_dict

if __name__ == "__main__":
    test_extraction_format()