#!/usr/bin/env python
"""
Bridge between Supabase embeddings and Neo4j knowledge graph.

This script enriches Neo4j nodes with architectural metadata from Supabase embeddings,
creating a more complete view of the codebase architecture.
"""

import os
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv
from supabase import create_client, Client
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()

class ArchitecturalBridge:
    """Bridge between Supabase embeddings and Neo4j graph database for architectural analysis.
    
    This class handles enriching the Neo4j graph with architectural metadata from embeddings,
    as well as analyzing the graph for architectural patterns and generating reports.
    """
    
    def discover_schema(self, project_name: str) -> Dict:
        """Discover the schema of the Neo4j database for the specified project.
        
        This allows the script to adapt to different property naming conventions
        and available node/relationship types in the database.
        """
        schema = {
            "codebase_id": project_name,  # Default fallback
            "codebase_id_property": "name",  # Default property name
            "layer_property": "dominant_layer",  # Default layer property
            "confidence_property": "layer_confidence",  # Default confidence property
            "available_labels": [],
            "available_relationships": [],
            "codebase_properties": {}
        }
        
        with self.neo4j_driver.session() as session:
            # Common property names for project identifiers
            potential_project_props = ["name", "project_name", "repo_name", "codebase_name", "identifier"]
            
            # Try to find the codebase node
            codebase_found = False
            for prop in potential_project_props:
                try:
                    result = session.run(
                        f"MATCH (c:Codebase) WHERE c.{prop} = $name RETURN c, '{prop}' as prop_name LIMIT 1", 
                        {"name": project_name}
                    )
                    if result.peek():
                        record = result.single()
                        schema["codebase_properties"] = dict(record["c"].items())
                        schema["codebase_id_property"] = record["prop_name"]
                        schema["codebase_id"] = schema["codebase_properties"].get(schema["codebase_id_property"], project_name)
                        codebase_found = True
                        break
                except Exception:
                    # Property might not exist, continue to the next one
                    continue
            
            # If not found by name, try to list available codebases
            if not codebase_found:
                print(f"⚠️ Could not find codebase with name '{project_name}'. Trying alternative lookup methods...")
                
                # Try to find any codebase as fallback
                result = session.run("MATCH (c:Codebase) RETURN c LIMIT 10")
                available_codebases = []
                
                while result.peek():
                    codebase = result.single()["c"]
                    codebase_dict = dict(codebase.items())
                    available_codebases.append(codebase_dict)
                    
                    # Check if any property value matches our project name
                    for prop, value in codebase_dict.items():
                        if isinstance(value, str) and project_name.lower() in value.lower():
                            schema["codebase_properties"] = codebase_dict
                            schema["codebase_id_property"] = prop
                            schema["codebase_id"] = value
                            codebase_found = True
                            print(f"✅ Found codebase with {prop}='{value}'")
                            break
                    if codebase_found:
                        break
                
                # If still not found but we have codebases, use the first one
                if not codebase_found and available_codebases:
                    schema["codebase_properties"] = available_codebases[0]
                    # Try to find a suitable identifier property
                    for prop in potential_project_props:
                        if prop in schema["codebase_properties"]:
                            schema["codebase_id_property"] = prop
                            schema["codebase_id"] = schema["codebase_properties"].get(prop)
                            codebase_found = True
                            print(f"✅ Using available codebase with {prop}='{schema['codebase_id']}'")
                            break
                    
                    if not codebase_found and schema["codebase_properties"]:
                        # Just use any property as identifier if all else fails
                        for prop, value in schema["codebase_properties"].items():
                            if isinstance(value, str) and prop != "path":
                                schema["codebase_id_property"] = prop
                                schema["codebase_id"] = value
                                codebase_found = True
                                print(f"✅ Using property {prop}='{value}' as codebase identifier")
                                break
            
            if not codebase_found:
                print(f"❌ No codebase found in Neo4j database. Please ensure the repository was parsed correctly.")
                return schema
            
            # Get available labels
            result = session.run("CALL db.labels() YIELD label RETURN collect(label) as labels")
            schema["available_labels"] = result.single()["labels"] if result.peek() else []
            
            # Get available relationship types
            result = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) as rel_types")
            schema["available_relationships"] = result.single()["rel_types"] if result.peek() else []
            
            # Discover architectural layer properties
            potential_layer_props = ["dominant_layer", "architectural_layer", "layer", "hexagonal_layer", "arch_layer"]
            for prop in potential_layer_props:
                try:
                    result = session.run(f"MATCH (n) WHERE n.{prop} IS NOT NULL RETURN count(n) as count LIMIT 1")
                    if result.peek() and result.single()["count"] > 0:
                        schema["layer_property"] = prop
                        break
                except Exception:
                    continue
            
            # Discover confidence properties
            confidence_props = ["layer_confidence", "architectural_confidence", "confidence", "arch_confidence"]
            for prop in confidence_props:
                try:
                    result = session.run(f"MATCH (n) WHERE n.{prop} IS NOT NULL RETURN count(n) as count LIMIT 1")
                    if result.peek() and result.single()["count"] > 0:
                        schema["confidence_property"] = prop
                        break
                except Exception:
                    continue
        
        return schema
    
    def __init__(self):
        """Initialize the bridge with connections to Supabase and Neo4j."""
        # Supabase connection
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        if not supabase_url or not supabase_key:
            raise ValueError("Missing Supabase credentials in .env")
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # Neo4j connection
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "neo4j")
        self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        print("✅ Connections established to Supabase and Neo4j")
    
    def close(self):
        """Close connections."""
        self.neo4j_driver.close()
    
    def fetch_embedding_metadata(self, project_name: str) -> List[Dict[str, Any]]:
        """Fetch embedding metadata from Supabase for a specific project."""
        print(f"🔍 Fetching embeddings for project: {project_name}")
        
        try:
            response = self.supabase.table("python_code_chunks") \
                .select("id, project_name, file_name, relative_path, chunk_type, name, architectural_layer") \
                .eq("project_name", project_name) \
                .execute()
            
            if hasattr(response, 'data'):
                print(f"✅ Found {len(response.data)} embedding records")
                return response.data
            else:
                print("❌ No data attribute in response")
                return []
        except Exception as e:
            print(f"❌ Error fetching embeddings: {e}")
            return []
        
    def _get_neo4j_node_by_name(self, tx, node_type: str, name: str, file_name: Optional[str] = None) -> List:
        """Find Neo4j nodes by name and optionally file name."""
        query = f"""
        MATCH (n:{node_type})
        WHERE n.name = $name
        {" AND n.path CONTAINS $file_name" if file_name else ""}
        RETURN n
        """
        params = {"name": name}
        if file_name:
            params["file_name"] = file_name
        
        result = tx.run(query, **params)
        return list(result)
    
    def _update_node_architectural_metadata(self, tx, node_id: int, metadata: Dict[str, Any]):
        """Update a Neo4j node with architectural metadata."""
        # Extract relevant metadata
        arch_layer = metadata.get("architectural_layer")
        chunk_type = metadata.get("chunk_type")
        
        # Skip if no architectural layer
        if not arch_layer:
            return
        
        # Update the node
        query = """
        MATCH (n)
        WHERE id(n) = $node_id
        SET n.architectural_layer = $arch_layer,
            n.chunk_type = $chunk_type,
            n.enriched = true
        RETURN n
        """
        tx.run(query, node_id=node_id, arch_layer=arch_layer, chunk_type=chunk_type)
    
    def match_and_enrich(self, metadata_list: List[Dict[str, Any]]):
        """Match embedding metadata to Neo4j nodes and enrich them."""
        print("🔄 Matching and enriching Neo4j nodes...")
        
        # Group by type for efficiency
        by_type = {
            "function": [],
            "class": [],
            "module": []
        }
        
        for item in metadata_list:
            chunk_type = item.get("chunk_type", "").lower()
            if chunk_type in by_type:
                by_type[chunk_type].append(item)
        
        # Process each type
        with self.neo4j_driver.session() as session:
            for chunk_type, items in by_type.items():
                print(f"🔄 Processing {len(items)} {chunk_type} items")
                
                node_type = {
                    "function": "Function",
                    "class": "Class",
                    "module": "File"
                }.get(chunk_type)
                
                if not node_type:
                    continue
                
                for item in items:
                    name = item.get("name")
                    file_name = item.get("file_name")
                    relative_path = item.get("relative_path")
                    
                    if not name:
                        continue
                    
                    file_path = None
                    if relative_path and file_name:
                        file_path = os.path.join(relative_path, file_name)
                    
                    # Determine if the node exists in Neo4j
                    if "architectural_layer" in item and item["architectural_layer"]:  
                        architectural_layer = item.get("architectural_layer", "")
                        # Update both layer properties to ensure compatibility
                        session.run("""
                            MATCH (n:{node_type} {{name: $name}})
                            SET n.dominant_layer = $layer, 
                                n.architectural_layer = $layer
                            RETURN n
                        """, {"name": name, "layer": architectural_layer, "node_type": node_type})
                        
                        # For classes and functions, also add architectural label
                        if node_type in ["Class", "Function"]:
                            # Create layer node if it doesn't exist
                            session.run("""
                                MERGE (l:ArchitecturalLayer {{name: $layer}})
                                RETURN l
                            """, {"layer": architectural_layer})
                            
                            # Connect node to layer
                            session.run("""
                                MATCH (n:{node_type} {{name: $name}})
                                MATCH (l:ArchitecturalLayer {{name: $layer}})
                                MERGE (n)-[:BELONGS_TO_LAYER]->(l)
                            """, {"name": name, "layer": architectural_layer, "node_type": node_type})
                    
                    # Try to find the node
                    result = session.execute_read(
                        self._get_neo4j_node_by_name, 
                        node_type, 
                        name,
                        file_name
                    )
                    
                    if result and len(result) > 0:
                        node = result[0]["n"]
                        session.execute_write(
                            self._update_node_architectural_metadata,
                            node.id,
                            item
                        )
    
    def create_architectural_views(self):
        """Create architectural views in Neo4j for better analysis."""
        print("🏗️ Creating architectural views...")
        
        with self.neo4j_driver.session() as session:
            # Create architectural layers as explicit nodes
            session.run("""
            MATCH (n)
            WHERE n.dominant_layer IS NOT NULL OR n.architectural_layer IS NOT NULL
            WITH DISTINCT coalesce(n.dominant_layer, n.architectural_layer) as layer
            WHERE layer IS NOT NULL
            MERGE (l:ArchitecturalLayer {name: layer})
            RETURN count(l)
            """)
            
            # Tag nodes with architectural_type for clearer visualization
            session.run("""
            MATCH (n)
            WHERE n.dominant_layer IS NOT NULL OR n.architectural_layer IS NOT NULL
            WITH n, coalesce(n.dominant_layer, n.architectural_layer) as layer
            SET n:ArchitecturalComponent,
                n.architectural_type = CASE
                    WHEN layer = 'Domain' THEN 'Core'
                    WHEN layer = 'Application' THEN 'Core'
                    WHEN layer = 'Port' THEN 'Interface'
                    WHEN layer = 'Adapter' THEN 'Infrastructure'
                    ELSE 'Unclassified'
                END
            RETURN count(n)
            """)
            
            # Connect nodes to their architectural layers
            session.run("""
            MATCH (n) 
            WHERE n.dominant_layer IS NOT NULL OR n.architectural_layer IS NOT NULL
            WITH n, coalesce(n.dominant_layer, n.architectural_layer) as layer
            WHERE layer IS NOT NULL
            MATCH (l:ArchitecturalLayer {name: layer})
            MERGE (n)-[:BELONGS_TO_LAYER]->(l)
            RETURN count(n)
            """)
    
    def generate_architectural_report(self, project_name: str, detailed=False) -> Dict:
        """Generate a comprehensive architectural report.
        
        This analyzes the Neo4j data to generate a report on architectural patterns,
        potential issues, and suggestions for improvements.
        
        Args:
            project_name: Name of the project to analyze
            detailed: Whether to include detailed component lists
            
        Returns:
            Dictionary containing the architectural report
        """
        # Initialize report structure
        report = {
            "project_name": project_name,
            "timestamp": time.time(),
            "analysis_version": "2.0",
            "layer_stats": {},
            "layer_relationships": [],
            "potential_issues": [],
            "components": {
                "classes": [],
                "functions": [],
                "files": []
            },
            "architectural_metrics": {
                "complexity": 0.0,
                "cohesion": 0.0,
                "coupling": 0.0
            },
            "correction_suggestions": []
        }
        
        # Discover schema for this project
        schema = self.discover_schema(project_name)
        
        # Log schema discovery results
        print(f"\n📋 Schema discovery results for '{project_name}'")
        print(f"  Project identifier: {schema['codebase_id_property']}={schema['codebase_id']}")
        print(f"  Layer property: {schema['layer_property']}")
        print(f"  Available relationships: {', '.join(schema['available_relationships'])}")
        
        # If no codebase found, return empty report
        if not schema["codebase_properties"]:
            return report
            
        try:
            with self.neo4j_driver.session() as session:
                # Layer statistics using the discovered schema
                layer_prop = schema['layer_property']
                codebase_id_prop = schema['codebase_id_property']
                codebase_id = schema['codebase_id']
                
                print(f"📊 Generating architectural report for {project_name}...")
                
                # Dynamic query construction based on discovered schema
                query = f"""
                MATCH (c:Codebase) WHERE c.{codebase_id_prop} = $codebase_id
                MATCH (n) 
                WHERE n.{layer_prop} IS NOT NULL
                RETURN 
                    LOWER(n.{layer_prop}) as layer, 
                    count(n) as count, 
                    count(CASE WHEN n:Class THEN 1 END) as class_count,
                    count(CASE WHEN n:Function THEN 1 END) as function_count,
                    count(CASE WHEN n:File THEN 1 END) as file_count
                ORDER BY count DESC
                """
                
                try:
                    result = session.run(query, {"codebase_id": codebase_id})
                
                    for record in result:
                        report["layer_stats"][record["layer"]] = {
                            "total": record["count"],
                            "class_count": record["class_count"],
                            "function_count": record["function_count"],
                            "file_count": record["file_count"]
                        }
                except Exception as e:
                    print(f"Error querying layer statistics: {str(e)}")
                
                # Check for exception proliferation
                # First verify that Class label exists in the database
                exception_count = 0
                if "Class" in schema["available_labels"]:
                    result = session.run(f"""
                    MATCH (c:Class) 
                    WHERE c.name CONTAINS 'Exception' OR c.name CONTAINS 'Error'
                    WITH count(distinct c) as exception_count
                    RETURN exception_count
                    """)
                    
                    exception_count = result.single()["exception_count"] if result.peek() else 0
                
                if exception_count > 10:  # Arbitrary threshold
                    report["potential_issues"].append({
                        "issue_type": "Exception Proliferation",
                        "severity": "HIGH",
                        "description": f"Too many exception types ({exception_count})",
                        "impact": "Having too many exception types makes error handling complex, inconsistent, and difficult to maintain.",
                        "remediation": [
                            "Create a hierarchical exception framework",
                            "Consolidate similar exception types",
                            "Establish consistent error handling patterns",
                            "Consider using custom error codes instead of custom exception classes"
                        ]
                    })
                
                # 2. Domain Model Duplication - check if Class label exists
                if "Class" in schema["available_labels"]:
                    try:
                        result = session.run("""
                        MATCH (c1:Class)
                        MATCH (c2:Class)
                        WHERE id(c1) < id(c2) 
                        AND c1.name = c2.name 
                        AND c1.name IS NOT NULL
                        AND c1.module <> c2.module
                        AND NOT c1.name STARTS WITH '__'
                        AND NOT c1.name IN ['Test', 'Exception', 'Error']
                        RETURN c1.name as class_name, collect(c1.module + '.' + c1.name) + collect(c2.module + '.' + c2.name) as instances
                        LIMIT 10
                        """)
                        
                        duplicated_classes = []
                        for record in result:
                            duplicated_classes.append({
                                "name": record["class_name"],
                                "instances": record["instances"]
                            })
                        
                        if duplicated_classes:
                            report["potential_issues"].append({
                                "issue_type": "Domain Model Duplication",
                                "severity": "CRITICAL",
                                "description": "Multiple copies of domain models exist across the codebase",
                                "instances": duplicated_classes,
                                "impact": "Domain model duplication leads to inconsistencies, difficult maintenance, and confusion about the canonical implementation.",
                                "remediation": [
                                    "Consolidate duplicated domain models into a shared domain package",
                                    "Use dependency injection to provide domain model implementations",
                                    "Implement a single source of truth for domain entities",
                                    "Consider using a shared kernel if domains are truly separate"
                                ]
                            })
                    except Exception as e:
                        print(f"Could not check for domain model duplication: {str(e)}")
                
                # 3. Business Logic Duplication - check if Function nodes and required relationships exist
                if "Function" in schema["available_labels"]:
                    duplicated_functions = []
                    
                    # Check if we can use apoc for text similarity
                    try:
                        result = session.run("""
                        MATCH (f1:Function)
                        MATCH (f2:Function)
                        WHERE id(f1) < id(f2)
                        AND f1.name = f2.name
                        AND f1.name IS NOT NULL
                        AND size(f1.name) > 3
                        AND NOT f1.name STARTS WITH '__'
                        WITH f1, f2, apoc.text.jaroWinklerDistance(f1.docstring, f2.docstring) as similarity
                        WHERE similarity > 0.8
                        RETURN f1.name as function_name, collect(f1.module + '.' + f1.name) + collect(f2.module + '.' + f2.name) as instances
                        LIMIT 10
                        """)
                        
                        for record in result:
                            duplicated_functions.append({
                                "name": record["function_name"],
                                "instances": record["instances"]
                            })
                    except Exception as e:
                        print(f"Could not use APOC for similarity check: {str(e)}")
                        
                    # Alternative simpler check if apoc is not available or found nothing
                    if not duplicated_functions:
                        try:
                            result = session.run("""
                            MATCH (f1:Function)
                            MATCH (f2:Function)
                            WHERE id(f1) < id(f2) 
                            AND f1.name = f2.name 
                            AND f1.name IS NOT NULL
                            AND size(f1.name) > 3
                            AND NOT f1.name STARTS WITH '__'
                            AND f1.module <> f2.module
                            RETURN f1.name as function_name, collect(f1.module + '.' + f1.name) + collect(f2.module + '.' + f2.name) as instances
                            LIMIT 10
                            """)
                            
                            for record in result:
                                duplicated_functions.append({
                                    "name": record["function_name"],
                                    "instances": record["instances"]
                                })
                        except Exception as e:
                            print(f"Could not check for business logic duplication: {str(e)}")
                    
                    if duplicated_functions:
                        report["potential_issues"].append({
                            "issue_type": "Business Logic Duplication",
                            "severity": "HIGH",
                            "description": "Repeated business logic across components",
                            "instances": duplicated_functions,
                            "impact": "Duplicated business logic creates maintenance challenges, inconsistent behavior, and makes the system more prone to bugs when logic changes in one place but not others.",
                            "remediation": [
                                "Extract common logic into shared services/utilities",
                                "Apply DRY (Don't Repeat Yourself) principle",
                                "Consider using dependency injection to reuse core logic",
                                "Refactor duplicated code into a common base class or trait"
                            ]
                        })
                
                # 1. Architectural Relationships Analysis
                layer_prop = schema['layer_property']
                
                # Check if relevant relationship types exist
                if "DEPENDS_ON" in schema["available_relationships"] or "USES" in schema["available_relationships"]:
                    # Use the relationship types that are available
                    rel_types = []
                    if "DEPENDS_ON" in schema["available_relationships"]: rel_types.append("DEPENDS_ON")
                    if "USES" in schema["available_relationships"]: rel_types.append("USES")
                    
                    rel_query = "|".join(rel_types)
                    
                    query = f"""
                    MATCH (from)-[r:{rel_query}]->(to)
                    WHERE from.{layer_prop} IS NOT NULL AND to.{layer_prop} IS NOT NULL
                    WITH LOWER(from.{layer_prop}) as from_layer,
                         LOWER(to.{layer_prop}) as to_layer,
                         count(r) as rel_count
                    RETURN from_layer, to_layer, rel_count
                    ORDER BY rel_count DESC
                    """
                    
                    try:
                        result = session.run(query)
                    except Exception as e:
                        print(f"Error analyzing architectural relationships: {str(e)}")
                        return report
                
                    for record in result:
                        report["layer_relationships"].append({
                            "from_layer": record["from_layer"],
                            "to_layer": record["to_layer"],
                            "rel_count": record["rel_count"]
                        })
                
                # Check for architectural violations
                # Process each relationship record for architectural violations
                for record in report["layer_relationships"]:
                    try:
                        if self._check_architectural_violation(record["from_layer"], record["to_layer"]):
                            report["potential_issues"].append({
                                "issue_type": "Architectural Layer Violation",
                                "severity": "CRITICAL",
                                "description": f"Invalid dependency from {record['from_layer']} to {record['to_layer']}",
                                "impact": "Violating architectural layer constraints leads to tight coupling, reduced maintainability, and makes it harder to replace or evolve components independently.",
                                "remediation": [
                                    "Refactor code to respect hexagonal architecture boundaries",
                                    "Introduce proper abstractions via ports/interfaces",
                                    "Use dependency injection to invert control flow",
                                    "Apply the Dependency Inversion Principle"
                                ]
                            })
                    except Exception as e:
                        print(f"Error checking architectural violation: {str(e)}")
                        
                # Check for hexagonal architecture violations
                try:
                    violations = self._check_hex_architectural_violations(session, project_name)
                    report["potential_issues"].extend(violations)
                except Exception as e:
                    print(f"Error checking architectural violations: {str(e)}")
        
                # Save report to file
                try:
                    report_file = f"architectural_report_{project_name.replace('/', '_')}_{int(time.time())}.json"
                    with open(report_file, 'w', encoding='utf-8') as f:
                        json.dump(report, f, indent=2)
                
                    print(f"📝 Architectural report saved to {report_file}")
                except Exception as e:
                    print(f"Error saving report to file: {str(e)}")
        except Exception as e:
            print(f"Critical error in report generation: {str(e)}")
            return {"error": str(e)}
            
        return report

    def _check_architectural_violation(self, from_layer: str, to_layer: str) -> bool:
        """Check if this relationship violates hexagonal architecture principles."""
        # Simplified rules for hexagonal architecture
        hexagonal_rules = {
            "domain": ["application"],  # Domain can only be used by Application
            "application": ["domain", "port"],  # Application can use Domain and Ports
            "port": [],  # Ports should not depend on anything
            "adapter": ["port"],  # Adapters can only use Ports
            "primaryadapter": ["port"],  # Primary adapters can only use Ports
            "secondaryadapter": ["port"],  # Secondary adapters can only use Ports
            "infrastructure": ["domain", "application"],  # Infrastructure can use domain/application
            "interface": ["application", "domain"]  # Interface can use application/domain
        }
        
        # If we have rules for this layer
        if from_layer in hexagonal_rules:
            allowed_dependencies = hexagonal_rules[from_layer]
            return to_layer not in allowed_dependencies
        
        return False  # No rules defined, so no violation
        
    def _check_hex_architectural_violations(self, session, codebase_name):
        """Check for hexagonal architecture violations in a generic way."""
        violations = []
        
        # Define hexagonal architecture layer dependency rules
        # Format: {"outer_layer": ["inner_layers_it_shouldnt_depend_on"]}
        hex_rules = {
            "infrastructure": [],  # Infrastructure can depend on any layer
            "presentation": ["domain"],  # Presentation shouldn't depend directly on domain
            "application": [],  # Application can depend on any layer
            "domain": ["infrastructure", "presentation"]  # Domain shouldn't depend on infrastructure or presentation
        }
        
        # Check for all defined layer violation rules
        for source_layer, forbidden_targets in hex_rules.items():
            for target_layer in forbidden_targets:
                # Try with both dominant_layer and architectural_layer properties
                violation_result = session.run("""
                    MATCH (source)-[r:DEPENDS_ON|CALLS|USES|INHERITS_FROM]->(target)
                    WHERE source.project_name = $codebase_name AND target.project_name = $codebase_name
                        AND (
                            (LOWER(COALESCE(source.dominant_layer, source.architectural_layer)) = $source_layer
                            AND LOWER(COALESCE(target.dominant_layer, target.architectural_layer)) = $target_layer)
                        )
                    RETURN count(*) as violation_count
                """, {"codebase_name": codebase_name, "source_layer": source_layer.lower(), "target_layer": target_layer.lower()})
                
                record = violation_result.single()
                if record and record["violation_count"] > 0:
                    violations.append({
                        "description": f"{source_layer.capitalize()} layer directly depends on {target_layer.capitalize()} layer",
                        "count": record["violation_count"],
                        "source": source_layer,
                        "target": target_layer
                    })
        
        # Also check for unknown layer components that have dependencies
        unknown_layer_result = session.run("""
            MATCH (source)-[r:DEPENDS_ON|CALLS|USES|INHERITS_FROM]->(target)
            WHERE source.project_name = $codebase_name AND target.project_name = $codebase_name
                AND (COALESCE(source.dominant_layer, source.architectural_layer) IS NULL
                    OR LOWER(COALESCE(source.dominant_layer, source.architectural_layer)) = 'unknown')
                AND (target.dominant_layer IS NOT NULL OR target.architectural_layer IS NOT NULL)
            RETURN count(*) as violation_count
        """, {"codebase_name": codebase_name})
        
        record = unknown_layer_result.single()
        if record and record["violation_count"] > 5:  # Only flag if significant number
            violations.append({
                "description": "Components with unknown architectural layer have dependencies on known layers",
                "count": record["violation_count"],
                "source": "unknown",
                "target": "various"
            })
        
        return violations

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Bridge Supabase embeddings with Neo4j knowledge graph")
    parser.add_argument("project_name", help="Name of the project to analyze")
    parser.add_argument("--report-only", action="store_true", help="Only generate report without enriching")
    parser.add_argument("--detailed", action="store_true", help="Generate a more detailed report with component lists")
    args = parser.parse_args()
    
    bridge = ArchitecturalBridge()
    
    try:
        if not args.report_only:
            # Fetch and enrich
            metadata_list = bridge.fetch_embedding_metadata(args.project_name)
            bridge.match_and_enrich(metadata_list)
            bridge.create_architectural_views()
        
        # Generate report
        report = bridge.generate_architectural_report(args.project_name, detailed=args.detailed)
        
        # Add AI guidance for architectural correction
        if report["potential_issues"]:
            report["correction_suggestions"] = [
                {
                    "category": "Architecture Refactoring",
                    "suggestion": "Consider implementing a strict hexagonal architecture pattern with clear boundaries between domain, application, ports, and adapters.",
                    "reasoning": "The identified issues suggest architectural drift and inconsistent application of patterns."
                },
                {
                    "category": "Code Organization",
                    "suggestion": "Establish a modular monolith structure with well-defined package boundaries before considering microservices.",
                    "reasoning": "The duplication issues indicate premature splitting without proper modularization."
                },
                {
                    "category": "Testing Strategy",
                    "suggestion": "Implement architectural fitness functions that verify compliance with the intended architecture.",
                    "reasoning": "Automated tests would prevent architectural degradation over time."
                }
            ]
        print(f"\n🚀 Found {len(report.get('potential_issues', []))} potential architectural issues")
        
        for issue in report.get("potential_issues", []):
            print(f"\n⚠️ {issue['severity']} - {issue['issue_type']}")
            print(f"   {issue['description']}")
    finally:
        bridge.close()

if __name__ == "__main__":
    main()
