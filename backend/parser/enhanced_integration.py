"""
Enhanced Integration for Task 2.5: Caching, Parallelism, and Neo4j Integration

This module provides a comprehensive integration layer that seamlessly combines:
1. Hash-based incremental caching from Task 2.3
2. Parallel processing architecture from Task 2.1
3. Memory-efficient parsing from Task 2.2
4. Neo4j graph database export
5. Plugin system compatibility

# AI-Intent: Application-Service
# Intent: Integration service that orchestrates cached parallel parsing with Neo4j export
# Confidence: High
# @layer: application
# @component: integration
# @performance: parallel-cached-export
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .codebase_parser import CodebaseParser
from .config import ParserConfig, get_parser_config
from .hash_based_cache import HashBasedCache, CacheEntry
from .models import ParsedModule
from .parallel_processor import ParallelProcessor, ProcessingMetrics

# Initialize logger first
logger = logging.getLogger(__name__)

# Handle optional dependencies gracefully
try:
    from .exporters.neo4j_exporter import Neo4jExporter
except ImportError:
    Neo4jExporter = None
    logger.warning("Neo4j exporter not available")

# Try different import paths for relationship extractor
RelationshipExtractor = None
CodeRelationship = None

try:
    # Try absolute import first
    from backend.graph_builder.relationship_extractor import RelationshipExtractor, CodeRelationship
except ImportError:
    try:
        # Try relative import
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
        from backend.graph_builder.relationship_extractor import RelationshipExtractor, CodeRelationship
    except ImportError:
        # Create simple stubs
        from dataclasses import dataclass
        from typing import Any, Dict
        
        class RelationshipExtractor:
            def __init__(self, file_path=None, module_name=None):
                self.file_path = file_path
                self.module_name = module_name
                self.relationships = []
                
            def extract_relationships_from_parsed_module(self, parsed_module):
                """Extract relationships from a ParsedModule object."""
                return []
                
            def visit(self, ast_tree):
                """Compatibility method for AST visitor pattern."""
                pass
        
        @dataclass
        class CodeRelationship:
            source: str = ""
            target: str = ""
            relationship_type: str = ""
            metadata: Dict[str, Any] = None
            
            def __post_init__(self):
                if self.metadata is None:
                    self.metadata = {}
        
        logger.warning("Relationship extractor not available, using stub")


class EnhancedIntegration:
    """
    Enhanced integration class that orchestrates cached parallel parsing with Neo4j export.
    
    This class provides the complete workflow:
    1. Discover files to parse
    2. Use cache to determine what needs re-parsing
    3. Parse changed files in parallel with memory management
    4. Extract relationships from parsed modules
    5. Store results in cache
    6. Export to Neo4j atomically
    7. Provide comprehensive metrics and progress tracking
    """
    
    def __init__(self, 
                 config: Optional[ParserConfig] = None,
                 neo4j_options: Optional[Dict[str, Any]] = None,
                 enable_caching: bool = True,
                 enable_parallel: bool = True,
                 enable_neo4j_export: bool = True):
        """
        Initialize the enhanced integration.
        
        Args:
            config: Parser configuration
            neo4j_options: Neo4j connection options
            enable_caching: Enable hash-based caching
            enable_parallel: Enable parallel processing
            enable_neo4j_export: Enable Neo4j export
        """
        self.config = config or get_parser_config("comprehensive")
        self.enable_caching = enable_caching
        self.enable_parallel = enable_parallel
        self.enable_neo4j_export = enable_neo4j_export
        
        # Initialize core components
        self.codebase_parser = CodebaseParser(self.config)
        
        # Initialize cache if enabled
        self.cache = None
        if self.enable_caching:
            cache_dir = self.config.tool_options.get('cache', {}).get('cache_dir', '.cache/parser')
            self.cache = HashBasedCache(self.config, cache_dir)
        
        # Initialize relationship extractor
        # For the stub class or when we don't have file-specific info yet, initialize without parameters
        try:
            self.relationship_extractor = RelationshipExtractor()
        except TypeError:
            # If the real RelationshipExtractor requires parameters, create with empty values
            self.relationship_extractor = RelationshipExtractor("", "")
        
        # Initialize Neo4j exporter if enabled
        self.neo4j_exporter = None
        if self.enable_neo4j_export and Neo4jExporter is not None:
            default_neo4j_options = {
                "uri": "bolt://localhost:7687",
                "user": "neo4j", 
                "password": "password",
                "database": "neo4j",
                "batch_size": 100,
                "clear_existing": False,
                "include_content": False,
                "detect_architecture": True
            }
            if neo4j_options:
                default_neo4j_options.update(neo4j_options)
            self.neo4j_exporter = Neo4jExporter(default_neo4j_options)
        elif self.enable_neo4j_export and Neo4jExporter is None:
            logger.warning("Neo4j export requested but Neo4j exporter not available")
            self.enable_neo4j_export = False
        
        # Progress observers
        self.progress_observers: List[Callable] = []
        
        # Metrics
        self.integration_metrics = {
            'total_files': 0,
            'cached_files': 0,
            'parsed_files': 0,
            'failed_files': 0,
            'cache_hit_rate': 0.0,
            'parsing_duration': 0.0,
            'relationship_extraction_duration': 0.0,
            'neo4j_export_duration': 0.0,
            'total_duration': 0.0,
            'relationships_extracted': 0,
            'nodes_created': 0,
            'relationships_created': 0
        }
    
    def add_progress_observer(self, callback: Callable[[Dict[str, Any]], None]):
        """Add a progress observer for real-time updates."""
        self.progress_observers.append(callback)
        if hasattr(self.codebase_parser, 'add_progress_observer'):
            self.codebase_parser.add_progress_observer(callback)
    
    def _notify_progress(self, stage: str, progress: Dict[str, Any]):
        """Notify all progress observers."""
        notification = {
            'stage': stage,
            'timestamp': time.time(),
            **progress
        }
        for observer in self.progress_observers:
            try:
                observer(notification)
            except Exception as e:
                logger.warning(f"Progress observer error: {e}")
    
    def parse_codebase_with_integration(self, 
                                      root_path: str,
                                      force_reparse: bool = False,
                                      export_to_neo4j: bool = True) -> Dict[str, Any]:
        """
        Parse a codebase with full integration of caching, parallel processing, and Neo4j export.
        
        Args:
            root_path: Root directory of the codebase
            force_reparse: Force re-parsing of all files (ignore cache)
            export_to_neo4j: Whether to export results to Neo4j
            
        Returns:
            Comprehensive results including parsed modules, metrics, and export status
        """
        start_time = time.time()
        
        try:
            # Stage 1: Discover files
            self._notify_progress("discovery", {"status": "discovering_files"})
            python_files = self._discover_python_files(root_path)
            self.integration_metrics['total_files'] = len(python_files)
            
            logger.info(f"Discovered {len(python_files)} Python files")
            self._notify_progress("discovery", {
                "status": "completed", 
                "files_found": len(python_files)
            })
            
            # Stage 2: Cache analysis
            changed_files = python_files
            cached_files = []
            cached_results = {}
            
            if self.cache and not force_reparse:
                self._notify_progress("cache_analysis", {"status": "analyzing_cache"})
                changed_files, cached_files = self.cache.get_changed_files(python_files)
                
                # Load cached results
                if cached_files:
                    cached_results = self.cache.bulk_load_cached_results(cached_files)
                
                self.integration_metrics['cached_files'] = len(cached_files)
                self.integration_metrics['cache_hit_rate'] = len(cached_files) / len(python_files) if python_files else 0
                
                logger.info(f"Cache analysis: {len(changed_files)} changed, {len(cached_files)} cached")
                self._notify_progress("cache_analysis", {
                    "status": "completed",
                    "changed_files": len(changed_files),
                    "cached_files": len(cached_files),
                    "hit_rate": self.integration_metrics['cache_hit_rate']
                })
            
            # Stage 3: Parse changed files
            parsed_modules = {}
            parsing_start = time.time()
            
            if changed_files:
                self._notify_progress("parsing", {
                    "status": "parsing_files", 
                    "files_to_parse": len(changed_files)
                })
                
                if self.enable_parallel and len(changed_files) > 1:
                    # Use parallel processing for changed files
                    parsed_modules = self.codebase_parser.parallel_processor.process_files(
                        changed_files, self.codebase_parser.parse_file
                    )
                else:
                    # Sequential parsing
                    for file_path in changed_files:
                        try:
                            result = self.codebase_parser.parse_file(file_path)
                            if result:
                                parsed_modules[file_path] = result
                        except Exception as e:
                            logger.error(f"Error parsing {file_path}: {e}")
                            self.integration_metrics['failed_files'] += 1
                
                self.integration_metrics['parsed_files'] = len(parsed_modules)
            
            parsing_duration = time.time() - parsing_start
            self.integration_metrics['parsing_duration'] = parsing_duration
            
            logger.info(f"Parsed {len(parsed_modules)} files in {parsing_duration:.2f}s")
            self._notify_progress("parsing", {
                "status": "completed",
                "files_parsed": len(parsed_modules),
                "duration": parsing_duration
            })
            
            # Stage 4: Combine cached and parsed results
            all_modules = {}
            
            # Add cached results
            for file_path, cache_entry in cached_results.items():
                if cache_entry and cache_entry.parsed_module:
                    all_modules[file_path] = cache_entry.parsed_module
            
            # Add newly parsed results
            all_modules.update(parsed_modules)
            
            logger.info(f"Total modules available: {len(all_modules)}")
            
            # Stage 5: Extract relationships
            relationship_start = time.time()
            all_relationships = {}
            
            self._notify_progress("relationships", {
                "status": "extracting_relationships",
                "modules_to_process": len(all_modules)
            })
            
            for file_path, parsed_module in all_modules.items():
                try:
                    # Use the correct method name for relationship extraction
                    relationships = self.relationship_extractor.extract_relationships_from_parsed_module(parsed_module)
                    all_relationships[file_path] = relationships
                except Exception as e:
                    logger.warning(f"Error extracting relationships from {file_path}: {e}")
                    all_relationships[file_path] = []
            
            total_relationships = sum(len(rels) for rels in all_relationships.values())
            relationship_duration = time.time() - relationship_start
            self.integration_metrics['relationship_extraction_duration'] = relationship_duration
            self.integration_metrics['relationships_extracted'] = total_relationships
            
            logger.info(f"Extracted {total_relationships} relationships in {relationship_duration:.2f}s")
            self._notify_progress("relationships", {
                "status": "completed",
                "relationships_extracted": total_relationships,
                "duration": relationship_duration
            })
            
            # Stage 6: Update cache with new results
            if self.cache and parsed_modules:
                self._notify_progress("cache_update", {"status": "updating_cache"})
                
                for file_path, parsed_module in parsed_modules.items():
                    relationships = all_relationships.get(file_path, [])
                    self.cache.store_result(
                        file_path, parsed_module, relationships, 
                        parsing_duration / len(parsed_modules) if parsed_modules else 0
                    )
                
                # Save cache to disk
                self.cache.save_hash_cache()
                
                self._notify_progress("cache_update", {"status": "completed"})
            
            # Stage 7: Export to Neo4j
            neo4j_duration = 0.0
            nodes_created = 0
            relationships_created = 0
            
            if self.neo4j_exporter and export_to_neo4j and all_modules:
                self._notify_progress("neo4j_export", {
                    "status": "exporting_to_neo4j",
                    "modules_to_export": len(all_modules)
                })
                
                neo4j_start = time.time()
                
                try:
                    # Prepare data for Neo4j export
                    export_data = {
                        'modules': list(all_modules.values()),
                        'relationships': all_relationships,
                        'metadata': {
                            'parsed_at': time.time(),
                            'total_files': len(all_modules),
                            'cache_hit_rate': self.integration_metrics['cache_hit_rate']
                        }
                    }
                    
                    # Export to Neo4j atomically
                    success = self.neo4j_exporter.export(export_data)
                    
                    if success:
                        # Get export metrics
                        nodes_created = self.neo4j_exporter.total_nodes
                        relationships_created = self.neo4j_exporter.total_relationships
                        
                        logger.info(f"Neo4j export successful: {nodes_created} nodes, {relationships_created} relationships")
                    
                except Exception as e:
                    logger.error(f"Neo4j export failed: {e}")
                
                neo4j_duration = time.time() - neo4j_start
                self.integration_metrics['neo4j_export_duration'] = neo4j_duration
                self.integration_metrics['nodes_created'] = nodes_created
                self.integration_metrics['relationships_created'] = relationships_created
                
                self._notify_progress("neo4j_export", {
                    "status": "completed",
                    "nodes_created": nodes_created,
                    "relationships_created": relationships_created,
                    "duration": neo4j_duration
                })
            
            # Final metrics
            total_duration = time.time() - start_time
            self.integration_metrics['total_duration'] = total_duration
            
            logger.info(f"Integration completed in {total_duration:.2f}s")
            self._notify_progress("completed", {
                "status": "integration_completed",
                "total_duration": total_duration,
                "metrics": self.integration_metrics
            })
            
            return {
                'success': True,
                'parsed_modules': all_modules,
                'relationships': all_relationships,
                'metrics': self.integration_metrics,
                'cache_stats': self.cache.get_cache_stats() if self.cache else None,
                'neo4j_export': {
                    'enabled': export_to_neo4j,
                    'nodes_created': nodes_created,
                    'relationships_created': relationships_created
                }
            }
            
        except Exception as e:
            error_msg = f"Integration failed: {e}"
            logger.error(error_msg)
            self._notify_progress("error", {"status": "failed", "error": str(e)})
            
            return {
                'success': False,
                'error': error_msg,
                'metrics': self.integration_metrics
            }
    
    def _discover_python_files(self, root_path: str) -> List[str]:
        """Discover Python files in the given directory tree."""
        python_files = []
        root_path = Path(root_path)
        
        for py_file in root_path.rglob("*.py"):
            # Skip common non-source directories
            path_parts = py_file.parts
            if any(skip in path_parts for skip in ["__pycache__", ".git", "venv", "env", "site-packages"]):
                continue
            python_files.append(str(py_file))
        
        return python_files
    
    def get_integration_metrics(self) -> Dict[str, Any]:
        """Get comprehensive integration metrics."""
        return {
            **self.integration_metrics,
            'cache_stats': self.cache.get_cache_stats() if self.cache else None,
            'parallel_processing_metrics': self.codebase_parser.get_processing_metrics() if hasattr(self.codebase_parser, 'get_processing_metrics') else None
        }
    
    def clear_all_caches(self) -> bool:
        """Clear all caches (parsing and hash-based)."""
        success = True
        
        if self.cache:
            success &= self.cache.clear_cache()
        
        if hasattr(self.codebase_parser, 'clear_cache'):
            try:
                self.codebase_parser.clear_cache()
            except:
                success = False
        
        return success
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on all integrated components."""
        health = {
            'overall_status': 'healthy',
            'components': {}
        }
        
        # Check parser
        try:
            self.codebase_parser.config
            health['components']['parser'] = 'healthy'
        except Exception as e:
            health['components']['parser'] = f'unhealthy: {e}'
            health['overall_status'] = 'degraded'
        
        # Check cache
        if self.cache:
            try:
                self.cache.get_cache_stats()
                health['components']['cache'] = 'healthy'
            except Exception as e:
                health['components']['cache'] = f'unhealthy: {e}'
                health['overall_status'] = 'degraded'
        else:
            health['components']['cache'] = 'disabled'
        
        # Check Neo4j connection
        if self.neo4j_exporter:
            try:
                connected = self.neo4j_exporter.connect()
                health['components']['neo4j'] = 'healthy' if connected else 'connection_failed'
                if not connected:
                    health['overall_status'] = 'degraded'
                # Disconnect after test
                self.neo4j_exporter.disconnect()
            except Exception as e:
                health['components']['neo4j'] = f'unhealthy: {e}'
                health['overall_status'] = 'degraded'
        else:
            health['components']['neo4j'] = 'disabled'
        
        return health
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if self.cache:
            return self.cache.get_cache_stats()
        return {
            'cache_enabled': False,
            'total_cached_files': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
