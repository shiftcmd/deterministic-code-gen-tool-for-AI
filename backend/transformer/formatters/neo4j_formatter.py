"""
Neo4j Cypher formatter for transformation output.

Converts TupleSet objects into parameterized Cypher commands
ready for execution in Neo4j, with proper escaping and batch optimization.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Set

from ..models.tuples import TupleSet, Neo4jNodeTuple, Neo4jRelationshipTuple

logger = logging.getLogger(__name__)


class Neo4jFormatter:
    """
    Formats TupleSet objects into Neo4j Cypher commands.
    
    Generates both parameterized queries for programmatic use
    and safe literal queries for manual execution.
    """
    
    def __init__(self):
        """Initialize the Neo4j formatter."""
        self.queries: List[str] = []
        self.parameters: List[Dict[str, Any]] = []
        
    def format(self, tuple_set: TupleSet) -> str:
        """
        Format a TupleSet into Cypher commands.
        
        Args:
            tuple_set: TupleSet containing nodes and relationships
            
        Returns:
            String containing formatted Cypher commands
        """
        self.queries.clear()
        self.parameters.clear()
        
        if tuple_set.size == 0:
            logger.warning("Empty tuple set provided for formatting")
            return self._generate_empty_output()
        
        # Generate node creation queries
        for node in tuple_set.nodes:
            self._format_node(node)
        
        # Generate relationship creation queries
        for relationship in tuple_set.relationships:
            self._format_relationship(relationship)
        
        # Generate formatted output
        return self._generate_output(tuple_set.metadata)
    
    def _format_node(self, node: Neo4jNodeTuple) -> None:
        """Format a single node tuple into Cypher."""
        # Create merge properties clause
        merge_props = node.merge_properties or {"unique_key"}
        merge_conditions = []
        
        for prop in merge_props:
            if prop in node.properties:
                merge_conditions.append(f"{prop}: ${prop}")
        
        if not merge_conditions:
            # Fallback to unique_key if no merge properties found
            merge_conditions = ["unique_key: $unique_key"]
        
        merge_clause = ", ".join(merge_conditions)
        
        # Build SET clause for all properties
        set_clauses = []
        for prop, value in node.properties.items():
            set_clauses.append(f"n.{prop} = ${prop}")
        
        set_clause = ", ".join(set_clauses) if set_clauses else ""
        
        # Generate query
        query = f"""
MERGE (n:{node.label} {{{merge_clause}}})
"""
        if set_clause:
            query += f"SET {set_clause}\n"
        
        # Prepare parameters
        params = {
            "unique_key": node.unique_key,
            **node.properties
        }
        
        self.queries.append(query.strip())
        self.parameters.append(params)
    
    def _format_relationship(self, relationship: Neo4jRelationshipTuple) -> None:
        """Format a single relationship tuple into Cypher."""
        # Build match clauses for source and target nodes
        source_match = f"(source"
        target_match = f"(target"
        
        if relationship.source_label:
            source_match += f":{relationship.source_label}"
        if relationship.target_label:
            target_match += f":{relationship.target_label}"
        
        source_match += " {unique_key: $source_key})"
        target_match += " {unique_key: $target_key})"
        
        # Build relationship properties
        rel_props = ""
        if relationship.properties:
            prop_assignments = []
            for prop, value in relationship.properties.items():
                prop_assignments.append(f"{prop}: ${prop}")
            rel_props = f" {{{', '.join(prop_assignments)}}}"
        
        # Generate query
        query = f"""
MATCH {source_match}
MATCH {target_match}
MERGE (source)-[r:{relationship.relationship_type}{rel_props}]->(target)
"""
        
        # Prepare parameters
        params = {
            "source_key": relationship.source_key,
            "target_key": relationship.target_key,
            **relationship.properties
        }
        
        self.queries.append(query.strip())
        self.parameters.append(params)
    
    def _generate_output(self, metadata: Dict[str, Any]) -> str:
        """Generate the complete formatted output."""
        lines = [
            "// Neo4j Cypher Commands - Transformation Output",
            f"// Generated at: {datetime.utcnow().isoformat()}",
            f"// Job ID: {metadata.get('job_id', 'unknown')}",
            f"// Total queries: {len(self.queries)}",
            "",
            "// IMPORTANT: These are parameterized queries.",
            "// Use with Neo4j driver's session.run(query, parameters) method.",
            "// For manual execution, see the batch script section below.",
            "",
            "// Metadata:",
            f"// {json.dumps(metadata, indent=2)}",
            "",
            "// === PARAMETERIZED QUERIES ===",
            ""
        ]
        
        # Add parameterized queries
        for i, (query, params) in enumerate(zip(self.queries, self.parameters)):
            lines.extend([
                f"// Query {i + 1}",
                "// " + "-" * 50,
                query,
                "// Parameters:",
                json.dumps(params, indent=2, default=str),
                ""
            ])
        
        # Add batch execution section
        lines.extend([
            "",
            "// === BATCH EXECUTION SCRIPT ===",
            "// For Neo4j Browser or cypher-shell",
            "// " + "=" * 50,
            ""
        ])
        
        # Generate safe literal queries
        for i, (query, params) in enumerate(zip(self.queries, self.parameters)):
            safe_query = self._create_safe_literal_query(query, params)
            lines.extend([
                f"// Batch Query {i + 1}",
                safe_query + ";",
                ""
            ])
        
        # Add execution statistics
        lines.extend([
            "",
            "// === EXECUTION STATISTICS ===",
            f"// Total nodes: {self._count_node_queries()}",
            f"// Total relationships: {self._count_relationship_queries()}",
            f"// Total queries: {len(self.queries)}",
            ""
        ])
        
        return "\n".join(lines)
    
    def _create_safe_literal_query(self, query: str, params: Dict[str, Any]) -> str:
        """Create a safe literal query by properly escaping parameter values."""
        safe_query = query
        
        for param_name, param_value in params.items():
            placeholder = f"${param_name}"
            
            if isinstance(param_value, str):
                # Escape single quotes and backslashes
                escaped_value = param_value.replace("\\", "\\\\").replace("'", "\\'")
                safe_value = f"'{escaped_value}'"
            elif isinstance(param_value, bool):
                safe_value = "true" if param_value else "false"
            elif param_value is None:
                safe_value = "null"
            elif isinstance(param_value, (list, dict)):
                # Convert complex types to JSON strings
                json_str = json.dumps(param_value).replace("'", "\\'")
                safe_value = f"'{json_str}'"
            else:
                safe_value = str(param_value)
            
            # Replace parameter placeholder
            safe_query = safe_query.replace(placeholder, safe_value)
        
        return safe_query
    
    def _count_node_queries(self) -> int:
        """Count the number of node creation queries."""
        return sum(1 for query in self.queries if "MERGE (n:" in query)
    
    def _count_relationship_queries(self) -> int:
        """Count the number of relationship creation queries."""
        return sum(1 for query in self.queries if "MERGE (source)-[r:" in query)
    
    def _generate_empty_output(self) -> str:
        """Generate output for empty tuple set."""
        return f"""
// Neo4j Cypher Commands - Transformation Output
// Generated at: {datetime.utcnow().isoformat()}
// Status: No data to transform

// No tuples were provided for transformation.
// This could indicate:
// 1. Empty extraction data
// 2. All modules filtered out during processing
// 3. Processing errors that prevented tuple generation

// Please check the transformation logs for more details.
"""


# Utility function for quick formatting
def format_tuples_to_cypher(tuple_set: TupleSet) -> str:
    """
    Quick utility to format a TupleSet to Cypher.
    
    Args:
        tuple_set: TupleSet to format
        
    Returns:
        Formatted Cypher commands
    """
    formatter = Neo4jFormatter()
    return formatter.format(tuple_set)