"""
Generic Hexagonal Architecture Tagging System

A comprehensive system for analyzing and tagging code components within
a hexagonal architecture framework, combining static analysis with AI-powered
semantic understanding to create knowledge graphs in Neo4j.
"""

__version__ = "0.1.0"
__author__ = "Generic Hexagonal Tagger Team"
__email__ = "team@hexagonal-tagger.dev"

from .application.services.tagging_service import TaggingService
from .core.domain.code_component import CodeComponent
from .core.domain.tag import Tag, TagRegistry

__all__ = [
    "Tag",
    "TagRegistry",
    "CodeComponent",
    "TaggingService",
]
