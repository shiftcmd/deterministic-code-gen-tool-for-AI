"""
Relationship Extractor - Adapted from MCP ast_dependency_extraction.py

Extracts code dependencies using Python AST for PostgreSQL + Neo4j integration.
Based on example_code/ast_dependency_extraction.py with adaptations for:
- PostgreSQL for relationship metadata storage
- Neo4j for graph relationship creation
- Integration with existing debug tool architecture

Reference: example_code/INTEGRATION_PSEUDOCODE.md Section 5 (lines 323-450)
"""

import ast
import json
import logging
from typing import Dict, List, Set, Tuple, Optional, Any
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class CodeRelationship:
    """Represents a relationship between code components"""
    relationship_type: str  # 'import', 'function_call', 'method_call', 'inheritance', 'class_usage'
    source_component_id: Optional[int]
    target_component_id: Optional[int]
    source_file: str
    target_file: Optional[str]
    source_name: str
    target_name: str
    line_number: int
    metadata: Dict[str, Any]

class RelationshipExtractor(ast.NodeVisitor):
    """
    Extract code dependencies using Python AST for PostgreSQL + Neo4j integration.
    
    Adapted from MCP ast_dependency_extraction.py to work with existing:
    - PostgreSQL for structured relationship data
    - Neo4j for graph relationships
    - Chroma for semantic similarity (future enhancement)
    """
    
    def __init__(self, file_path: str, module_name: str, postgres_client=None, neo4j_client=None):
        self.file_path = file_path
        self.module_name = module_name
        self.postgres_client = postgres_client
        self.neo4j_client = neo4j_client
        self.current_class = None
        self.current_function = None
        
        # Collected relationships for batch processing
        self.relationships: List[CodeRelationship] = []
        
    def visit_Import(self, node):
        """Extract import statements: import module"""
        for alias in node.names:
            imported_module = alias.name
            relationship = CodeRelationship(
                relationship_type='import',
                source_component_id=None,  # Will be resolved later
                target_component_id=None,
                source_file=self.file_path,
                target_file=None,
                source_name=self.module_name,
                target_name=imported_module,
                line_number=node.lineno,
                metadata={
                    'import_type': 'import',
                    'alias': alias.asname,
                    'imported_item': None
                }
            )
            self.relationships.append(relationship)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Extract from imports: from module import item"""
        if node.module:
            for alias in node.names:
                relationship = CodeRelationship(
                    relationship_type='import',
                    source_component_id=None,
                    target_component_id=None,
                    source_file=self.file_path,
                    target_file=None,
                    source_name=self.module_name,
                    target_name=node.module,
                    line_number=node.lineno,
                    metadata={
                        'import_type': 'from_import',
                        'imported_item': alias.name,
                        'alias': alias.asname,
                        'level': node.level  # For relative imports
                    }
                )
                self.relationships.append(relationship)
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        """Extract class definitions and inheritance"""
        old_class = self.current_class
        self.current_class = node.name
        
        # Extract inheritance relationships
        for base in node.bases:
            base_name = self._get_name_from_node(base)
            if base_name:
                relationship = CodeRelationship(
                    relationship_type='inheritance',
                    source_component_id=None,
                    target_component_id=None,
                    source_file=self.file_path,
                    target_file=None,
                    source_name=node.name,
                    target_name=base_name,
                    line_number=node.lineno,
                    metadata={
                        'child_class': node.name,
                        'child_module': self.module_name,
                        'parent_class': base_name,
                        'is_interface': 'ABC' in base_name or 'Protocol' in base_name
                    }
                )
                self.relationships.append(relationship)
        
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_FunctionDef(self, node):
        """Extract function definitions and track context"""
        old_function = self.current_function
        self.current_function = node.name
        
        self.generic_visit(node)
        self.current_function = old_function
    
    def visit_AsyncFunctionDef(self, node):
        """Handle async functions same as regular functions"""
        self.visit_FunctionDef(node)
    
    def visit_Call(self, node):
        """Extract function/method calls"""
        called_name = self._get_name_from_node(node.func)
        
        if called_name and self.current_function:
            # Determine if it's a method call or function call
            if isinstance(node.func, ast.Attribute):
                # Method call: obj.method()
                obj_name = self._get_name_from_node(node.func.value)
                relationship = CodeRelationship(
                    relationship_type='method_call',
                    source_component_id=None,
                    target_component_id=None,
                    source_file=self.file_path,
                    target_file=None,
                    source_name=self.current_function,
                    target_name=called_name,
                    line_number=node.lineno,
                    metadata={
                        'caller_function': self.current_function,
                        'caller_class': self.current_class,
                        'caller_module': self.module_name,
                        'called_function': called_name,
                        'called_object': obj_name,
                        'call_type': 'method_call'
                    }
                )
            else:
                # Function call: function()
                relationship = CodeRelationship(
                    relationship_type='function_call',
                    source_component_id=None,
                    target_component_id=None,
                    source_file=self.file_path,
                    target_file=None,
                    source_name=self.current_function,
                    target_name=called_name,
                    line_number=node.lineno,
                    metadata={
                        'caller_function': self.current_function,
                        'caller_class': self.current_class,
                        'caller_module': self.module_name,
                        'called_function': called_name,
                        'call_type': 'function_call'
                    }
                )
            
            self.relationships.append(relationship)
        
        self.generic_visit(node)
    
    def visit_Assign(self, node):
        """Extract variable assignments and class instantiation"""
        # Track when classes are instantiated
        if isinstance(node.value, ast.Call):
            class_name = self._get_name_from_node(node.value.func)
            if class_name and self.current_function:
                relationship = CodeRelationship(
                    relationship_type='class_usage',
                    source_component_id=None,
                    target_component_id=None,
                    source_file=self.file_path,
                    target_file=None,
                    source_name=self.current_function,
                    target_name=class_name,
                    line_number=node.lineno,
                    metadata={
                        'using_function': self.current_function,
                        'using_class': self.current_class,
                        'using_module': self.module_name,
                        'used_class': class_name,
                        'usage_type': 'instantiation'
                    }
                )
                self.relationships.append(relationship)
        
        self.generic_visit(node)
    
    def visit_AnnAssign(self, node):
        """Extract type annotations"""
        if node.annotation:
            type_name = self._get_name_from_node(node.annotation)
            if type_name and self.current_function:
                relationship = CodeRelationship(
                    relationship_type='class_usage',
                    source_component_id=None,
                    target_component_id=None,
                    source_file=self.file_path,
                    target_file=None,
                    source_name=self.current_function,
                    target_name=type_name,
                    line_number=node.lineno,
                    metadata={
                        'using_function': self.current_function,
                        'using_class': self.current_class,
                        'using_module': self.module_name,
                        'used_class': type_name,
                        'usage_type': 'type_annotation'
                    }
                )
                self.relationships.append(relationship)
        
        self.generic_visit(node)
    
    def _get_name_from_node(self, node) -> Optional[str]:
        """Extract name from various AST node types"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            base = self._get_name_from_node(node.value)
            return f"{base}.{node.attr}" if base else node.attr
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None
    
    def store_relationships_in_postgres(self) -> bool:
        """
        Store relationship metadata in PostgreSQL for fast querying.
        Based on pseudocode Section 5, lines 395-409.
        """
        if not self.postgres_client or not self.relationships:
            return False
        
        try:
            for rel in self.relationships:
                self.postgres_client.execute_query(
                    """
                    INSERT INTO code_relationships (
                        relationship_type, source_component_id, target_component_id,
                        source_file, target_file, source_name, target_name,
                        line_number, metadata, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        rel.relationship_type,
                        rel.source_component_id,
                        rel.target_component_id,
                        rel.source_file,
                        rel.target_file,
                        rel.source_name,
                        rel.target_name,
                        rel.line_number,
                        json.dumps(rel.metadata),
                        datetime.now()
                    )
                )
            
            logger.info(f"Stored {len(self.relationships)} relationships in PostgreSQL")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store relationships in PostgreSQL: {e}")
            return False
    
    def create_neo4j_relationships(self) -> bool:
        """
        Create graph relationships in Neo4j.
        Based on pseudocode Section 5, lines 411-449.
        """
        if not self.neo4j_client or not self.relationships:
            return False
        
        try:
            for rel in self.relationships:
                if rel.relationship_type == 'import':
                    query = self._generate_import_cypher(rel)
                elif rel.relationship_type == 'function_call':
                    query = self._generate_function_call_cypher(rel)
                elif rel.relationship_type == 'method_call':
                    query = self._generate_method_call_cypher(rel)
                elif rel.relationship_type == 'inheritance':
                    query = self._generate_inheritance_cypher(rel)
                elif rel.relationship_type == 'class_usage':
                    query = self._generate_class_usage_cypher(rel)
                else:
                    continue
                
                self.neo4j_client.execute_query(query)
            
            logger.info(f"Created {len(self.relationships)} relationships in Neo4j")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create Neo4j relationships: {e}")
            return False
    
    def _generate_import_cypher(self, rel: CodeRelationship) -> str:
        """Generate Cypher query for import relationships"""
        return f"""
        MATCH (source:File {{path: '{rel.source_file}'}})
        MERGE (target:File {{module_name: '{rel.target_name}'}})
        MERGE (source)-[:IMPORTS {{
            import_type: '{rel.metadata.get('import_type', '')}',
            imported_item: '{rel.metadata.get('imported_item', '')}',
            alias: '{rel.metadata.get('alias', '')}',
            line_number: {rel.line_number}
        }}]->(target)
        """
    
    def _generate_function_call_cypher(self, rel: CodeRelationship) -> str:
        """Generate Cypher query for function call relationships"""
        return f"""
        MATCH (caller:Function {{name: '{rel.source_name}', module: '{rel.metadata.get('caller_module', '')}'}})
        MERGE (called:Function {{name: '{rel.target_name}'}})
        MERGE (caller)-[:CALLS {{
            line_number: {rel.line_number},
            call_type: '{rel.metadata.get('call_type', '')}'
        }}]->(called)
        """
    
    def _generate_method_call_cypher(self, rel: CodeRelationship) -> str:
        """Generate Cypher query for method call relationships"""
        return f"""
        MATCH (caller:Method {{name: '{rel.source_name}', class: '{rel.metadata.get('caller_class', '')}'}})
        MERGE (called:Method {{name: '{rel.target_name}'}})
        MERGE (caller)-[:CALLS {{
            line_number: {rel.line_number},
            called_object: '{rel.metadata.get('called_object', '')}',
            call_type: '{rel.metadata.get('call_type', '')}'
        }}]->(called)
        """
    
    def _generate_inheritance_cypher(self, rel: CodeRelationship) -> str:
        """Generate Cypher query for inheritance relationships"""
        return f"""
        MATCH (child:Class {{name: '{rel.source_name}', module: '{rel.metadata.get('child_module', '')}'}})
        MERGE (parent:Class {{name: '{rel.target_name}'}})
        MERGE (child)-[:INHERITS_FROM {{
            line_number: {rel.line_number},
            is_interface: {str(rel.metadata.get('is_interface', False)).lower()}
        }}]->(parent)
        """
    
    def _generate_class_usage_cypher(self, rel: CodeRelationship) -> str:
        """Generate Cypher query for class usage relationships"""
        if rel.metadata.get('using_class'):
            # Method uses class
            return f"""
            MATCH (user:Method {{name: '{rel.source_name}', class: '{rel.metadata.get('using_class', '')}'}})
            MERGE (used:Class {{name: '{rel.target_name}'}})
            MERGE (user)-[:USES {{
                usage_type: '{rel.metadata.get('usage_type', '')}',
                line_number: {rel.line_number}
            }}]->(used)
            """
        else:
            # Function uses class
            return f"""
            MATCH (user:Function {{name: '{rel.source_name}', module: '{rel.metadata.get('using_module', '')}'}})
            MERGE (used:Class {{name: '{rel.target_name}'}})
            MERGE (user)-[:USES {{
                usage_type: '{rel.metadata.get('usage_type', '')}',
                line_number: {rel.line_number}
            }}]->(used)
            """

def extract_relationships_from_file(file_path: str, postgres_client=None, neo4j_client=None) -> Optional[RelationshipExtractor]:
    """
    Extract all relationships from a single Python file.
    Adapted from MCP ast_dependency_extraction.py extract_dependencies_from_file().
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=file_path)
        
        # Determine module name from file path
        module_name = Path(file_path).stem
        
        extractor = RelationshipExtractor(file_path, module_name, postgres_client, neo4j_client)
        extractor.visit(tree)
        
        return extractor
    
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return None

def extract_relationships_from_directory(directory: str, postgres_client=None, neo4j_client=None) -> List[RelationshipExtractor]:
    """
    Extract relationships from all Python files in a directory.
    Adapted from MCP ast_dependency_extraction.py extract_dependencies_from_directory().
    """
    extractors = []
    
    for file_path in Path(directory).rglob("*.py"):
        extractor = extract_relationships_from_file(str(file_path), postgres_client, neo4j_client)
        if extractor:
            extractors.append(extractor)
    
    return extractors

def batch_store_relationships(extractors: List[RelationshipExtractor]) -> Dict[str, int]:
    """
    Batch store all relationships in both PostgreSQL and Neo4j.
    Returns statistics about stored relationships.
    """
    stats = {
        'postgres_success': 0,
        'postgres_failed': 0,
        'neo4j_success': 0,
        'neo4j_failed': 0,
        'total_relationships': 0
    }
    
    for extractor in extractors:
        stats['total_relationships'] += len(extractor.relationships)
        
        # Store in PostgreSQL
        if extractor.store_relationships_in_postgres():
            stats['postgres_success'] += len(extractor.relationships)
        else:
            stats['postgres_failed'] += len(extractor.relationships)
        
        # Create in Neo4j
        if extractor.create_neo4j_relationships():
            stats['neo4j_success'] += len(extractor.relationships)
        else:
            stats['neo4j_failed'] += len(extractor.relationships)
    
    return stats