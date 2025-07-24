"""
Relationship type definitions for code relationships.

Defines standardized relationship types that can exist between
code elements in the knowledge graph.
"""

from enum import Enum
from typing import Dict, Any, Set, Optional
from dataclasses import dataclass


class RelationshipType(Enum):
    """Standardized relationship types for code elements."""
    
    # Structural relationships
    IMPORTS = "IMPORTS"                   # Module imports another module
    CONTAINS = "CONTAINS"                 # Module contains class/function/variable
    DEFINES = "DEFINES"                   # Class defines method/attribute
    HAS_METHOD = "HAS_METHOD"            # Class has method
    HAS_ATTRIBUTE = "HAS_ATTRIBUTE"      # Class has attribute
    
    # Behavioral relationships  
    CALLS = "CALLS"                      # Function calls another function
    INVOKES = "INVOKES"                  # Method invokes another method
    USES = "USES"                        # Code element uses another element
    INSTANTIATES = "INSTANTIATES"        # Creates instance of class
    
    # Hierarchical relationships
    INHERITS_FROM = "INHERITS_FROM"      # Class inherits from another class
    EXTENDS = "EXTENDS"                  # Class extends another class
    IMPLEMENTS = "IMPLEMENTS"            # Class implements interface
    OVERRIDES = "OVERRIDES"              # Method overrides parent method
    
    # Type relationships
    HAS_TYPE = "HAS_TYPE"               # Variable has type
    RETURNS = "RETURNS"                  # Function returns type
    ACCEPTS = "ACCEPTS"                  # Function accepts parameter type
    
    # Dependency relationships
    DEPENDS_ON = "DEPENDS_ON"           # General dependency
    IMPORTS_FROM = "IMPORTS_FROM"       # Specific import from module
    
    # Semantic relationships (via embeddings)
    SIMILAR_TO = "SIMILAR_TO"           # Semantically similar elements
    RELATED_TO = "RELATED_TO"           # Related code elements


@dataclass
class RelationshipDefinition:
    """
    Definition of a relationship type with metadata.
    
    Provides additional information about how relationships
    should be created and what properties they should have.
    """
    relationship_type: RelationshipType
    source_labels: Set[str]              # Valid source node labels
    target_labels: Set[str]              # Valid target node labels
    description: str                     # Human-readable description
    properties: Dict[str, type]          # Expected relationship properties
    bidirectional: bool = False          # Whether relationship works both ways
    
    def is_valid_connection(self, source_label: str, target_label: str) -> bool:
        """Check if connection between labels is valid for this relationship."""
        return (source_label in self.source_labels and 
                target_label in self.target_labels)


# Relationship definitions registry
RELATIONSHIP_DEFINITIONS: Dict[RelationshipType, RelationshipDefinition] = {
    
    RelationshipType.IMPORTS: RelationshipDefinition(
        relationship_type=RelationshipType.IMPORTS,
        source_labels={"Module"},
        target_labels={"Module"},
        description="Module imports another module",
        properties={
            "import_name": str,
            "asname": str,
            "fromname": str,
            "is_star": bool,
            "line_start": int,
            "line_end": int
        }
    ),
    
    RelationshipType.CONTAINS: RelationshipDefinition(
        relationship_type=RelationshipType.CONTAINS,
        source_labels={"Module", "Class"},
        target_labels={"Class", "Function", "Method", "Variable"},
        description="Container contains code element",
        properties={
            "line_start": int,
            "line_end": int
        }
    ),
    
    RelationshipType.INHERITS_FROM: RelationshipDefinition(
        relationship_type=RelationshipType.INHERITS_FROM,
        source_labels={"Class"},
        target_labels={"Class"},
        description="Class inherits from another class",
        properties={
            "inheritance_order": int,
            "line_number": int
        }
    ),
    
    RelationshipType.CALLS: RelationshipDefinition(
        relationship_type=RelationshipType.CALLS,
        source_labels={"Function", "Method"},
        target_labels={"Function", "Method"},
        description="Function or method calls another function/method",
        properties={
            "call_type": str,  # direct, indirect, conditional
            "line_number": int,
            "arguments_count": int
        }
    ),
    
    RelationshipType.HAS_METHOD: RelationshipDefinition(
        relationship_type=RelationshipType.HAS_METHOD,
        source_labels={"Class"},
        target_labels={"Method"},
        description="Class has method",
        properties={
            "visibility": str,  # public, private, protected
            "is_static": bool,
            "is_class_method": bool,
            "is_property": bool
        }
    ),
    
    RelationshipType.HAS_TYPE: RelationshipDefinition(
        relationship_type=RelationshipType.HAS_TYPE,
        source_labels={"Variable", "Function", "Method"},
        target_labels={"Class"},
        description="Element has type annotation",
        properties={
            "type_string": str,
            "is_inferred": bool,
            "confidence": float
        }
    ),
    
    RelationshipType.USES: RelationshipDefinition(
        relationship_type=RelationshipType.USES,
        source_labels={"Function", "Method", "Class"},
        target_labels={"Class", "Function", "Method", "Variable"},
        description="Code element uses another element",
        properties={
            "usage_type": str,  # instantiation, access, modification
            "line_number": int,
            "context": str
        }
    ),
    
    RelationshipType.SIMILAR_TO: RelationshipDefinition(
        relationship_type=RelationshipType.SIMILAR_TO,
        source_labels={"Function", "Method", "Class"},
        target_labels={"Function", "Method", "Class"},
        description="Elements are semantically similar",
        properties={
            "similarity_score": float,
            "similarity_method": str,  # embedding, structural, behavioral
            "computed_at": str
        },
        bidirectional=True
    )
}


def get_relationship_definition(relationship_type: RelationshipType) -> Optional[RelationshipDefinition]:
    """Get the definition for a relationship type."""
    return RELATIONSHIP_DEFINITIONS.get(relationship_type)


def validate_relationship(
    relationship_type: RelationshipType,
    source_label: str,
    target_label: str
) -> bool:
    """Validate that a relationship can exist between source and target labels."""
    definition = get_relationship_definition(relationship_type)
    if not definition:
        return False
    return definition.is_valid_connection(source_label, target_label)


def get_valid_relationships_for_labels(
    source_label: str,
    target_label: str
) -> Set[RelationshipType]:
    """Get all valid relationship types between two node labels."""
    valid_relationships = set()
    for rel_type, definition in RELATIONSHIP_DEFINITIONS.items():
        if definition.is_valid_connection(source_label, target_label):
            valid_relationships.add(rel_type)
    return valid_relationships