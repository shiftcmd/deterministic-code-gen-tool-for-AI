"""
Relationship-Aware Parser for Task 2.2.

This module integrates the memory-efficient parser with relationship extraction
capabilities from the existing relationship_extractor.py, creating a unified
parsing system that extracts both structural information and code relationships
in a memory-efficient manner.

# AI-Intent: Core-Domain:Application
# Intent: Unified parser that extracts structure and relationships efficiently
# Confidence: High
# @layer: application
# @component: relationship-extraction
# @depends-on: memory-efficient-parser, relationship-extractor
"""

import ast
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .config import ParserConfig
from .memory_efficient_parser import MemoryEfficientParser
from .models import ParsedModule
from ..graph_builder.relationship_extractor import RelationshipExtractor, CodeRelationship

logger = logging.getLogger(__name__)


class RelationshipAwareParser(MemoryEfficientParser):
    """
    Enhanced parser that combines memory-efficient parsing with relationship extraction.
    
    This parser extends the memory-efficient parser to also extract code relationships
    including imports, function calls, inheritance, and dependencies. It integrates
    seamlessly with the existing relationship extraction infrastructure.
    """
    
    def __init__(self, config: ParserConfig, postgres_client=None, neo4j_client=None):
        super().__init__(config)
        self.postgres_client = postgres_client
        self.neo4j_client = neo4j_client
        
        # Track relationships across all parsed files
        self.global_relationships: List[CodeRelationship] = []
        self.relationship_extractors: Dict[str, RelationshipExtractor] = {}
    
    def parse_file_with_relationships(self, file_path: str, progress_callback=None) -> Tuple[Optional[ParsedModule], Optional[RelationshipExtractor]]:
        """
        Parse a file extracting both structure and relationships.
        
        Args:
            file_path: Path to the Python file
            progress_callback: Optional progress callback
            
        Returns:
            Tuple of (ParsedModule, RelationshipExtractor) or (None, None) if failed
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return None, None
        
        try:
            # First, parse the file structure using memory-efficient methods
            with self._memory_monitor():
                parsed_module = self.parse_file_memory_efficient(str(file_path), progress_callback)
                
                if parsed_module is None:
                    return None, None
                
                # Then extract relationships from the same file
                relationship_extractor = self._extract_relationships(str(file_path))
                
                if relationship_extractor:
                    # Store for global relationship tracking
                    self.relationship_extractors[str(file_path)] = relationship_extractor
                    self.global_relationships.extend(relationship_extractor.relationships)
                
                return parsed_module, relationship_extractor
                
        except Exception as e:
            logger.error(f"Relationship-aware parsing failed for {file_path}: {e}")
            return None, None
    
    def _extract_relationships(self, file_path: str) -> Optional[RelationshipExtractor]:
        """Extract relationships from a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=file_path)
            module_name = Path(file_path).stem
            
            # Create relationship extractor
            extractor = RelationshipExtractor(
                file_path=file_path,
                module_name=module_name,
                postgres_client=self.postgres_client,
                neo4j_client=self.neo4j_client
            )
            
            # Visit the AST to extract relationships
            extractor.visit(tree)
            
            logger.debug(f"Extracted {len(extractor.relationships)} relationships from {file_path}")
            return extractor
            
        except Exception as e:
            logger.error(f"Error extracting relationships from {file_path}: {e}")
            return None
    
    def parse_codebase_with_relationships(self, root_path: str, progress_callback=None) -> Dict[str, Tuple[ParsedModule, RelationshipExtractor]]:
        """
        Parse an entire codebase extracting both structure and relationships.
        
        Args:
            root_path: Root directory of the codebase
            progress_callback: Optional progress callback
            
        Returns:
            Dictionary mapping file paths to (ParsedModule, RelationshipExtractor) tuples
        """
        results = {}
        root_path = Path(root_path)
        
        # Discover Python files
        python_files = list(root_path.rglob("*.py"))
        total_files = len(python_files)
        
        logger.info(f"Processing {total_files} Python files for structure and relationships")
        
        for i, file_path in enumerate(python_files):
            if progress_callback:
                progress_callback({
                    'stage': 'parsing_files',
                    'current': i + 1,
                    'total': total_files,
                    'file': str(file_path)
                })
            
            parsed_module, relationship_extractor = self.parse_file_with_relationships(
                str(file_path), progress_callback
            )
            
            if parsed_module and relationship_extractor:
                results[str(file_path)] = (parsed_module, relationship_extractor)
            elif parsed_module:
                # Even if relationship extraction failed, keep the parsed module
                results[str(file_path)] = (parsed_module, None)
        
        logger.info(f"Successfully processed {len(results)} files with {len(self.global_relationships)} total relationships")
        return results
    
    def batch_store_all_relationships(self) -> Dict[str, int]:
        """
        Store all extracted relationships in PostgreSQL and Neo4j.
        
        Returns:
            Statistics about stored relationships
        """
        stats = {
            'postgres_success': 0,
            'postgres_failed': 0,
            'neo4j_success': 0,
            'neo4j_failed': 0,
            'total_relationships': len(self.global_relationships),
            'files_processed': len(self.relationship_extractors)
        }
        
        if not self.relationship_extractors:
            logger.warning("No relationship extractors to process")
            return stats
        
        logger.info(f"Batch storing relationships from {stats['files_processed']} files")
        
        # Process each file's relationships
        for file_path, extractor in self.relationship_extractors.items():
            try:
                # Store in PostgreSQL
                if self.postgres_client and extractor.store_relationships_in_postgres():
                    stats['postgres_success'] += len(extractor.relationships)
                else:
                    stats['postgres_failed'] += len(extractor.relationships)
                
                # Create in Neo4j
                if self.neo4j_client and extractor.create_neo4j_relationships():
                    stats['neo4j_success'] += len(extractor.relationships)
                else:
                    stats['neo4j_failed'] += len(extractor.relationships)
                    
            except Exception as e:
                logger.error(f"Error storing relationships for {file_path}: {e}")
                stats['postgres_failed'] += len(extractor.relationships)
                stats['neo4j_failed'] += len(extractor.relationships)
        
        logger.info(f"Relationship storage complete: {stats}")
        return stats
    
    def get_relationship_summary(self) -> Dict[str, Any]:
        """Get summary of extracted relationships."""
        relationship_types = {}
        file_count = len(self.relationship_extractors)
        
        for relationship in self.global_relationships:
            rel_type = relationship.relationship_type
            if rel_type not in relationship_types:
                relationship_types[rel_type] = 0
            relationship_types[rel_type] += 1
        
        return {
            'total_relationships': len(self.global_relationships),
            'files_processed': file_count,
            'relationship_types': relationship_types,
            'avg_relationships_per_file': len(self.global_relationships) / file_count if file_count > 0 else 0
        }
    
    def get_cross_file_dependencies(self) -> List[Dict[str, Any]]:
        """Get relationships that cross file boundaries."""
        cross_file_deps = []
        
        for relationship in self.global_relationships:
            if (relationship.target_file and 
                relationship.source_file != relationship.target_file):
                cross_file_deps.append({
                    'source_file': relationship.source_file,
                    'target_file': relationship.target_file,
                    'source_name': relationship.source_name,
                    'target_name': relationship.target_name,
                    'relationship_type': relationship.relationship_type,
                    'line_number': relationship.line_number
                })
        
        return cross_file_deps
    
    def clear_relationship_cache(self):
        """Clear relationship caches to free memory."""
        self.global_relationships.clear()
        self.relationship_extractors.clear()
        logger.debug("Cleared relationship caches")


def create_relationship_aware_parser(config: ParserConfig, postgres_client=None, neo4j_client=None) -> RelationshipAwareParser:
    """
    Factory function to create a relationship-aware parser.
    
    Args:
        config: Parser configuration
        postgres_client: Optional PostgreSQL client
        neo4j_client: Optional Neo4j client
        
    Returns:
        Configured RelationshipAwareParser instance
    """
    return RelationshipAwareParser(config, postgres_client, neo4j_client)
