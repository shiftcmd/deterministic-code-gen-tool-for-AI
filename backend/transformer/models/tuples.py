"""
Neo4j tuple definitions for transformation output.

Defines standardized tuple formats for nodes and relationships
that will be consumed by Phase 3 (Neo4j upload domain).
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from enum import Enum


class NodeLabel(Enum):
    """Neo4j node labels."""
    MODULE = "Module"
    CLASS = "Class"
    FUNCTION = "Function"
    METHOD = "Method"
    VARIABLE = "Variable"
    IMPORT = "Import"


@dataclass
class Neo4jNodeTuple:
    """
    Standardized node tuple for Neo4j upload.
    
    This represents a single node that will be created in Neo4j
    with MERGE operations to ensure uniqueness.
    """
    label: str                           # Node label (Module, Class, Function, etc.)
    properties: Dict[str, Any]           # Node properties
    unique_key: str                      # Unique identifier for MERGE operations
    merge_properties: Set[str] = field(default_factory=set)  # Properties used in MERGE
    
    def __post_init__(self):
        """Validate the tuple after initialization."""
        if not self.label:
            raise ValueError("Node label cannot be empty")
        if not self.unique_key:
            raise ValueError("Unique key cannot be empty")
        if not self.properties:
            self.properties = {}
            
    def to_cypher_params(self) -> Dict[str, Any]:
        """Convert to Cypher parameters format."""
        return {
            "label": self.label,
            "unique_key": self.unique_key,
            "properties": self.properties,
            "merge_properties": list(self.merge_properties) if self.merge_properties else ["unique_key"]
        }


@dataclass 
class Neo4jRelationshipTuple:
    """
    Standardized relationship tuple for Neo4j upload.
    
    This represents a relationship between two nodes in Neo4j.
    """
    source_key: str                      # Source node unique key
    target_key: str                      # Target node unique key
    relationship_type: str               # Relationship label
    properties: Dict[str, Any] = field(default_factory=dict)  # Relationship properties
    source_label: Optional[str] = None   # Source node label (for optimization)
    target_label: Optional[str] = None   # Target node label (for optimization)
    
    def __post_init__(self):
        """Validate the tuple after initialization."""
        if not self.source_key:
            raise ValueError("Source key cannot be empty")
        if not self.target_key:
            raise ValueError("Target key cannot be empty") 
        if not self.relationship_type:
            raise ValueError("Relationship type cannot be empty")
            
    def to_cypher_params(self) -> Dict[str, Any]:
        """Convert to Cypher parameters format."""
        return {
            "source_key": self.source_key,
            "target_key": self.target_key,
            "relationship_type": self.relationship_type,
            "properties": self.properties,
            "source_label": self.source_label,
            "target_label": self.target_label
        }


@dataclass
class TupleSet:
    """
    Collection of nodes and relationships for batch processing.
    
    This represents a complete set of tuples generated from
    transformation processing, ready for Neo4j upload.
    """
    nodes: List[Neo4jNodeTuple] = field(default_factory=list)
    relationships: List[Neo4jRelationshipTuple] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_node(self, node: Neo4jNodeTuple) -> None:
        """Add a node tuple to the set."""
        self.nodes.append(node)
        
    def add_relationship(self, relationship: Neo4jRelationshipTuple) -> None:
        """Add a relationship tuple to the set."""
        self.relationships.append(relationship)
        
    def merge(self, other: 'TupleSet') -> 'TupleSet':
        """Merge another TupleSet into this one."""
        merged = TupleSet(
            nodes=self.nodes + other.nodes,
            relationships=self.relationships + other.relationships,
            metadata={**self.metadata, **other.metadata}
        )
        return merged
        
    @property
    def size(self) -> int:
        """Total number of tuples in the set."""
        return len(self.nodes) + len(self.relationships)
        
    @property
    def node_count(self) -> int:
        """Number of node tuples."""
        return len(self.nodes)
        
    @property
    def relationship_count(self) -> int:
        """Number of relationship tuples."""
        return len(self.relationships)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for serialization."""
        return {
            "nodes": [node.to_cypher_params() for node in self.nodes],
            "relationships": [rel.to_cypher_params() for rel in self.relationships],
            "metadata": self.metadata,
            "statistics": {
                "node_count": self.node_count,
                "relationship_count": self.relationship_count,
                "total_size": self.size
            }
        }