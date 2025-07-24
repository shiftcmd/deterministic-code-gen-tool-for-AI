"""
Serialization module for converting parsed Python objects to JSON.

This module handles the conversion of ParsedModule and related objects
into a JSON-serializable format for the extraction output.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from dataclasses import asdict, is_dataclass

from models import (
    ParsedModule, ParsedClass, ParsedFunction, 
    ParsedVariable, ParsedImport
)
from communication import StatusReporter, NullStatusReporter


class Serializer:
    """Handles serialization of parsed code objects to JSON format."""
    
    def __init__(self):
        """Initialize the serializer."""
        self.status_reporter = None
        
    def serialize_modules(
        self, 
        modules: Dict[str, ParsedModule],
        status_reporter: Optional[StatusReporter] = None
    ) -> Dict[str, Any]:
        """
        Serialize a dictionary of parsed modules to JSON-compatible format.
        
        Args:
            modules: Dictionary mapping file paths to ParsedModule objects
            status_reporter: Optional status reporter for progress updates
            
        Returns:
            JSON-serializable dictionary
        """
        self.status_reporter = status_reporter or NullStatusReporter()
        
        # Report serialization start
        self.status_reporter.report_status(
            phase="extraction",
            status="serializing",
            message=f"Serializing {len(modules)} modules"
        )
        
        # Create the output structure
        output = {
            "metadata": {
                "version": "1.0",
                "generated_at": datetime.utcnow().isoformat(),
                "module_count": len(modules),
                "parser": "python_debug_tool_ast_parser"
            },
            "modules": {}
        }
        
        # Serialize each module
        for i, (path, module) in enumerate(modules.items()):
            self.status_reporter.report_progress(
                current=i,
                total=len(modules),
                message=f"Serializing module: {module.name}"
            )
            
            output["modules"][path] = self._serialize_module(module)
            
        # Add summary statistics
        output["summary"] = self._calculate_summary(output["modules"])
        
        return output
        
    def _serialize_module(self, module: ParsedModule) -> Dict[str, Any]:
        """Serialize a single ParsedModule object."""
        return {
            "name": module.name,
            "path": module.path,
            "line_count": module.line_count,
            "size_bytes": module.size_bytes,
            "last_modified": module.last_modified,
            "docstring": module.docstring,
            "imports": [self._serialize_import(imp) for imp in module.imports],
            "classes": [self._serialize_class(cls) for cls in module.classes],
            "functions": [self._serialize_function(func) for func in module.functions],
            "variables": [self._serialize_variable(var) for var in module.variables],
            "ast_errors": module.ast_errors
        }
        
    def _serialize_import(self, import_obj: ParsedImport) -> Dict[str, Any]:
        """Serialize a ParsedImport object."""
        return {
            "name": import_obj.name,
            "asname": import_obj.asname,
            "fromname": import_obj.fromname,
            "is_star": import_obj.is_star,
            "line_start": import_obj.line_start,
            "line_end": import_obj.line_end
        }
        
    def _serialize_class(self, class_obj: ParsedClass) -> Dict[str, Any]:
        """Serialize a ParsedClass object."""
        return {
            "name": class_obj.name,
            "bases": class_obj.bases,
            "docstring": class_obj.docstring,
            "methods": [self._serialize_function(method) for method in class_obj.methods],
            "attributes": class_obj.attributes,
            "line_start": class_obj.line_start,
            "line_end": class_obj.line_end,
            "decorators": class_obj.decorators,
            "inner_classes": [self._serialize_class(inner) for inner in class_obj.inner_classes]
        }
        
    def _serialize_function(self, func_obj: ParsedFunction) -> Dict[str, Any]:
        """Serialize a ParsedFunction object."""
        return {
            "name": func_obj.name,
            "signature": func_obj.signature,
            "docstring": func_obj.docstring,
            "parameters": func_obj.parameters,
            "return_type": func_obj.return_type,
            "variables": [self._serialize_variable(var) for var in func_obj.variables],
            "nested_functions": [
                self._serialize_function(nested) 
                for nested in func_obj.nested_functions
            ],
            "line_start": func_obj.line_start,
            "line_end": func_obj.line_end,
            "decorators": func_obj.decorators,
            "is_method": func_obj.is_method,
            "is_static": func_obj.is_static,
            "is_class_method": func_obj.is_class_method
        }
        
    def _serialize_variable(self, var_obj: ParsedVariable) -> Dict[str, Any]:
        """Serialize a ParsedVariable object."""
        return {
            "name": var_obj.name,
            "inferred_type": var_obj.inferred_type,
            "value_repr": var_obj.value_repr,
            "line_start": var_obj.line_start,
            "line_end": var_obj.line_end,
            "is_class_var": var_obj.is_class_var,
            "is_constant": var_obj.is_constant,
            "scope": var_obj.scope
        }
        
    def _calculate_summary(self, modules: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary statistics for the serialized modules."""
        total_classes = 0
        total_functions = 0
        total_methods = 0
        total_imports = 0
        total_variables = 0
        total_lines = 0
        
        for module_data in modules.values():
            total_imports += len(module_data.get("imports", []))
            total_classes += len(module_data.get("classes", []))
            total_functions += len(module_data.get("functions", []))
            total_variables += len(module_data.get("variables", []))
            total_lines += module_data.get("line_count", 0)
            
            # Count methods in classes
            for class_data in module_data.get("classes", []):
                total_methods += len(class_data.get("methods", []))
                
        return {
            "total_modules": len(modules),
            "total_classes": total_classes,
            "total_functions": total_functions,
            "total_methods": total_methods,
            "total_imports": total_imports,
            "total_variables": total_variables,
            "total_lines": total_lines
        }


class EnhancedJSONEncoder(json.JSONEncoder):
    """Enhanced JSON encoder that handles additional Python types."""
    
    def default(self, obj):
        """Handle non-standard types."""
        if is_dataclass(obj):
            return asdict(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, "__dict__"):
            return obj.__dict__
        return super().default(obj)