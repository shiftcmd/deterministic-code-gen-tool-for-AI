"""
Neo4j exporter for Python Debug Tool.

This module implements an exporter to save parsed code information
into a Neo4j graph database, creating nodes and relationships
for code elements.

# AI-Intent: Infrastructure
# Intent: This module serves as an adapter to the Neo4j database
# Confidence: High
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from . import ParserExporter, register_exporter

logger = logging.getLogger(__name__)


class Neo4jExporter(ParserExporter):
    """Exporter to save parsed code to Neo4j graph database."""

    name = "neo4j"
    description = "Exports parsed code to Neo4j graph database"
    version = "1.0.0"

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """
        Initialize the Neo4j exporter.

        Args:
            options: Configuration options for the exporter
                - uri: Neo4j connection URI (default: from environment)
                - user: Neo4j username (default: from environment)
                - password: Neo4j password (default: from environment)
                - database: Neo4j database name (default: neo4j)
                - batch_size: Number of statements to batch (default: 100)
                - clear_existing: Whether to clear existing nodes (default: False)
                - include_content: Whether to include code content (default: False)
                - detect_architecture: Whether to detect architectural patterns (default: False)
                - relationship_types: List of relationship types to create (default: all)
        """
        default_options = {
            "uri": os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
            "user": os.environ.get("NEO4J_USER", "neo4j"),
            "password": os.environ.get("NEO4J_PASSWORD", "password"),
            "database": os.environ.get("NEO4J_DATABASE", "neo4j"),
            "batch_size": 100,
            "clear_existing": False,
            "include_content": False,
            "detect_architecture": False,
            "relationship_types": [
                "IMPORTS",
                "DEFINES",
                "CONTAINS",
                "CALLS",
                "INHERITS_FROM",
                "DEPENDS_ON",
            ],
        }

        # Start with default options, then update with provided options
        merged_options = default_options.copy()
        if options:
            merged_options.update(options)

        super().__init__(merged_options)

        self.driver = None
        self.session = None
        self.transaction = None
        self.batch_count = 0
        self.total_nodes = 0
        self.total_relationships = 0

    def connect(self) -> bool:
        """
        Connect to the Neo4j database.

        Returns:
            True if connection succeeded, False otherwise
        """
        try:
            from neo4j import GraphDatabase

            self.driver = GraphDatabase.driver(
                self.options["uri"],
                auth=(self.options["user"], self.options["password"]),
            )

            # Verify connection
            self.driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {self.options['uri']}")

            return True
        except ImportError:
            logger.error(
                "Neo4j Python driver not installed. Install with 'pip install neo4j'"
            )
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from the Neo4j database."""
        if self.driver:
            self.driver.close()
            logger.info("Disconnected from Neo4j")

    def export(self, data: Dict[str, Any]) -> bool:
        """
        Export parsed data to Neo4j.

        Args:
            data: Parsed code data to export

        Returns:
            True if export succeeded, False otherwise
        """
        if not self.connect():
            return False

        try:
            with self.driver.session(database=self.options["database"]) as session:
                self.session = session

                # Clear existing data if requested
                if self.options["clear_existing"]:
                    self._clear_existing_data()

                # Create codebase node
                codebase_id = self._create_codebase_node(data)

                # Process modules
                self._process_modules(data, codebase_id)

                # Create relationships between nodes
                self._create_relationships(data)

                # Flush any remaining batch operations
                self._flush_batch()

                logger.info(
                    f"Export complete. Created {self.total_nodes} nodes and {self.total_relationships} relationships."
                )
                return True

        except Exception as e:
            logger.error(f"Error exporting to Neo4j: {e}")
            return False
        finally:
            self.disconnect()

    def _clear_existing_data(self) -> None:
        """Clear existing data from the database."""
        logger.info("Clearing existing data from Neo4j")
        self.session.run("MATCH (n) DETACH DELETE n")

    def _create_codebase_node(self, data: Dict[str, Any]) -> str:
        """
        Create a node representing the entire codebase.

        Args:
            data: Parsed codebase data

        Returns:
            ID of the created codebase node
        """
        codebase_name = data.get("name", "unknown")
        codebase_path = data.get("path", "unknown")

        # Generate a unique ID for the codebase
        codebase_id = (
            f"codebase_{codebase_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )

        # Prepare properties
        properties = {
            "id": codebase_id,
            "name": codebase_name,
            "path": codebase_path,
            "created_at": datetime.now().isoformat(),
            "module_count": len(data.get("modules", [])),
            "parsed_with": data.get("parsed_with", "unknown"),
        }

        # Add architectural information if available and enabled
        if self.options["detect_architecture"]:
            if "architectural_hints" in data:
                for key, value in data["architectural_hints"].items():
                    properties[key] = value

            # Default architectural style if not detected
            if "architecture_style" not in properties:
                properties["architecture_style"] = "unknown"

        # Create the codebase node
        query = "CREATE (c:Codebase $properties) " "RETURN c.id as id"

        result = self.session.run(query, properties=properties)
        self.total_nodes += 1

        # Return the codebase ID for reference
        return codebase_id

    def _process_modules(self, data: Dict[str, Any], codebase_id: str) -> None:
        """
        Process modules from the parsed data.

        Args:
            data: Parsed codebase data
            codebase_id: ID of the parent codebase node
        """
        modules = data.get("modules", [])
        if not modules and "ast_type" in data and data["ast_type"] == "module":
            # If the data itself is a module (single file analysis)
            modules = [data]

        for module_data in modules:
            # Create module node
            module_id = self._create_module_node(module_data, codebase_id)

            # Process classes
            for class_data in module_data.get("classes", []):
                class_id = self._create_class_node(class_data, module_id)

                # Process methods
                for method_data in class_data.get("methods", []) + class_data.get(
                    "method_details", []
                ):
                    self._create_function_node(method_data, module_id, class_id)

            # Process standalone functions
            for function_data in module_data.get("functions", []):
                if not function_data.get("is_method", False):
                    self._create_function_node(function_data, module_id)

            # Process variables
            for variable_data in module_data.get("variables", []):
                self._create_variable_node(variable_data, module_id)

            # Process imports
            for import_data in module_data.get("imports", []):
                self._create_import_node(import_data, module_id)

    def _create_module_node(self, data: Dict[str, Any], codebase_id: str) -> str:
        """
        Create a node representing a module.

        Args:
            data: Module data
            codebase_id: ID of the parent codebase

        Returns:
            ID of the created module node
        """
        module_name = data.get("name", "unknown")
        module_path = data.get("path", "unknown")

        # Generate a unique ID for the module
        module_id = f"module_{module_path}".replace("/", "_").replace(".", "_")

        # Prepare properties
        properties = {
            "id": module_id,
            "name": module_name,
            "path": module_path,
            "docstring": data.get("docstring", ""),
            "line_count": data.get("line_count", 0),
            "codebase_id": codebase_id,
        }

        # Include code content if requested
        if self.options["include_content"] and "content" in data:
            properties["content"] = data["content"]

        # Create the module node and relationship to codebase
        query = (
            "CREATE (m:Module $properties) "
            "WITH m "
            "MATCH (c:Codebase {id: $codebase_id}) "
            "CREATE (c)-[:CONTAINS]->(m) "
            "RETURN m.id as id"
        )

        self._execute_batch(
            query, parameters={"properties": properties, "codebase_id": codebase_id}
        )

        self.total_nodes += 1
        self.total_relationships += 1

        return module_id

    def _create_class_node(self, data: Dict[str, Any], module_id: str) -> str:
        """
        Create a node representing a class.

        Args:
            data: Class data
            module_id: ID of the parent module

        Returns:
            ID of the created class node
        """
        class_name = data.get("name", "unknown")

        # Generate a unique ID for the class
        class_id = f"{module_id}_class_{class_name}"

        # Prepare properties
        properties = {
            "id": class_id,
            "name": class_name,
            "docstring": data.get("docstring", ""),
            "line_start": data.get("line_start", 0),
            "line_end": data.get("line_end", 0),
            "bases": data.get("bases", []),
            "methods": data.get("methods", []),
            "module_id": module_id,
        }

        # Add complexity metrics if available
        if "complexity" in data:
            properties["complexity"] = data["complexity"]

        # Add architectural information if enabled and available
        if self.options["detect_architecture"] and "architectural_hints" in data:
            for key, value in data["architectural_hints"].items():
                properties[key] = value

        # Create the class node and relationship to module
        query = (
            "CREATE (c:Class $properties) "
            "WITH c "
            "MATCH (m:Module {id: $module_id}) "
            "CREATE (m)-[:DEFINES]->(c) "
            "RETURN c.id as id"
        )

        self._execute_batch(
            query, parameters={"properties": properties, "module_id": module_id}
        )

        self.total_nodes += 1
        self.total_relationships += 1

        return class_id

    def _create_function_node(
        self, data: Dict[str, Any], module_id: str, class_id: str = None
    ) -> str:
        """
        Create a node representing a function or method.

        Args:
            data: Function data
            module_id: ID of the parent module
            class_id: ID of the parent class (if method)

        Returns:
            ID of the created function node
        """
        function_name = data.get("name", "unknown")
        is_method = data.get("is_method", False) or class_id is not None

        # Generate a unique ID for the function
        if is_method and class_id:
            function_id = f"{class_id}_method_{function_name}"
        else:
            function_id = f"{module_id}_function_{function_name}"

        # Prepare properties
        properties = {
            "id": function_id,
            "name": function_name,
            "docstring": data.get("docstring", ""),
            "line_start": data.get("line_start", 0),
            "line_end": data.get("line_end", 0),
            "is_method": is_method,
            "is_static": data.get("is_static", False),
            "is_class_method": data.get("is_class", False),
            "parameters": [p.get("name") for p in data.get("parameters", [])],
            "parameter_count": len(data.get("parameters", [])),
            "return_annotation": data.get("return_annotation"),
            "module_id": module_id,
        }

        if class_id:
            properties["class_id"] = class_id

        # Add complexity if available
        if "complexity" in data:
            properties["complexity"] = data["complexity"]

        # Create the function node
        query = "CREATE (f:Function $properties) RETURN f.id as id"
        self._execute_batch(query, parameters={"properties": properties})
        self.total_nodes += 1

        # Create relationship to parent
        if is_method and class_id:
            # Method belongs to a class
            query = (
                "MATCH (f:Function {id: $function_id}), (c:Class {id: $class_id}) "
                "CREATE (c)-[:DEFINES]->(f)"
            )
            self._execute_batch(
                query, parameters={"function_id": function_id, "class_id": class_id}
            )
        else:
            # Standalone function belongs to a module
            query = (
                "MATCH (f:Function {id: $function_id}), (m:Module {id: $module_id}) "
                "CREATE (m)-[:DEFINES]->(f)"
            )
            self._execute_batch(
                query, parameters={"function_id": function_id, "module_id": module_id}
            )

        self.total_relationships += 1
        return function_id

    def _create_variable_node(
        self, data: Dict[str, Any], module_id: str, class_id: str = None
    ) -> str:
        """
        Create a node representing a variable.

        Args:
            data: Variable data
            module_id: ID of the parent module
            class_id: ID of the parent class (if class variable)

        Returns:
            ID of the created variable node
        """
        variable_name = data.get("name", "unknown")
        scope = data.get("scope", "module")

        # Generate a unique ID for the variable
        if scope == "class" and class_id:
            variable_id = f"{class_id}_var_{variable_name}"
        else:
            variable_id = f"{module_id}_var_{variable_name}"

        # Prepare properties
        properties = {
            "id": variable_id,
            "name": variable_name,
            "line_start": data.get("line_start", 0),
            "line_end": data.get("line_end", 0),
            "inferred_type": data.get("inferred_type", "unknown"),
            "is_constant": data.get("is_constant", False),
            "scope": scope,
            "module_id": module_id,
        }

        if class_id:
            properties["class_id"] = class_id

        # Create the variable node
        query = "CREATE (v:Variable $properties) RETURN v.id as id"
        self._execute_batch(query, parameters={"properties": properties})
        self.total_nodes += 1

        # Create relationship to parent
        if scope == "class" and class_id:
            # Class variable
            query = (
                "MATCH (v:Variable {id: $variable_id}), (c:Class {id: $class_id}) "
                "CREATE (c)-[:DEFINES]->(v)"
            )
            self._execute_batch(
                query, parameters={"variable_id": variable_id, "class_id": class_id}
            )
        else:
            # Module variable
            query = (
                "MATCH (v:Variable {id: $variable_id}), (m:Module {id: $module_id}) "
                "CREATE (m)-[:DEFINES]->(v)"
            )
            self._execute_batch(
                query, parameters={"variable_id": variable_id, "module_id": module_id}
            )

        self.total_relationships += 1
        return variable_id

    def _create_import_node(self, data: Dict[str, Any], module_id: str) -> str:
        """
        Create a node representing an import statement.

        Args:
            data: Import data
            module_id: ID of the parent module

        Returns:
            ID of the created import node
        """
        import_name = data.get("name", "unknown")
        import_type = data.get("type", "import")

        # Generate a unique ID for the import
        if "fromname" in data:
            import_id = f"{module_id}_import_{data['fromname']}_{import_name}"
        else:
            import_id = f"{module_id}_import_{import_name}"

        # Clean up ID to avoid invalid characters
        import_id = import_id.replace(".", "_").replace("*", "star")

        # Prepare properties
        properties = {
            "id": import_id,
            "name": import_name,
            "type": import_type,
            "line_start": data.get("line_start", 0),
            "module_id": module_id,
        }

        if "fromname" in data:
            properties["fromname"] = data["fromname"]

        if "asname" in data and data["asname"]:
            properties["asname"] = data["asname"]

        if "is_star" in data:
            properties["is_star"] = data["is_star"]

        # Create the import node
        query = "CREATE (i:Import $properties) RETURN i.id as id"
        self._execute_batch(query, parameters={"properties": properties})
        self.total_nodes += 1

        # Create relationship to module
        query = (
            "MATCH (i:Import {id: $import_id}), (m:Module {id: $module_id}) "
            "CREATE (m)-[:IMPORTS]->(i)"
        )
        self._execute_batch(
            query, parameters={"import_id": import_id, "module_id": module_id}
        )

        self.total_relationships += 1
        return import_id

    def _create_relationships(self, data: Dict[str, Any]) -> None:
        """
        Create relationships between nodes based on the parsed data.

        Args:
            data: Parsed codebase data
        """
        if "INHERITS_FROM" in self.options["relationship_types"]:
            self._create_inheritance_relationships()

        if "CALLS" in self.options["relationship_types"]:
            self._create_function_call_relationships()

        if "DEPENDS_ON" in self.options["relationship_types"]:
            self._create_dependency_relationships()

    def _create_inheritance_relationships(self) -> None:
        """Create inheritance relationships between classes."""
        # Find all classes with base classes
        query = (
            "MATCH (c:Class) "
            "WHERE size(c.bases) > 0 "
            "RETURN c.id as id, c.name as name, c.bases as bases, c.module_id as module_id"
        )

        result = self.session.run(query)

        for record in result:
            class_id = record["id"]
            bases = record["bases"]
            module_id = record["module_id"]

            for base in bases:
                # Try to find the base class
                base_query = (
                    "MATCH (b:Class) " "WHERE b.name = $base_name " "RETURN b.id as id"
                )

                # First try exact name
                base_result = self.session.run(base_query, base_name=base)
                base_records = list(base_result)

                if not base_records:
                    # If not found, try with module qualifier
                    if "." in base:
                        base_name = base.split(".")[-1]
                        base_result = self.session.run(base_query, base_name=base_name)
                        base_records = list(base_result)

                for base_record in base_records:
                    base_id = base_record["id"]

                    # Create the inheritance relationship
                    relationship_query = (
                        "MATCH (c:Class {id: $class_id}), (b:Class {id: $base_id}) "
                        "CREATE (c)-[:INHERITS_FROM]->(b)"
                    )

                    self._execute_batch(
                        relationship_query,
                        parameters={"class_id": class_id, "base_id": base_id},
                    )

                    self.total_relationships += 1

    def _create_function_call_relationships(self) -> None:
        """Create function call relationships."""
        # This would require additional analysis to detect function calls
        # which is typically not included in basic parsing
        # Advanced tools like astroid can provide this information

        logger.info("Function call relationship detection requires additional analysis")

    def _create_dependency_relationships(self) -> None:
        """Create dependency relationships between modules."""
        # Create dependency relationships based on imports
        query = (
            "MATCH (m:Module)-[:IMPORTS]->(i:Import) "
            "MATCH (target:Module) "
            "WHERE (i.name = target.name OR i.fromname = target.name) "
            "CREATE (m)-[:DEPENDS_ON]->(target)"
        )

        result = self.session.run(query)
        self.total_relationships += result.consume().counters.relationships_created

    def _execute_batch(self, query: str, parameters: Dict[str, Any] = None) -> None:
        """
        Execute a query in batch mode.

        Args:
            query: Cypher query to execute
            parameters: Query parameters
        """
        if not self.transaction:
            self.transaction = self.session.begin_transaction()

        self.transaction.run(query, parameters or {})
        self.batch_count += 1

        if self.batch_count >= self.options["batch_size"]:
            self._flush_batch()

    def _flush_batch(self) -> None:
        """Commit the current batch transaction."""
        if self.transaction:
            self.transaction.commit()
            self.transaction = None
            self.batch_count = 0

    def get_schema(self) -> Dict[str, Any]:
        """
        Get the schema of the Neo4j graph.

        Returns:
            Dictionary describing the schema
        """
        if not self.driver:
            if not self.connect():
                return {"error": "Could not connect to Neo4j"}

        try:
            with self.driver.session(database=self.options["database"]) as session:
                # Get node labels
                labels_query = "CALL db.labels()"
                labels_result = session.run(labels_query)
                labels = [record["label"] for record in labels_result]

                # Get relationship types
                rels_query = "CALL db.relationshipTypes()"
                rels_result = session.run(rels_query)
                relationship_types = [
                    record["relationshipType"] for record in rels_result
                ]

                # Get property keys
                props_query = "CALL db.propertyKeys()"
                props_result = session.run(props_query)
                property_keys = [record["propertyKey"] for record in props_result]

                # Sample schema for each node label
                node_schemas = {}
                for label in labels:
                    sample_query = f"MATCH (n:{label}) RETURN n LIMIT 1"
                    sample_result = session.run(sample_query)
                    records = list(sample_result)

                    if records:
                        sample_node = records[0]["n"]
                        node_schemas[label] = {
                            "properties": list(dict(sample_node).keys()),
                            "count": session.run(
                                f"MATCH (:{label}) RETURN count(*) as count"
                            ).single()["count"],
                        }
                    else:
                        node_schemas[label] = {"properties": [], "count": 0}

                return {
                    "labels": labels,
                    "relationship_types": relationship_types,
                    "property_keys": property_keys,
                    "node_schemas": node_schemas,
                }

        except Exception as e:
            logger.error(f"Error getting Neo4j schema: {e}")
            return {"error": str(e)}
        finally:
            self.disconnect()


# Register the exporter
register_exporter(Neo4jExporter)
