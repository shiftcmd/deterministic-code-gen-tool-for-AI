"""
Core domain models for code components and their relationships.

This module contains the CodeComponent entity and related value objects
that represent analyzed code elements in the hexagonal architecture tagging system.
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator

from .tag import Tag, TagCollection


class ComponentType(str, Enum):
    """Types of code components that can be analyzed."""

    CODEBASE = "codebase"
    MODULE = "module"
    FILE = "file"
    CLASS = "class"
    METHOD = "method"
    FUNCTION = "function"
    PROPERTY = "property"
    CONSTANT = "constant"
    VARIABLE = "variable"
    INTERFACE = "interface"
    ENUM = "enum"


class RelationshipType(str, Enum):
    """Types of relationships between code components."""

    # Structural relationships
    CONTAINS = "CONTAINS"
    DEFINES = "DEFINES"
    DECLARES = "DECLARES"
    HAS_METHOD = "HAS_METHOD"
    HAS_PROPERTY = "HAS_PROPERTY"
    HAS_ATTRIBUTE = "HAS_ATTRIBUTE"

    # Inheritance relationships
    INHERITS_FROM = "INHERITS_FROM"
    IMPLEMENTS = "IMPLEMENTS"
    EXTENDS = "EXTENDS"

    # Composition relationships
    COMPOSES = "COMPOSES"
    AGGREGATES = "AGGREGATES"

    # Behavioral relationships
    CALLS = "CALLS"
    INVOKES = "INVOKES"
    USES = "USES"
    DEPENDS_ON = "DEPENDS_ON"
    REQUIRES = "REQUIRES"
    PROVIDES = "PROVIDES"
    CONSUMES = "CONSUMES"
    PRODUCES = "PRODUCES"
    TRANSFORMS = "TRANSFORMS"
    VALIDATES = "VALIDATES"

    # Architectural relationships
    ADAPTS = "ADAPTS"
    ORCHESTRATES = "ORCHESTRATES"
    COORDINATES = "COORDINATES"
    MANAGES = "MANAGES"
    CONTROLS = "CONTROLS"
    MONITORS = "MONITORS"
    CONFIGURES = "CONFIGURES"
    SECURES = "SECURES"
    CACHES = "CACHES"
    PERSISTS = "PERSISTS"

    # Port-Adapter relationships
    ACCEPTS = "ACCEPTS"
    SENDS_TO = "SENDS_TO"
    ROUTES_TO = "ROUTES_TO"
    HANDLES = "HANDLES"
    PUBLISHES = "PUBLISHES"
    SUBSCRIBES_TO = "SUBSCRIBES_TO"
    CONNECTS_TO = "CONNECTS_TO"
    WRAPS = "WRAPS"

    # Data flow relationships
    READS_FROM = "READS_FROM"
    WRITES_TO = "WRITES_TO"
    FLOWS_TO = "FLOWS_TO"
    PROCESSES = "PROCESSES"
    ENRICHES = "ENRICHES"
    FILTERS = "FILTERS"
    AGGREGATES_FROM = "AGGREGATES_FROM"
    MAPS_TO = "MAPS_TO"

    # Event relationships
    TRIGGERS = "TRIGGERS"
    RESPONDS_TO = "RESPONDS_TO"
    LISTENS_TO = "LISTENS_TO"
    EMITS = "EMITS"
    HANDLES_EVENT = "HANDLES_EVENT"
    PROPAGATES = "PROPAGATES"


class Relationship(BaseModel):
    """
    Value object representing a relationship between two code components.

    Relationships capture the various ways code components interact,
    depend on each other, or are structurally related.
    """

    id: UUID = Field(
        default_factory=uuid4, description="Unique identifier for this relationship"
    )
    source_id: UUID = Field(..., description="ID of the source component")
    target_id: UUID = Field(..., description="ID of the target component")
    relationship_type: RelationshipType = Field(..., description="Type of relationship")
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Confidence in this relationship"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional relationship metadata"
    )
    tags: TagCollection = Field(
        default_factory=TagCollection,
        description="Tags associated with this relationship",
    )

    class Config:
        frozen = True
        use_enum_values = True

    @validator("confidence")
    def validate_confidence(cls, v: float) -> float:
        """Ensure confidence is within valid range."""
        return max(0.0, min(1.0, v))

    def __hash__(self) -> int:
        """Make Relationship hashable."""
        return hash((self.source_id, self.target_id, self.relationship_type))

    def to_neo4j_properties(self) -> Dict[str, Any]:
        """Convert relationship to Neo4j properties."""
        properties = {
            "id": str(self.id),
            "confidence": self.confidence,
            "relationship_type": self.relationship_type.value,
        }

        # Add metadata
        if self.metadata:
            properties["metadata"] = json.dumps(self.metadata)

        # Add tag information
        if self.tags.tags:
            properties["tags"] = [tag.name for tag in self.tags.tags]
            properties.update(self.tags.to_neo4j_properties())

        return properties


class CodeMetrics(BaseModel):
    """
    Value object containing various metrics about a code component.

    Provides quantitative measures that can be used for analysis,
    quality assessment, and architectural decision making.
    """

    lines_of_code: int = Field(default=0, ge=0, description="Total lines of code")
    cyclomatic_complexity: int = Field(
        default=1, ge=1, description="Cyclomatic complexity measure"
    )
    method_count: int = Field(
        default=0, ge=0, description="Number of methods (for classes)"
    )
    parameter_count: int = Field(
        default=0, ge=0, description="Number of parameters (for methods/functions)"
    )
    dependency_count: int = Field(default=0, ge=0, description="Number of dependencies")
    fan_in: int = Field(
        default=0, ge=0, description="Number of components depending on this one"
    )
    fan_out: int = Field(
        default=0, ge=0, description="Number of components this one depends on"
    )
    depth_of_inheritance: int = Field(
        default=0, ge=0, description="Depth in inheritance hierarchy"
    )

    class Config:
        frozen = True

    @property
    def complexity_score(self) -> float:
        """Calculate a normalized complexity score (0-10)."""
        # Weighted combination of various complexity factors
        weights = {
            "cyclomatic": 0.3,
            "methods": 0.2,
            "dependencies": 0.2,
            "lines": 0.15,
            "parameters": 0.1,
            "inheritance": 0.05,
        }

        # Normalize each metric (rough heuristics)
        normalized = {
            "cyclomatic": min(self.cyclomatic_complexity / 10.0, 1.0),
            "methods": min(self.method_count / 20.0, 1.0),
            "dependencies": min(self.dependency_count / 15.0, 1.0),
            "lines": min(self.lines_of_code / 500.0, 1.0),
            "parameters": min(self.parameter_count / 8.0, 1.0),
            "inheritance": min(self.depth_of_inheritance / 5.0, 1.0),
        }

        # Calculate weighted score
        score = sum(normalized[key] * weights[key] for key in weights)
        return round(score * 10, 2)  # Scale to 0-10

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        return {
            "lines_of_code": self.lines_of_code,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "method_count": self.method_count,
            "parameter_count": self.parameter_count,
            "dependency_count": self.dependency_count,
            "fan_in": self.fan_in,
            "fan_out": self.fan_out,
            "depth_of_inheritance": self.depth_of_inheritance,
            "complexity_score": self.complexity_score,
        }


class CodeComponent(BaseModel):
    """
    Entity representing a code component in the system.

    This is the central entity that represents any analyzable piece of code,
    from entire codebases down to individual methods and properties.
    """

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    name: str = Field(..., description="Name of the component")
    component_type: ComponentType = Field(..., description="Type of component")
    file_path: Optional[str] = Field(
        default=None, description="Path to the file containing this component"
    )
    line_number: Optional[int] = Field(
        default=None, ge=1, description="Line number where component is defined"
    )
    end_line_number: Optional[int] = Field(
        default=None, ge=1, description="Line number where component ends"
    )
    parent_id: Optional[UUID] = Field(
        default=None, description="ID of parent component"
    )

    # Core attributes
    tags: TagCollection = Field(
        default_factory=TagCollection, description="Tags assigned to this component"
    )
    metrics: CodeMetrics = Field(
        default_factory=CodeMetrics, description="Quantitative metrics"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    # Relationships
    relationships: List[Relationship] = Field(
        default_factory=list, description="Relationships to other components"
    )

    # Analysis results
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Confidence in the analysis"
    )
    analysis_timestamp: Optional[str] = Field(
        default=None, description="When this component was last analyzed"
    )

    class Config:
        use_enum_values = True

    @validator("end_line_number")
    def validate_end_line(
        cls, v: Optional[int], values: Dict[str, Any]
    ) -> Optional[int]:
        """Ensure end line is after start line."""
        if (
            v is not None
            and "line_number" in values
            and values["line_number"] is not None
        ):
            if v < values["line_number"]:
                raise ValueError("End line must be after start line")
        return v

    @validator("confidence")
    def validate_confidence(cls, v: float) -> float:
        """Ensure confidence is within valid range."""
        return max(0.0, min(1.0, v))

    def add_tag(self, tag: Tag) -> None:
        """Add a tag to this component."""
        self.tags = self.tags.add(tag)

    def remove_tag(self, tag: Tag) -> None:
        """Remove a tag from this component."""
        self.tags = self.tags.remove(tag)

    def has_tag(self, tag_name: str) -> bool:
        """Check if component has a specific tag."""
        return any(tag.name == tag_name for tag in self.tags.tags)

    def get_tags_by_category(self, category: str) -> Set[Tag]:
        """Get all tags in a specific category."""
        from .tag import TagCategory

        try:
            cat = TagCategory(category)
            return self.tags.get_by_category(cat)
        except ValueError:
            return set()

    def add_relationship(self, relationship: Relationship) -> None:
        """Add a relationship to this component."""
        if relationship not in self.relationships:
            self.relationships.append(relationship)

    def get_relationships_by_type(
        self, relationship_type: RelationshipType
    ) -> List[Relationship]:
        """Get all relationships of a specific type."""
        return [
            rel
            for rel in self.relationships
            if rel.relationship_type == relationship_type
        ]

    def get_outgoing_relationships(self) -> List[Relationship]:
        """Get relationships where this component is the source."""
        return [rel for rel in self.relationships if rel.source_id == self.id]

    def get_incoming_relationships(self) -> List[Relationship]:
        """Get relationships where this component is the target."""
        return [rel for rel in self.relationships if rel.target_id == self.id]

    @property
    def full_path(self) -> str:
        """Get the full path identifier for this component."""
        if self.file_path:
            path = Path(self.file_path).stem
            if self.component_type in [
                ComponentType.CLASS,
                ComponentType.METHOD,
                ComponentType.FUNCTION,
            ]:
                return f"{path}.{self.name}"
            return path
        return self.name

    @property
    def architectural_layer(self) -> Optional[str]:
        """Get the architectural layer this component belongs to."""
        from .tag import TagCategory

        arch_tags = self.get_tags_by_category(TagCategory.ARCHITECTURAL.value)

        # Priority order for architectural layers
        layer_priority = [
            "Core",
            "Domain",
            "Application",
            "Infrastructure",
            "Port",
            "Adapter",
        ]

        for layer in layer_priority:
            if any(tag.name == layer for tag in arch_tags):
                return layer

        return None

    @property
    def primary_role(self) -> Optional[str]:
        """Get the primary role of this component."""
        from .tag import TagCategory

        role_tags = self.get_tags_by_category(TagCategory.ROLE.value)

        if role_tags:
            # Return the first role tag (could be enhanced with priority logic)
            return next(iter(role_tags)).name

        return None

    def to_neo4j_node(self) -> Dict[str, Any]:
        """Convert component to Neo4j node representation."""
        # Get primary labels from tags
        labels = self.tags.to_neo4j_labels()

        # Ensure component type is always a label
        if self.component_type.value.title() not in labels:
            labels.append(self.component_type.value.title())

        # Build properties
        properties = {
            "id": str(self.id),
            "name": self.name,
            "component_type": self.component_type.value,
            "confidence": self.confidence,
        }

        # Add optional properties
        if self.file_path:
            properties["file_path"] = self.file_path
        if self.line_number:
            properties["line_number"] = self.line_number
        if self.end_line_number:
            properties["end_line_number"] = self.end_line_number
        if self.parent_id:
            properties["parent_id"] = str(self.parent_id)
        if self.analysis_timestamp:
            properties["analysis_timestamp"] = self.analysis_timestamp

        # Add metrics
        properties.update(self.metrics.to_dict())

        # Add metadata
        if self.metadata:
            properties["metadata"] = json.dumps(self.metadata)

        # Add tag properties
        properties.update(self.tags.to_neo4j_properties())

        # Add derived properties
        if self.architectural_layer:
            properties["architectural_layer"] = self.architectural_layer
        if self.primary_role:
            properties["primary_role"] = self.primary_role

        properties["full_path"] = self.full_path

        return {"labels": labels, "properties": properties}

    def __str__(self) -> str:
        """String representation of the component."""
        return f"{self.component_type.value}:{self.name}"

    def __hash__(self) -> int:
        """Make CodeComponent hashable."""
        return hash(self.id)
