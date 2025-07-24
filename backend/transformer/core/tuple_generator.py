"""
Neo4j tuple generation from parsed code elements.

Converts ParsedModule, ParsedClass, ParsedFunction, etc. from Phase 1
into standardized Neo4j tuples for Phase 3 upload.
"""

import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

from ..models.tuples import Neo4jNodeTuple, Neo4jRelationshipTuple, TupleSet, NodeLabel
from ..models.relationships import RelationshipType, validate_relationship

logger = logging.getLogger(__name__)


class TupleGenerator:
    """
    Generates Neo4j tuples from parsed code elements.
    
    This class converts the output from Phase 1 extraction into
    standardized tuple formats ready for Neo4j upload in Phase 3.
    """
    
    def __init__(self):
        """Initialize the tuple generator."""
        self.generated_keys: Set[str] = set()
        self.relationship_cache: Dict[str, Neo4jRelationshipTuple] = {}
        
    def generate_module_tuples(self, module_path: str, module_data: Dict[str, Any]) -> TupleSet:
        """
        Generate tuples for a complete module.
        
        Args:
            module_path: File path of the module
            module_data: Parsed module data from Phase 1
            
        Returns:
            TupleSet containing all nodes and relationships for the module
        """
        tuple_set = TupleSet()
        
        try:
            # Generate module node
            module_node = self._create_module_node(module_path, module_data)
            tuple_set.add_node(module_node)
            
            # Generate import relationships
            for import_data in module_data.get("imports", []):
                import_rel = self._create_import_relationship(module_path, import_data)
                if import_rel:
                    tuple_set.add_relationship(import_rel)
            
            # Generate class nodes and relationships
            for class_data in module_data.get("classes", []):
                class_tuples = self._create_class_tuples(module_path, class_data)
                tuple_set = tuple_set.merge(class_tuples)
                
            # Generate function nodes and relationships  
            for function_data in module_data.get("functions", []):
                function_tuples = self._create_function_tuples(module_path, function_data)
                tuple_set = tuple_set.merge(function_tuples)
                
            # Generate variable nodes and relationships
            for variable_data in module_data.get("variables", []):
                variable_tuples = self._create_variable_tuples(module_path, variable_data)
                tuple_set = tuple_set.merge(variable_tuples)
                
            # Add metadata
            tuple_set.metadata = {
                "module_path": module_path,
                "module_name": module_data.get("name", ""),
                "generated_at": datetime.utcnow().isoformat(),
                "line_count": module_data.get("line_count", 0)
            }
            
            logger.debug(f"Generated {tuple_set.size} tuples for module: {module_path}")
            return tuple_set
            
        except Exception as e:
            logger.error(f"Failed to generate tuples for module {module_path}: {e}")
            raise
    
    def _create_module_node(self, module_path: str, module_data: Dict[str, Any]) -> Neo4jNodeTuple:
        """Create a Module node tuple."""
        unique_key = f"module:{module_path}"
        
        properties = {
            "path": module_path,
            "name": module_data.get("name", ""),
            "line_count": module_data.get("line_count", 0),
            "size_bytes": module_data.get("size_bytes", 0),
            "last_modified": module_data.get("last_modified", ""),
            "docstring": module_data.get("docstring", "")
        }
        
        return Neo4jNodeTuple(
            label=NodeLabel.MODULE.value,
            properties=properties,
            unique_key=unique_key,
            merge_properties={"path"}
        )
    
    def _create_import_relationship(
        self, 
        module_path: str, 
        import_data: Dict[str, Any]
    ) -> Optional[Neo4jRelationshipTuple]:
        """Create an IMPORTS relationship tuple."""
        try:
            source_key = f"module:{module_path}"
            
            # Determine target module
            target_module = import_data.get("fromname") or import_data.get("name", "")
            if not target_module:
                logger.warning(f"Empty import target in {module_path}")
                return None
                
            target_key = f"module:{target_module}"
            
            properties = {
                "import_name": import_data.get("name", ""),
                "asname": import_data.get("asname", ""),
                "fromname": import_data.get("fromname", ""),
                "is_star": import_data.get("is_star", False),
                "line_start": import_data.get("line_start", 0),
                "line_end": import_data.get("line_end", 0)
            }
            
            return Neo4jRelationshipTuple(
                source_key=source_key,
                target_key=target_key,
                relationship_type=RelationshipType.IMPORTS.value,
                properties=properties,
                source_label=NodeLabel.MODULE.value,
                target_label=NodeLabel.MODULE.value
            )
            
        except Exception as e:
            logger.warning(f"Failed to create import relationship: {e}")
            return None
    
    def _create_class_tuples(self, module_path: str, class_data: Dict[str, Any]) -> TupleSet:
        """Create tuples for a class and its relationships."""
        tuple_set = TupleSet()
        class_name = class_data.get("name", "")
        
        if not class_name:
            logger.warning(f"Empty class name in {module_path}")
            return tuple_set
            
        # Create class node
        class_unique_key = f"class:{module_path}:{class_name}"
        class_properties = {
            "name": class_name,
            "module_path": module_path,
            "docstring": class_data.get("docstring", ""),
            "line_start": class_data.get("line_start", 0),
            "line_end": class_data.get("line_end", 0),
            "decorators": class_data.get("decorators", [])
        }
        
        class_node = Neo4jNodeTuple(
            label=NodeLabel.CLASS.value,
            properties=class_properties,
            unique_key=class_unique_key,
            merge_properties={"name", "module_path"}
        )
        tuple_set.add_node(class_node)
        
        # Create CONTAINS relationship from module to class
        module_key = f"module:{module_path}"
        contains_rel = Neo4jRelationshipTuple(
            source_key=module_key,
            target_key=class_unique_key,
            relationship_type=RelationshipType.CONTAINS.value,
            properties={
                "line_start": class_data.get("line_start", 0),
                "line_end": class_data.get("line_end", 0)
            },
            source_label=NodeLabel.MODULE.value,
            target_label=NodeLabel.CLASS.value
        )
        tuple_set.add_relationship(contains_rel)
        
        # Create inheritance relationships
        for base_class in class_data.get("bases", []):
            inheritance_rel = self._create_inheritance_relationship(
                module_path, class_name, base_class
            )
            if inheritance_rel:
                tuple_set.add_relationship(inheritance_rel)
        
        # Process methods
        for method_data in class_data.get("methods", []):
            method_tuples = self._create_method_tuples(module_path, class_name, method_data)
            tuple_set = tuple_set.merge(method_tuples)
        
        return tuple_set
    
    def _create_inheritance_relationship(
        self, 
        module_path: str, 
        child_class: str, 
        parent_class: str
    ) -> Optional[Neo4jRelationshipTuple]:
        """Create an INHERITS_FROM relationship tuple."""
        try:
            child_key = f"class:{module_path}:{child_class}"
            parent_key = f"class:{parent_class}"  # May be from different module
            
            return Neo4jRelationshipTuple(
                source_key=child_key,
                target_key=parent_key,
                relationship_type=RelationshipType.INHERITS_FROM.value,
                properties={
                    "inheritance_order": 0,  # TODO: Extract actual order
                    "line_number": 0  # TODO: Extract line number
                },
                source_label=NodeLabel.CLASS.value,
                target_label=NodeLabel.CLASS.value
            )
        except Exception as e:
            logger.warning(f"Failed to create inheritance relationship: {e}")
            return None
    
    def _create_method_tuples(
        self, 
        module_path: str, 
        class_name: str, 
        method_data: Dict[str, Any]
    ) -> TupleSet:
        """Create tuples for a method."""
        tuple_set = TupleSet()
        method_name = method_data.get("name", "")
        
        if not method_name:
            logger.warning(f"Empty method name in {class_name}")
            return tuple_set
        
        # Create method node
        method_unique_key = f"method:{module_path}:{class_name}:{method_name}"
        method_properties = {
            "name": method_name,
            "class_name": class_name,
            "module_path": module_path,
            "signature": method_data.get("signature", ""),
            "docstring": method_data.get("docstring", ""),
            "line_start": method_data.get("line_start", 0),
            "line_end": method_data.get("line_end", 0),
            "decorators": method_data.get("decorators", []),
            "is_static": method_data.get("is_static", False),
            "is_class_method": method_data.get("is_class_method", False),
            "return_type": method_data.get("return_type", "")
        }
        
        method_node = Neo4jNodeTuple(
            label=NodeLabel.METHOD.value,
            properties=method_properties,
            unique_key=method_unique_key,
            merge_properties={"name", "class_name", "module_path"}
        )
        tuple_set.add_node(method_node)
        
        # Create HAS_METHOD relationship from class to method
        class_key = f"class:{module_path}:{class_name}"
        has_method_rel = Neo4jRelationshipTuple(
            source_key=class_key,
            target_key=method_unique_key,
            relationship_type=RelationshipType.HAS_METHOD.value,
            properties={
                "visibility": "public",  # TODO: Detect visibility
                "is_static": method_data.get("is_static", False),
                "is_class_method": method_data.get("is_class_method", False),
                "is_property": False  # TODO: Detect properties
            },
            source_label=NodeLabel.CLASS.value,
            target_label=NodeLabel.METHOD.value
        )
        tuple_set.add_relationship(has_method_rel)
        
        return tuple_set
    
    def _create_function_tuples(self, module_path: str, function_data: Dict[str, Any]) -> TupleSet:
        """Create tuples for a module-level function."""
        tuple_set = TupleSet()
        function_name = function_data.get("name", "")
        
        if not function_name:
            logger.warning(f"Empty function name in {module_path}")
            return tuple_set
        
        # Create function node
        function_unique_key = f"function:{module_path}:{function_name}"
        function_properties = {
            "name": function_name,
            "module_path": module_path,
            "signature": function_data.get("signature", ""),
            "docstring": function_data.get("docstring", ""),
            "line_start": function_data.get("line_start", 0),
            "line_end": function_data.get("line_end", 0),
            "decorators": function_data.get("decorators", []),
            "return_type": function_data.get("return_type", "")
        }
        
        function_node = Neo4jNodeTuple(
            label=NodeLabel.FUNCTION.value,
            properties=function_properties,
            unique_key=function_unique_key,
            merge_properties={"name", "module_path"}
        )
        tuple_set.add_node(function_node)
        
        # Create CONTAINS relationship from module to function
        module_key = f"module:{module_path}"
        contains_rel = Neo4jRelationshipTuple(
            source_key=module_key,
            target_key=function_unique_key,
            relationship_type=RelationshipType.CONTAINS.value,
            properties={
                "line_start": function_data.get("line_start", 0),
                "line_end": function_data.get("line_end", 0)
            },
            source_label=NodeLabel.MODULE.value,
            target_label=NodeLabel.FUNCTION.value
        )
        tuple_set.add_relationship(contains_rel)
        
        return tuple_set
    
    def _create_variable_tuples(self, module_path: str, variable_data: Dict[str, Any]) -> TupleSet:
        """Create tuples for a variable."""
        tuple_set = TupleSet()
        variable_name = variable_data.get("name", "")
        
        if not variable_name:
            logger.warning(f"Empty variable name in {module_path}")
            return tuple_set
        
        # Create variable node
        variable_unique_key = f"variable:{module_path}:{variable_name}"
        variable_properties = {
            "name": variable_name,
            "module_path": module_path,
            "inferred_type": variable_data.get("inferred_type", ""),
            "value_repr": variable_data.get("value_repr", ""),
            "line_start": variable_data.get("line_start", 0),
            "line_end": variable_data.get("line_end", 0),
            "is_class_var": variable_data.get("is_class_var", False),
            "is_constant": variable_data.get("is_constant", False),
            "scope": variable_data.get("scope", "module")
        }
        
        variable_node = Neo4jNodeTuple(
            label=NodeLabel.VARIABLE.value,
            properties=variable_properties,
            unique_key=variable_unique_key,
            merge_properties={"name", "module_path"}
        )
        tuple_set.add_node(variable_node)
        
        # Create CONTAINS relationship from module to variable
        module_key = f"module:{module_path}"
        contains_rel = Neo4jRelationshipTuple(
            source_key=module_key,
            target_key=variable_unique_key,
            relationship_type=RelationshipType.CONTAINS.value,
            properties={
                "line_start": variable_data.get("line_start", 0),
                "line_end": variable_data.get("line_end", 0)
            },
            source_label=NodeLabel.MODULE.value,
            target_label=NodeLabel.VARIABLE.value
        )
        tuple_set.add_relationship(contains_rel)
        
        return tuple_set
    
    def clear_cache(self) -> None:
        """Clear internal caches."""
        self.generated_keys.clear()
        self.relationship_cache.clear()