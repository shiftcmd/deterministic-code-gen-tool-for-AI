"""
Cypher Generator for Neo4j Knowledge Graph.

This module transforms the extraction output into parameterized Neo4j Cypher
commands, implementing safe query generation with proper escaping.

Key improvements:
- Parameterized queries to prevent injection
- Proper handling of special characters
- Status reporting integration
- Batch command generation for efficiency
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from communication import StatusReporter, NullStatusReporter


logger = logging.getLogger(__name__)


class CypherGenerator:
    """Generates Neo4j Cypher commands from extraction data."""
    
    def __init__(self):
        """Initialize the Cypher generator."""
        self.queries = []
        self.parameters = []
        
    def generate(
        self, 
        extraction_data: Dict[str, Any],
        status_reporter: Optional[StatusReporter] = None
    ) -> str:
        """
        Generate Cypher commands from extraction data.
        
        Args:
            extraction_data: The parsed extraction_output.json data
            status_reporter: Optional status reporter for progress updates
            
        Returns:
            String containing all Cypher commands
        """
        if not status_reporter:
            status_reporter = NullStatusReporter()
            
        # Clear previous state
        self.queries = []
        self.parameters = []
        
        # Extract modules data
        modules = extraction_data.get("modules", {})
        total_modules = len(modules)
        
        if total_modules == 0:
            logger.warning("No modules found in extraction data")
            return ""
            
        # Process each module
        for i, (module_path, module_data) in enumerate(modules.items()):
            status_reporter.report_progress(
                current=i,
                total=total_modules,
                message=f"Processing module: {module_data.get('name', 'unknown')}"
            )
            
            self._process_module(module_path, module_data)
            
        # Generate final output
        status_reporter.report_status(
            phase="transformation",
            status="formatting",
            message="Formatting Cypher commands"
        )
        
        output = self._format_output()
        
        status_reporter.report_status(
            phase="transformation",
            status="formatted",
            message=f"Generated {len(self.queries)} Cypher queries",
            metadata={
                "query_count": len(self.queries),
                "parameter_sets": len(self.parameters)
            }
        )
        
        return output
        
    def _process_module(self, module_path: str, module_data: Dict[str, Any]) -> None:
        """Process a single module and generate its Cypher commands."""
        module_name = module_data.get("name", "")
        
        # Create module node
        self._create_module_node(module_path, module_data)
        
        # Process imports
        for import_data in module_data.get("imports", []):
            self._create_import_relationship(module_path, import_data)
            
        # Process classes
        for class_data in module_data.get("classes", []):
            self._process_class(module_path, class_data)
            
        # Process functions
        for function_data in module_data.get("functions", []):
            self._process_function(module_path, function_data)
            
        # Process variables
        for variable_data in module_data.get("variables", []):
            self._process_variable(module_path, variable_data)
            
    def _create_module_node(self, module_path: str, module_data: Dict[str, Any]) -> None:
        """Create a Module node."""
        query = """
MERGE (m:Module {path: $path})
SET m.name = $name,
    m.line_count = $line_count,
    m.size_bytes = $size_bytes,
    m.last_modified = $last_modified,
    m.docstring = $docstring
"""
        
        params = {
            "path": module_path,
            "name": module_data.get("name", ""),
            "line_count": module_data.get("line_count", 0),
            "size_bytes": module_data.get("size_bytes", 0),
            "last_modified": module_data.get("last_modified", ""),
            "docstring": module_data.get("docstring", "")
        }
        
        self.queries.append(query)
        self.parameters.append(params)
        
    def _create_import_relationship(self, module_path: str, import_data: Dict[str, Any]) -> None:
        """Create an IMPORTS relationship."""
        query = """
MATCH (from:Module {path: $from_path})
MERGE (to:Module {name: $to_module})
MERGE (from)-[r:IMPORTS]->(to)
SET r.name = $import_name,
    r.asname = $asname,
    r.fromname = $fromname,
    r.is_star = $is_star,
    r.line_start = $line_start,
    r.line_end = $line_end
"""
        
        # Determine the imported module name
        to_module = import_data.get("fromname") or import_data.get("name", "")
        
        params = {
            "from_path": module_path,
            "to_module": to_module,
            "import_name": import_data.get("name", ""),
            "asname": import_data.get("asname", ""),
            "fromname": import_data.get("fromname", ""),
            "is_star": import_data.get("is_star", False),
            "line_start": import_data.get("line_start", 0),
            "line_end": import_data.get("line_end", 0)
        }
        
        self.queries.append(query)
        self.parameters.append(params)
        
    def _process_class(self, module_path: str, class_data: Dict[str, Any]) -> None:
        """Process a class and its relationships."""
        class_name = class_data.get("name", "")
        
        # Create class node
        query = """
MATCH (m:Module {path: $module_path})
MERGE (c:Class {name: $name, module_path: $module_path})
MERGE (m)-[:CONTAINS]->(c)
SET c.docstring = $docstring,
    c.line_start = $line_start,
    c.line_end = $line_end,
    c.decorators = $decorators
"""
        
        params = {
            "module_path": module_path,
            "name": class_name,
            "docstring": class_data.get("docstring", ""),
            "line_start": class_data.get("line_start", 0),
            "line_end": class_data.get("line_end", 0),
            "decorators": json.dumps(class_data.get("decorators", []))
        }
        
        self.queries.append(query)
        self.parameters.append(params)
        
        # Create inheritance relationships
        for base_class in class_data.get("bases", []):
            self._create_inheritance_relationship(module_path, class_name, base_class)
            
        # Process methods
        for method_data in class_data.get("methods", []):
            self._process_method(module_path, class_name, method_data)
            
        # Process inner classes
        for inner_class in class_data.get("inner_classes", []):
            self._process_class(module_path, inner_class)
            
    def _create_inheritance_relationship(
        self, 
        module_path: str, 
        child_class: str, 
        parent_class: str
    ) -> None:
        """Create an INHERITS_FROM relationship."""
        query = """
MATCH (child:Class {name: $child_name, module_path: $module_path})
MERGE (parent:Class {name: $parent_name})
MERGE (child)-[:INHERITS_FROM]->(parent)
"""
        
        params = {
            "module_path": module_path,
            "child_name": child_class,
            "parent_name": parent_class
        }
        
        self.queries.append(query)
        self.parameters.append(params)
        
    def _process_method(
        self, 
        module_path: str, 
        class_name: str, 
        method_data: Dict[str, Any]
    ) -> None:
        """Process a method within a class."""
        method_name = method_data.get("name", "")
        
        query = """
MATCH (c:Class {name: $class_name, module_path: $module_path})
MERGE (m:Method {name: $name, class_name: $class_name, module_path: $module_path})
MERGE (c)-[:HAS_METHOD]->(m)
SET m.signature = $signature,
    m.docstring = $docstring,
    m.line_start = $line_start,
    m.line_end = $line_end,
    m.decorators = $decorators,
    m.is_static = $is_static,
    m.is_class_method = $is_class_method,
    m.return_type = $return_type
"""
        
        params = {
            "module_path": module_path,
            "class_name": class_name,
            "name": method_name,
            "signature": method_data.get("signature", ""),
            "docstring": method_data.get("docstring", ""),
            "line_start": method_data.get("line_start", 0),
            "line_end": method_data.get("line_end", 0),
            "decorators": json.dumps(method_data.get("decorators", [])),
            "is_static": method_data.get("is_static", False),
            "is_class_method": method_data.get("is_class_method", False),
            "return_type": method_data.get("return_type", "")
        }
        
        self.queries.append(query)
        self.parameters.append(params)
        
    def _process_function(self, module_path: str, function_data: Dict[str, Any]) -> None:
        """Process a module-level function."""
        function_name = function_data.get("name", "")
        
        query = """
MATCH (m:Module {path: $module_path})
MERGE (f:Function {name: $name, module_path: $module_path})
MERGE (m)-[:CONTAINS]->(f)
SET f.signature = $signature,
    f.docstring = $docstring,
    f.line_start = $line_start,
    f.line_end = $line_end,
    f.decorators = $decorators,
    f.return_type = $return_type
"""
        
        params = {
            "module_path": module_path,
            "name": function_name,
            "signature": function_data.get("signature", ""),
            "docstring": function_data.get("docstring", ""),
            "line_start": function_data.get("line_start", 0),
            "line_end": function_data.get("line_end", 0),
            "decorators": json.dumps(function_data.get("decorators", [])),
            "return_type": function_data.get("return_type", "")
        }
        
        self.queries.append(query)
        self.parameters.append(params)
        
    def _process_variable(self, module_path: str, variable_data: Dict[str, Any]) -> None:
        """Process a variable assignment."""
        variable_name = variable_data.get("name", "")
        
        query = """
MATCH (m:Module {path: $module_path})
MERGE (v:Variable {name: $name, module_path: $module_path})
MERGE (m)-[:CONTAINS]->(v)
SET v.inferred_type = $inferred_type,
    v.value_repr = $value_repr,
    v.line_start = $line_start,
    v.line_end = $line_end,
    v.is_class_var = $is_class_var,
    v.is_constant = $is_constant,
    v.scope = $scope
"""
        
        params = {
            "module_path": module_path,
            "name": variable_name,
            "inferred_type": variable_data.get("inferred_type", ""),
            "value_repr": variable_data.get("value_repr", ""),
            "line_start": variable_data.get("line_start", 0),
            "line_end": variable_data.get("line_end", 0),
            "is_class_var": variable_data.get("is_class_var", False),
            "is_constant": variable_data.get("is_constant", False),
            "scope": variable_data.get("scope", "module")
        }
        
        self.queries.append(query)
        self.parameters.append(params)
        
    def _format_output(self) -> str:
        """Format the queries and parameters for output."""
        output_lines = [
            "// Neo4j Cypher Commands",
            f"// Generated at: {datetime.utcnow().isoformat()}",
            f"// Total queries: {len(self.queries)}",
            "",
            "// IMPORTANT: These are parameterized queries.",
            "// Use with Neo4j driver's session.run(query, parameters) method.",
            "",
        ]
        
        # Add each query with its parameters
        for i, (query, params) in enumerate(zip(self.queries, self.parameters)):
            output_lines.extend([
                f"// Query {i + 1}",
                "// " + "-" * 50,
                query.strip(),
                "// Parameters:",
                json.dumps(params, indent=2),
                "",
            ])
            
        # Add batch execution script
        output_lines.extend([
            "",
            "// Batch Execution Script (for Neo4j Browser or cypher-shell):",
            "// " + "=" * 50,
            "",
        ])
        
        # Generate non-parameterized versions for manual execution
        for query, params in zip(self.queries, self.parameters):
            safe_query = self._create_safe_query(query, params)
            output_lines.append(safe_query + ";")
            output_lines.append("")
            
        return "\n".join(output_lines)
        
    def _create_safe_query(self, query: str, params: Dict[str, Any]) -> str:
        """Create a safe non-parameterized query by properly escaping values."""
        safe_query = query
        
        for param_name, param_value in params.items():
            # Escape string values
            if isinstance(param_value, str):
                # Escape single quotes and backslashes
                escaped_value = param_value.replace("\\", "\\\\").replace("'", "\\'")
                safe_value = f"'{escaped_value}'"
            elif isinstance(param_value, bool):
                safe_value = "true" if param_value else "false"
            elif param_value is None:
                safe_value = "null"
            else:
                safe_value = str(param_value)
                
            # Replace parameter placeholder
            safe_query = safe_query.replace(f"${param_name}", safe_value)
            
        return safe_query