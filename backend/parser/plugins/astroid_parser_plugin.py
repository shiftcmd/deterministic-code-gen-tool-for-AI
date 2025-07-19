"""
Astroid parser plugin for Python Debug Tool.

This module implements a parser plugin using the Astroid library,
providing enhanced type inference and object-oriented analysis.

# AI-Intent: Core-Domain
# Intent: Provides enhanced parsing capabilities using Astroid
# Confidence: High
"""

import logging
import os
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


class AstroidPlugin(ParserPlugin):
    """Parser plugin using the Astroid library."""

    name = "astroid"
    description = (
        "Enhanced parser using Astroid for better type inference and OOP analysis"
    )
    version = "1.0.0"
    supported_types = {"module", "class", "function", "variable"}
    requires_dependencies = ["astroid"]
    default_options = {
        "infer_types": True,
        "extract_docstrings": True,
        "analyze_inheritance": True,
        "track_method_calls": False,
        "detect_design_patterns": False,
    }

    def parse_module(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Parse a Python module file using Astroid.

        Args:
            file_path: Path to the Python file
            content: Content of the file

        Returns:
            Dictionary with parsed module information
        """
        try:
            import astroid
            from astroid import MANAGER

            # Parse the module with astroid
            module = MANAGER.ast_from_file(file_path)

            # Extract basic module information
            result = {
                "imports": self._extract_imports(module),
                "classes": [],
                "functions": [],
                "variables": [],
                "docstring": module.doc or "",
                "ast_type": "module",
            }

            # Extract classes, functions, and variables
            for node in module.body:
                if isinstance(node, astroid.ClassDef):
                    result["classes"].append(self.parse_class(node, {"module": module}))
                elif isinstance(node, astroid.FunctionDef):
                    result["functions"].append(
                        self.parse_function(node, {"module": module})
                    )
                elif isinstance(node, astroid.Assign):
                    result["variables"].extend(
                        self.parse_variable(node, {"scope": "module", "module": module})
                    )
                elif isinstance(node, astroid.AnnAssign):
                    result["variables"].extend(
                        self.parse_variable(node, {"scope": "module", "module": module})
                    )

            return result

        except ImportError:
            logger.error("Astroid not installed. Install with 'pip install astroid'")
            raise
        except Exception as e:
            logger.error(f"Error parsing {file_path} with Astroid: {e}")
            raise

    def parse_class(self, node: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a Python class definition using Astroid.

        Args:
            node: Astroid node representing the class
            context: Parsing context

        Returns:
            Dictionary with parsed class information
        """
        import astroid

        docstring = node.doc or "" if self.options["extract_docstrings"] else ""

        # Extract base classes
        bases = []
        for base in node.bases:
            if isinstance(base, astroid.Name):
                bases.append(base.name)
            elif isinstance(base, astroid.Attribute):
                # Handle module.Class format
                expr = base.expr
                if isinstance(expr, astroid.Name):
                    bases.append(f"{expr.name}.{base.attrname}")
                else:
                    bases.append(base.attrname)
            else:
                # For more complex expressions, just note that there's a base
                bases.append("<complex_base>")

        # Extract methods and class variables
        methods = []
        class_vars = []

        for child_node in node.get_children():
            if isinstance(child_node, astroid.FunctionDef):
                methods.append(
                    self.parse_function(
                        child_node,
                        {
                            "in_class": True,
                            "class_name": node.name,
                            "module": context.get("module"),
                        },
                    )
                )
            elif isinstance(child_node, astroid.Assign):
                class_vars.extend(
                    self.parse_variable(
                        child_node,
                        {
                            "scope": "class",
                            "class_name": node.name,
                            "module": context.get("module"),
                        },
                    )
                )
            elif isinstance(child_node, astroid.AnnAssign):
                class_vars.extend(
                    self.parse_variable(
                        child_node,
                        {
                            "scope": "class",
                            "class_name": node.name,
                            "module": context.get("module"),
                        },
                    )
                )

        # Extract architectural hints from docstring or annotations if configured
        architectural_hints = {}
        if self.options["detect_design_patterns"]:
            # Look for AI-Intent tags or architectural patterns
            if docstring:
                for line in docstring.split("\n"):
                    line = line.strip()
                    if line.startswith("# AI-Intent:"):
                        architectural_hints["intent_tag"] = line.replace(
                            "# AI-Intent:", ""
                        ).strip()
                    elif line.startswith("# Intent:"):
                        architectural_hints["intent_description"] = line.replace(
                            "# Intent:", ""
                        ).strip()
                    elif line.startswith("# Confidence:"):
                        architectural_hints["confidence"] = line.replace(
                            "# Confidence:", ""
                        ).strip()

        # Calculate complexity metrics
        complexity = 1
        if methods:
            # Simple complexity based on number of methods, inheritance, etc.
            complexity = min(
                10, 1 + len(methods) // 3 + len(bases) + len(class_vars) // 5
            )

        result = {
            "name": node.name,
            "docstring": docstring,
            "bases": bases,
            "methods": [m["name"] for m in methods],
            "method_details": methods,
            "variables": class_vars,
            "line_start": node.lineno,
            "line_end": node.tolineno,
            "decorators": [d.name for d in node.decorators.nodes]
            if node.decorators
            else [],
            "complexity": complexity,
            "ast_type": "class",
        }

        # Add architectural information if available
        if architectural_hints:
            result["architectural_hints"] = architectural_hints

        return result

    def parse_function(self, node: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a Python function definition using Astroid.

        Args:
            node: Astroid node representing the function
            context: Parsing context

        Returns:
            Dictionary with parsed function information
        """
        import astroid

        docstring = node.doc or "" if self.options["extract_docstrings"] else ""

        # Extract parameters
        parameters = []

        # Process all argument types
        for arg in node.args.args:
            param = {
                "name": arg.name,
                "annotation": None,
                "has_default": arg in node.args.defaults,
                "default_value": None,
            }

            # Try to extract type annotation
            if arg.annotation and self.options["infer_types"]:
                if isinstance(arg.annotation, astroid.Name):
                    param["annotation"] = arg.annotation.name
                elif hasattr(arg.annotation, "as_string"):
                    param["annotation"] = arg.annotation.as_string()
                else:
                    param["annotation"] = "complex"

            parameters.append(param)

        # Handle *args
        if node.args.vararg:
            parameters.append(
                {
                    "name": f"*{node.args.vararg}",
                    "annotation": None,
                    "has_default": False,
                    "default_value": None,
                }
            )

        # Handle **kwargs
        if node.args.kwarg:
            parameters.append(
                {
                    "name": f"**{node.args.kwarg}",
                    "annotation": None,
                    "has_default": False,
                    "default_value": None,
                }
            )

        # Extract return type annotation
        return_annotation = None
        if node.returns and self.options["infer_types"]:
            if isinstance(node.returns, astroid.Name):
                return_annotation = node.returns.name
            elif hasattr(node.returns, "as_string"):
                return_annotation = node.returns.as_string()
            else:
                return_annotation = "complex"

        is_in_class = context.get("in_class", False)

        # Get decorators
        decorators = []
        if node.decorators:
            for decorator in node.decorators.nodes:
                if isinstance(decorator, astroid.Name):
                    decorators.append(decorator.name)
                elif isinstance(decorator, astroid.Call) and isinstance(
                    decorator.func, astroid.Name
                ):
                    decorators.append(decorator.func.name)

        # Calculate cyclomatic complexity
        complexity = 1
        if self.options.get("compute_complexity", False):
            complexity = self._calculate_complexity(node)

        return {
            "name": node.name,
            "docstring": docstring,
            "parameters": parameters,
            "return_annotation": return_annotation,
            "line_start": node.lineno,
            "line_end": node.tolineno,
            "decorators": decorators,
            "is_method": is_in_class,
            "is_static": "staticmethod" in decorators,
            "is_class": "classmethod" in decorators,
            "class_name": context.get("class_name") if is_in_class else None,
            "complexity": complexity,
            "ast_type": "function",
        }

    def parse_variable(
        self, node: Union[Any, Any], context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Parse a Python variable assignment using Astroid.

        Args:
            node: Astroid node representing the variable assignment
            context: Parsing context

        Returns:
            List of dictionaries with parsed variable information
        """
        import astroid

        variables = []

        if isinstance(node, astroid.Assign):
            for target in node.targets:
                if isinstance(target, astroid.AssignName):
                    # Try to infer the type
                    inferred_type = "unknown"
                    if self.options["infer_types"]:
                        try:
                            inferences = list(node.value.infer())
                            if inferences and hasattr(inferences[0], "pytype"):
                                inferred_type = (
                                    inferences[0].pytype().replace("builtins.", "")
                                )
                            elif inferences and hasattr(inferences[0], "name"):
                                inferred_type = inferences[0].name
                        except Exception:
                            # If type inference fails, try basic type detection
                            if isinstance(node.value, astroid.Const):
                                inferred_type = type(node.value.value).__name__
                            elif isinstance(node.value, astroid.Dict):
                                inferred_type = "dict"
                            elif isinstance(node.value, astroid.List):
                                inferred_type = "list"
                            elif isinstance(node.value, astroid.Tuple):
                                inferred_type = "tuple"
                            elif isinstance(node.value, astroid.Set):
                                inferred_type = "set"

                    variables.append(
                        {
                            "name": target.name,
                            "line_start": node.lineno,
                            "line_end": node.tolineno,
                            "inferred_type": inferred_type,
                            "is_constant": target.name.isupper(),
                            "scope": context.get("scope", "module"),
                            "class_name": context.get("class_name"),
                            "ast_type": "variable",
                        }
                    )

        elif isinstance(node, astroid.AnnAssign):
            if isinstance(node.target, astroid.Name):
                # Get explicit annotation
                annotation = None
                if node.annotation and self.options["infer_types"]:
                    if isinstance(node.annotation, astroid.Name):
                        annotation = node.annotation.name
                    elif hasattr(node.annotation, "as_string"):
                        annotation = node.annotation.as_string()

                # Try to infer the type from value if no annotation
                inferred_type = annotation or "unknown"
                if not annotation and self.options["infer_types"] and node.value:
                    try:
                        inferences = list(node.value.infer())
                        if inferences and hasattr(inferences[0], "pytype"):
                            inferred_type = (
                                inferences[0].pytype().replace("builtins.", "")
                            )
                        elif inferences and hasattr(inferences[0], "name"):
                            inferred_type = inferences[0].name
                    except Exception:
                        pass

                variables.append(
                    {
                        "name": node.target.name,
                        "line_start": node.lineno,
                        "line_end": node.tolineno,
                        "inferred_type": inferred_type,
                        "is_constant": node.target.name.isupper(),
                        "scope": context.get("scope", "module"),
                        "class_name": context.get("class_name"),
                        "ast_type": "variable",
                    }
                )

        return variables

    def _extract_imports(self, module) -> List[Dict[str, Any]]:
        """Extract imports using astroid."""
        import astroid

        imports = []

        for node in module.body:
            if isinstance(node, astroid.Import):
                for name, alias in node.names:
                    imports.append(
                        {
                            "name": name,
                            "asname": alias,
                            "line_start": node.lineno,
                            "line_end": node.lineno,
                            "type": "import",
                        }
                    )

            elif isinstance(node, astroid.ImportFrom):
                for name, alias in node.names:
                    if name == "*":
                        imports.append(
                            {
                                "name": "*",
                                "fromname": node.modname,
                                "line_start": node.lineno,
                                "line_end": node.lineno,
                                "is_star": True,
                                "type": "importfrom",
                            }
                        )
                    else:
                        imports.append(
                            {
                                "name": name,
                                "asname": alias,
                                "fromname": node.modname,
                                "line_start": node.lineno,
                                "line_end": node.lineno,
                                "type": "importfrom",
                            }
                        )

        return imports

    def _calculate_complexity(self, node) -> int:
        """Calculate cyclomatic complexity of a function."""
        import astroid

        complexity = 1  # Base complexity

        class ComplexityVisitor(astroid.NodeVisitor):
            def __init__(self):
                self.complexity = 0

            def visit_if(self, node):
                self.complexity += 1
                self.generic_visit(node)

            def visit_ifexp(self, node):
                self.complexity += 1
                self.generic_visit(node)

            def visit_for(self, node):
                self.complexity += 1
                self.generic_visit(node)

            def visit_while(self, node):
                self.complexity += 1
                self.generic_visit(node)

            def visit_tryexcept(self, node):
                self.complexity += len(node.handlers)
                self.generic_visit(node)

            def visit_with(self, node):
                self.complexity += 1
                self.generic_visit(node)

            def visit_assert(self, node):
                self.complexity += 1
                self.generic_visit(node)

            def visit_comprehension(self, node):
                self.complexity += 1
                self.generic_visit(node)

            def visit_and(self, node):
                self.complexity += len(node.values) - 1
                self.generic_visit(node)

            def visit_or(self, node):
                self.complexity += len(node.values) - 1
                self.generic_visit(node)

        visitor = ComplexityVisitor()
        node.accept(visitor)

        return complexity + visitor.complexity


# Register the plugin
register_plugin(AstroidPlugin)
