"""
Transformation Domain - Phase 2 of Parser Refactor

This domain handles the transformation of raw extraction data from Phase 1
into standardized tuples and data structures ready for Neo4j upload in Phase 3.

Key Components:
- Core transformation logic
- Tuple generation for Neo4j
- Relationship mapping
- Multiple output formatters
- Progress reporting and validation
"""

from .models.tuples import Neo4jNodeTuple, Neo4jRelationshipTuple
from .models.relationships import RelationshipType

__version__ = "2.0.0"
__all__ = [
    "Neo4jNodeTuple", 
    "Neo4jRelationshipTuple",
    "RelationshipType"
]