"""
Core domain models for tags and tag management.

This module contains the fundamental Tag value object and TagRegistry domain service
that form the foundation of the hexagonal architecture tagging system.
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class TagCategory(str, Enum):
    """Categories for organizing different types of tags."""

    STRUCTURAL = "structural"  # Basic code structure (Class, Method, Function)
    ARCHITECTURAL = (
        "architectural"  # Hexagonal layers (Core, Application, Infrastructure)
    )
    ROLE = "role"  # Architectural roles (Entity, Service, Repository)
    PATTERN = "pattern"  # Design patterns (Singleton, Factory, Observer)
    QUALITY = "quality"  # Quality attributes (ThreadSafe, Immutable, Async)
    FUNCTIONAL = "functional"  # Functional aspects (Reader, Writer, Validator)
    TECHNICAL = "technical"  # Technical patterns (CQRS, EventSourcing, API)
    SECURITY = "security"  # Security characteristics (Authenticated, Encrypted)
    PERFORMANCE = "performance"  # Performance attributes (Cacheable, HighThroughput)
    FILE_TYPE = "file_type"  # File classifications (ImplementationFile, TestFile)
    MODULE_TYPE = "module_type"  # Module classifications (DomainModule, TestModule)


class TagType(str, Enum):
    """Types of tags based on their application scope."""

    NODE_LABEL = "node_label"  # Applied as Neo4j node labels
    NODE_PROPERTY = "node_property"  # Stored as node properties
    RELATIONSHIP = "relationship"  # Used for relationship types
    METADATA = "metadata"  # Additional metadata attributes


class Tag(BaseModel):
    """
    Immutable value object representing a single tag.

    Tags are the fundamental unit of classification in the system,
    providing semantic meaning to code components and their relationships.
    """

    name: str = Field(..., description="Unique name of the tag")
    category: TagCategory = Field(..., description="Category this tag belongs to")
    tag_type: TagType = Field(
        default=TagType.NODE_LABEL, description="How this tag is applied"
    )
    description: str = Field(
        default="", description="Human-readable description of the tag"
    )
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Confidence score for this tag"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    parent_tags: Set[str] = Field(
        default_factory=set, description="Parent tags in hierarchy"
    )
    child_tags: Set[str] = Field(
        default_factory=set, description="Child tags in hierarchy"
    )

    class Config:
        frozen = True  # Make immutable
        use_enum_values = True

    @validator("name")
    def validate_name(cls, v: str) -> str:
        """Validate tag name format."""
        if not v or not v.strip():
            raise ValueError("Tag name cannot be empty")

        # Tag names should follow Neo4j label conventions
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Tag name must be alphanumeric with underscores or hyphens"
            )

        return v.strip()

    @validator("confidence")
    def validate_confidence(cls, v: float) -> float:
        """Ensure confidence is within valid range."""
        return max(0.0, min(1.0, v))

    def __hash__(self) -> int:
        """Make Tag hashable for use in sets."""
        return hash((self.name, self.category))

    def __str__(self) -> str:
        """String representation of the tag."""
        return f":{self.name}"

    def to_neo4j_label(self) -> str:
        """Convert tag to Neo4j label format."""
        return self.name

    def is_compatible_with(self, other: Tag) -> bool:
        """Check if this tag is compatible with another tag."""
        # Tags in the same category might have compatibility rules
        if self.category == other.category:
            # Some categories are mutually exclusive
            exclusive_pairs = {
                ("Mutable", "Immutable"),
                ("Sync", "Async"),
                ("Stateful", "Stateless"),
            }

            for pair in exclusive_pairs:
                if {self.name, other.name} == set(pair):
                    return False

        return True


class TagCollection(BaseModel):
    """
    Collection of tags with validation and utility methods.

    Provides operations for managing sets of tags while ensuring
    consistency and compatibility rules are maintained.
    """

    tags: Set[Tag] = Field(
        default_factory=set, description="Set of tags in this collection"
    )

    class Config:
        frozen = True

    def __len__(self) -> int:
        """Return number of tags in collection."""
        return len(self.tags)

    def __iter__(self):
        """Iterate over tags in collection."""
        return iter(self.tags)

    def __contains__(self, tag: Tag) -> bool:
        """Check if tag is in collection."""
        return tag in self.tags

    def add(self, tag: Tag) -> TagCollection:
        """Add a tag to the collection, returning a new collection."""
        if not self.is_compatible_with(tag):
            raise ValueError(f"Tag {tag.name} is not compatible with existing tags")

        new_tags = self.tags.copy()
        new_tags.add(tag)
        return TagCollection(tags=new_tags)

    def remove(self, tag: Tag) -> TagCollection:
        """Remove a tag from the collection, returning a new collection."""
        new_tags = self.tags.copy()
        new_tags.discard(tag)
        return TagCollection(tags=new_tags)

    def is_compatible_with(self, tag: Tag) -> bool:
        """Check if a tag is compatible with all tags in this collection."""
        return all(existing_tag.is_compatible_with(tag) for existing_tag in self.tags)

    def get_by_category(self, category: TagCategory) -> Set[Tag]:
        """Get all tags in a specific category."""
        return {tag for tag in self.tags if tag.category == category}

    def get_by_type(self, tag_type: TagType) -> Set[Tag]:
        """Get all tags of a specific type."""
        return {tag for tag in self.tags if tag.tag_type == tag_type}

    def to_neo4j_labels(self) -> List[str]:
        """Convert all node label tags to Neo4j label format."""
        return [
            tag.to_neo4j_label()
            for tag in self.tags
            if tag.tag_type == TagType.NODE_LABEL
        ]

    def to_neo4j_properties(self) -> Dict[str, Any]:
        """Convert property tags to Neo4j properties."""
        properties = {}

        for tag in self.tags:
            if tag.tag_type == TagType.NODE_PROPERTY:
                properties[f"tag_{tag.name.lower()}"] = True
                if tag.metadata:
                    properties[f"tag_{tag.name.lower()}_metadata"] = json.dumps(
                        tag.metadata
                    )

        # Add tag summary
        properties["tags"] = [tag.name for tag in self.tags]
        properties["tag_categories"] = list({tag.category.value for tag in self.tags})

        return properties


class TagRegistry:
    """
    Domain service for managing tag definitions and validation rules.

    Acts as the central registry for all available tags in the system,
    providing validation, suggestion, and hierarchy management capabilities.
    """

    def __init__(self) -> None:
        self._tags: Dict[str, Tag] = {}
        self._category_index: Dict[TagCategory, Set[str]] = {
            category: set() for category in TagCategory
        }
        self._hierarchy_graph: Dict[str, Set[str]] = {}  # parent -> children
        self._initialize_default_tags()

    def register_tag(self, tag: Tag) -> None:
        """Register a new tag in the registry."""
        if tag.name in self._tags:
            raise ValueError(f"Tag '{tag.name}' is already registered")

        self._tags[tag.name] = tag
        self._category_index[tag.category].add(tag.name)

        # Update hierarchy
        for parent_name in tag.parent_tags:
            if parent_name not in self._hierarchy_graph:
                self._hierarchy_graph[parent_name] = set()
            self._hierarchy_graph[parent_name].add(tag.name)

    def get_tag(self, name: str) -> Optional[Tag]:
        """Get a tag by name."""
        return self._tags.get(name)

    def get_tags_by_category(self, category: TagCategory) -> List[Tag]:
        """Get all tags in a specific category."""
        tag_names = self._category_index.get(category, set())
        return [self._tags[name] for name in tag_names if name in self._tags]

    def get_all_tags(self) -> List[Tag]:
        """Get all registered tags."""
        return list(self._tags.values())

    def validate_tag_combination(self, tags: List[Tag]) -> bool:
        """Validate that a combination of tags is compatible."""
        if not tags:
            return True

        # Check pairwise compatibility
        for i, tag1 in enumerate(tags):
            for tag2 in tags[i + 1 :]:
                if not tag1.is_compatible_with(tag2):
                    return False

        return True

    def suggest_tags(
        self, existing_tags: List[Tag], context: Dict[str, Any] = None
    ) -> List[Tag]:
        """Suggest additional tags based on existing tags and context."""
        suggestions = []
        context = context or {}

        # Get categories already present
        existing_categories = {tag.category for tag in existing_tags}

        # Suggest complementary tags based on patterns
        for tag in existing_tags:
            suggestions.extend(self._get_complementary_tags(tag, existing_categories))

        # Filter out incompatible suggestions
        compatible_suggestions = []
        for suggestion in suggestions:
            if suggestion not in existing_tags and self.validate_tag_combination(
                existing_tags + [suggestion]
            ):
                compatible_suggestions.append(suggestion)

        return compatible_suggestions[:10]  # Limit to top 10 suggestions

    def get_tag_hierarchy(self, tag_name: str) -> Dict[str, Any]:
        """Get the hierarchy information for a tag."""
        if tag_name not in self._tags:
            return {}

        tag = self._tags[tag_name]
        return {
            "tag": tag,
            "parents": [
                self._tags[parent] for parent in tag.parent_tags if parent in self._tags
            ],
            "children": [
                self._tags[child]
                for child in self._hierarchy_graph.get(tag_name, set())
                if child in self._tags
            ],
        }

    def _get_complementary_tags(
        self, tag: Tag, existing_categories: Set[TagCategory]
    ) -> List[Tag]:
        """Get tags that complement the given tag."""
        complementary = []

        # Architectural layer suggestions
        if tag.category == TagCategory.ARCHITECTURAL:
            if tag.name == "Core" and TagCategory.ROLE not in existing_categories:
                complementary.extend(self.get_tags_by_category(TagCategory.ROLE))

        # Pattern-based suggestions
        if tag.category == TagCategory.PATTERN:
            if (
                tag.name == "Repository"
                and TagCategory.ARCHITECTURAL not in existing_categories
            ):
                infrastructure_tag = self.get_tag("Infrastructure")
                if infrastructure_tag:
                    complementary.append(infrastructure_tag)

        return complementary

    def _initialize_default_tags(self) -> None:
        """Initialize the registry with default hexagonal architecture tags."""
        # Structural tags
        structural_tags = [
            Tag(
                name="Codebase",
                category=TagCategory.STRUCTURAL,
                description="Root container for entire codebase",
            ),
            Tag(
                name="Module",
                category=TagCategory.STRUCTURAL,
                description="Logical grouping of related files",
            ),
            Tag(
                name="File",
                category=TagCategory.STRUCTURAL,
                description="Individual source code files",
            ),
            Tag(
                name="Class",
                category=TagCategory.STRUCTURAL,
                description="Classes and interfaces",
            ),
            Tag(
                name="Method",
                category=TagCategory.STRUCTURAL,
                description="Class methods",
            ),
            Tag(
                name="Function",
                category=TagCategory.STRUCTURAL,
                description="Module-level functions",
            ),
            Tag(
                name="Property",
                category=TagCategory.STRUCTURAL,
                description="Class properties/attributes",
            ),
        ]

        # Architectural layer tags
        architectural_tags = [
            Tag(
                name="Core",
                category=TagCategory.ARCHITECTURAL,
                description="Inner hexagon - pure business logic",
            ),
            Tag(
                name="Application",
                category=TagCategory.ARCHITECTURAL,
                description="Middle layer - application services and ports",
            ),
            Tag(
                name="Infrastructure",
                category=TagCategory.ARCHITECTURAL,
                description="Outer layer - adapters and external concerns",
            ),
            Tag(
                name="Domain",
                category=TagCategory.ARCHITECTURAL,
                description="Core business domain",
            ),
            Tag(
                name="Port",
                category=TagCategory.ARCHITECTURAL,
                description="Interfaces defining boundaries",
            ),
            Tag(
                name="Adapter",
                category=TagCategory.ARCHITECTURAL,
                description="Concrete implementations of ports",
            ),
        ]

        # Role-based tags
        role_tags = [
            Tag(
                name="Entity",
                category=TagCategory.ROLE,
                description="Domain entities with identity",
            ),
            Tag(
                name="ValueObject",
                category=TagCategory.ROLE,
                description="Immutable domain value objects",
            ),
            Tag(
                name="Service",
                category=TagCategory.ROLE,
                description="Domain or application services",
            ),
            Tag(
                name="Repository",
                category=TagCategory.ROLE,
                description="Data access abstraction",
            ),
            Tag(
                name="Factory",
                category=TagCategory.ROLE,
                description="Object creation logic",
            ),
            Tag(
                name="UseCase",
                category=TagCategory.ROLE,
                description="Application use case handlers",
            ),
        ]

        # Quality attribute tags
        quality_tags = [
            Tag(
                name="Immutable",
                category=TagCategory.QUALITY,
                description="Immutable objects",
            ),
            Tag(
                name="Mutable",
                category=TagCategory.QUALITY,
                description="Mutable objects",
            ),
            Tag(
                name="ThreadSafe",
                category=TagCategory.QUALITY,
                description="Thread-safe components",
            ),
            Tag(
                name="Async",
                category=TagCategory.QUALITY,
                description="Asynchronous components",
            ),
            Tag(
                name="Sync",
                category=TagCategory.QUALITY,
                description="Synchronous components",
            ),
            Tag(
                name="Stateless",
                category=TagCategory.QUALITY,
                description="Stateless components",
            ),
            Tag(
                name="Stateful",
                category=TagCategory.QUALITY,
                description="Stateful components",
            ),
        ]

        # Register all default tags
        for tag_list in [structural_tags, architectural_tags, role_tags, quality_tags]:
            for tag in tag_list:
                try:
                    self.register_tag(tag)
                except ValueError:
                    # Tag already exists, skip
                    pass


# Global registry instance
_global_registry: Optional[TagRegistry] = None


def get_tag_registry() -> TagRegistry:
    """Get the global tag registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = TagRegistry()
    return _global_registry
