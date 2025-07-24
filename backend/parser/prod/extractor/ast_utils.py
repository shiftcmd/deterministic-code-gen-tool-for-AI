"""
Shared AST utilities to eliminate duplicate code across parsers and visitors.

This module consolidates common AST manipulation and extraction functions
that are used by multiple parser components.
"""

import ast
from typing import Any, List, Optional, Union


def get_attribute_path(node: Union[ast.Attribute, ast.Name]) -> str:
    """
    Extract the full attribute path from an AST node.
    
    Args:
        node: AST node (Attribute or Name)
        
    Returns:
        Full dotted path as string (e.g., "module.class.attribute")
    """
    parts = []
    current = node
    
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
        
    if isinstance(current, ast.Name):
        parts.append(current.id)
        
    return '.'.join(reversed(parts))


def extract_annotation(node: Union[ast.arg, ast.AnnAssign, ast.FunctionDef]) -> Optional[str]:
    """
    Extract type annotation from various AST nodes.
    
    Args:
        node: AST node that may have an annotation
        
    Returns:
        String representation of the annotation, or None
    """
    annotation = None
    
    if isinstance(node, ast.arg):
        annotation = node.annotation
    elif isinstance(node, ast.AnnAssign):
        annotation = node.annotation
    elif isinstance(node, ast.FunctionDef) and node.returns:
        annotation = node.returns
    else:
        return None
        
    if annotation:
        return ast.unparse(annotation)
    return None


def extract_value(node: ast.AST) -> Any:
    """
    Extract the actual value from various AST node types.
    
    Args:
        node: AST node containing a value
        
    Returns:
        The extracted value in appropriate Python type
    """
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.Str):  # Python < 3.8 compatibility
        return node.s
    elif isinstance(node, ast.Num):  # Python < 3.8 compatibility
        return node.n
    elif isinstance(node, ast.NameConstant):  # Python < 3.8 compatibility
        return node.value
    elif isinstance(node, ast.List):
        return [extract_value(elt) for elt in node.elts]
    elif isinstance(node, ast.Dict):
        return {
            extract_value(k) if k else None: extract_value(v)
            for k, v in zip(node.keys, node.values)
        }
    elif isinstance(node, ast.Tuple):
        return tuple(extract_value(elt) for elt in node.elts)
    elif isinstance(node, ast.Set):
        return {extract_value(elt) for elt in node.elts}
    elif isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return get_attribute_path(node)
    else:
        # For complex expressions, return the unparsed string
        try:
            return ast.unparse(node)
        except:
            return repr(node)


def get_decorators(node: Union[ast.FunctionDef, ast.ClassDef]) -> List[str]:
    """
    Extract decorator names from a function or class definition.
    
    Args:
        node: AST node for a function or class
        
    Returns:
        List of decorator names/expressions
    """
    decorators = []
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name):
            decorators.append(decorator.id)
        elif isinstance(decorator, ast.Attribute):
            decorators.append(get_attribute_path(decorator))
        elif isinstance(decorator, ast.Call):
            # Handle decorators with arguments
            if isinstance(decorator.func, ast.Name):
                decorators.append(decorator.func.id)
            elif isinstance(decorator.func, ast.Attribute):
                decorators.append(get_attribute_path(decorator.func))
        else:
            # For complex decorators, use unparse
            try:
                decorators.append(ast.unparse(decorator))
            except:
                decorators.append(repr(decorator))
                
    return decorators


def get_base_classes(node: ast.ClassDef) -> List[str]:
    """
    Extract base class names from a class definition.
    
    Args:
        node: AST ClassDef node
        
    Returns:
        List of base class names
    """
    bases = []
    for base in node.bases:
        if isinstance(base, ast.Name):
            bases.append(base.id)
        elif isinstance(base, ast.Attribute):
            bases.append(get_attribute_path(base))
        else:
            # For complex base expressions
            try:
                bases.append(ast.unparse(base))
            except:
                bases.append(repr(base))
                
    return bases


def get_function_arguments(node: ast.FunctionDef) -> List[dict]:
    """
    Extract detailed argument information from a function definition.
    
    Args:
        node: AST FunctionDef node
        
    Returns:
        List of argument dictionaries with name, type, and default value
    """
    args = []
    arguments = node.args
    
    # Process positional arguments
    defaults_start = len(arguments.args) - len(arguments.defaults)
    for i, arg in enumerate(arguments.args):
        arg_info = {
            "name": arg.arg,
            "type": extract_annotation(arg),
            "default": None
        }
        
        # Check if this argument has a default value
        if i >= defaults_start:
            default_index = i - defaults_start
            if default_index < len(arguments.defaults):
                arg_info["default"] = extract_value(arguments.defaults[default_index])
                
        args.append(arg_info)
        
    # Process varargs (*args)
    if arguments.vararg:
        args.append({
            "name": f"*{arguments.vararg.arg}",
            "type": extract_annotation(arguments.vararg),
            "default": None
        })
        
    # Process keyword-only arguments
    for i, arg in enumerate(arguments.kwonlyargs):
        arg_info = {
            "name": arg.arg,
            "type": extract_annotation(arg),
            "default": None
        }
        
        if i < len(arguments.kw_defaults) and arguments.kw_defaults[i]:
            arg_info["default"] = extract_value(arguments.kw_defaults[i])
            
        args.append(arg_info)
        
    # Process kwargs (**kwargs)
    if arguments.kwarg:
        args.append({
            "name": f"**{arguments.kwarg.arg}",
            "type": extract_annotation(arguments.kwarg),
            "default": None
        })
        
    return args


def is_dunder_method(name: str) -> bool:
    """Check if a method name is a dunder (double underscore) method."""
    return name.startswith("__") and name.endswith("__")


def is_private(name: str) -> bool:
    """Check if a name indicates a private member (starts with underscore)."""
    return name.startswith("_") and not is_dunder_method(name)


def get_docstring(node: Union[ast.FunctionDef, ast.ClassDef, ast.Module]) -> Optional[str]:
    """
    Extract docstring from a function, class, or module.
    
    Args:
        node: AST node that may have a docstring
        
    Returns:
        The docstring text, or None if not present
    """
    if not isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
        return None
        
    # Check if first statement is a string
    if node.body and isinstance(node.body[0], ast.Expr):
        if isinstance(node.body[0].value, (ast.Str, ast.Constant)):
            return extract_value(node.body[0].value)
            
    return None