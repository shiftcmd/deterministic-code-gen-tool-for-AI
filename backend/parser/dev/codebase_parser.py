"""
Codebase Parser module for Python Debug Tool.

This module implements the main CodebaseParser class that orchestrates
the parsing process across a Python codebase, utilizing configurable
tool combinations for different code element types.

# AI-Intent: Core-Domain
# Intent: This class serves as the primary domain entity for parsing Python codebases
# Confidence: High
"""

import ast
import hashlib
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from .config import ParserConfig, ParserType, get_parser_config
from .models import ParsedModule
from .module_parser import ModuleParser
from .parallel_processor import ParallelProcessor

logger = logging.getLogger(__name__)


class CodebaseParser:
    """
    Main parser class that scans and analyzes Python codebases.

    This class orchestrates the parsing process, applying the appropriate parsers
    based on configuration, and manages caching and parallel processing.
    """

    def __init__(self, config: Optional[ParserConfig] = None):
        """
        Initialize the codebase parser.

        Args:
            config: Configuration for the parser. If None, the standard preset is used.
        """
        self.config = config or get_parser_config("standard")
        self.module_parser = ModuleParser(self.config)
        self._cache = {}  # Simple in-memory cache
        
        # Initialize new parallel processor
        self.parallel_processor = ParallelProcessor(self.config)

    def parse_codebase(self, root_path: str) -> Dict[str, ParsedModule]:
        """
        Parse an entire Python codebase starting from a root directory.

        Args:
            root_path: Path to the root directory of the codebase

        Returns:
            Dictionary mapping file paths to parsed modules
        """
        root_path = os.path.abspath(root_path)
        logger.info(f"Parsing codebase at {root_path}")

        python_files = self._discover_python_files(root_path)
        logger.info(f"Discovered {len(python_files)} Python files")

        parsed_modules = {}

        # Use new parallel processing architecture if configured
        if self.config.parallel_processing and len(python_files) > 1:
            logger.info("Using enhanced parallel processing architecture")
            parsed_modules = self.parallel_processor.process_files(python_files, self.parse_file)
        else:
            # Sequential processing for small codebases or when disabled
            for file_path in python_files:
                try:
                    parsed_module = self.parse_file(file_path)
                    if parsed_module:
                        parsed_modules[file_path] = parsed_module
                except Exception as e:
                    logger.error(f"Error parsing {file_path}: {e}")

        logger.info(f"Successfully parsed {len(parsed_modules)} modules")
        
        # Log processing metrics if parallel processing was used
        if self.config.parallel_processing and len(python_files) > 1:
            metrics = self.parallel_processor.get_metrics()
            logger.info(f"Parsing metrics: {metrics.processed_files}/{metrics.total_files} files processed "
                       f"({metrics.success_rate:.1f}% success rate) in {metrics.duration:.2f}s "
                       f"({metrics.files_per_second:.1f} files/sec)")
        return parsed_modules

    def parse_file(self, file_path: str) -> Optional[ParsedModule]:
        """
        Parse a single Python file.

        Args:
            file_path: Path to the Python file

        Returns:
            Parsed module or None if parsing failed
        """
        file_path = os.path.abspath(file_path)

        # Check cache if enabled
        if self.config.cache_results and file_path in self._cache:
            return self._cache[file_path]

        # Check file size if limit is set
        if self.config.max_file_size > 0:
            file_size = os.path.getsize(file_path)
            if file_size > self.config.max_file_size:
                logger.warning(
                    f"Skipping {file_path}: exceeds size limit "
                    f"({file_size} > {self.config.max_file_size} bytes)"
                )
                return None

        try:
            # Use the module parser to parse the file
            parsed_module = self.module_parser.parse(file_path)

            # Cache the result if caching is enabled
            if self.config.cache_results:
                self._cache[file_path] = parsed_module

            return parsed_module

        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return None

    def _discover_python_files(self, root_path: str) -> List[str]:
        """
        Discover Python files in the given directory tree.

        Args:
            root_path: Root directory to search in

        Returns:
            List of Python file paths
        """
        python_files = []

        for dirpath, dirnames, filenames in os.walk(root_path):
            # Skip virtual environments and hidden directories
            dirnames[:] = [
                d
                for d in dirnames
                if not d.startswith(".") and d not in ["venv", "env", "__pycache__"]
            ]

            # Skip external libraries if configured
            if self.config.skip_external_libs:
                dirnames[:] = [
                    d for d in dirnames if d not in ["site-packages", "dist-packages"]
                ]

            for filename in filenames:
                if filename.endswith(".py"):
                    full_path = os.path.join(dirpath, filename)
                    python_files.append(full_path)

        return python_files

    def _parse_in_parallel(self, file_paths: List[str]) -> Dict[str, ParsedModule]:
        """
        Legacy parallel parsing method for backward compatibility.
        Now delegates to the new ParallelProcessor.

        Args:
            file_paths: List of file paths to parse

        Returns:
            Dictionary mapping file paths to parsed modules
        """
        logger.warning("_parse_in_parallel is deprecated - using ParallelProcessor")
        return self.parallel_processor.process_files(file_paths, self.parse_file)

    def add_progress_observer(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Add a progress observer for real-time parsing updates.
        
        Args:
            callback: Function that receives progress updates
        """
        self.parallel_processor.add_progress_observer(callback)
        
    def get_processing_metrics(self) -> Dict[str, Any]:
        """
        Get processing performance metrics.
        
        Returns:
            Dictionary containing processing metrics
        """
        metrics = self.parallel_processor.get_metrics()
        cache_stats = self.parallel_processor.get_cache_stats()
        
        return {
            "total_files": metrics.total_files,
            "processed_files": metrics.processed_files,
            "failed_files": metrics.failed_files,
            "success_rate": metrics.success_rate,
            "duration": metrics.duration,
            "files_per_second": metrics.files_per_second,
            "memory_utilization": self.parallel_processor.memory_manager.utilization_percentage,
            "cache_stats": cache_stats
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.
        
        Returns:
            Dictionary containing cache statistics
        """
        return self.parallel_processor.get_cache_stats()
    
    def clear_cache(self) -> bool:
        """
        Clear all cached parsing data.
        
        Returns:
            True if cache cleared successfully
        """
        success = self.parallel_processor.clear_cache()
        if success:
            logger.info("Parser cache cleared successfully")
        return success
    
    def invalidate_file_cache(self, file_path: str) -> bool:
        """
        Invalidate cache for a specific file.
        
        Args:
            file_path: Path to the file to invalidate
            
        Returns:
            True if invalidated successfully
        """
        return self.parallel_processor.invalidate_file_cache(file_path)
    
    def cleanup_stale_cache(self, max_age_days: int = 30) -> int:
        """
        Remove cache entries older than specified age.
        
        Args:
            max_age_days: Maximum age of cache entries in days
            
        Returns:
            Number of entries removed
        """
        removed_count = self.parallel_processor.cleanup_stale_cache(max_age_days)
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} stale cache entries")
        return removed_count

    def get_file_hash(self, file_path: str) -> str:
        """
        Calculate the MD5 hash of a file for caching purposes.

        Args:
            file_path: Path to the file

        Returns:
            MD5 hash of the file
        """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def clear_cache(self) -> None:
        """Clear the parsing cache."""
        self._cache.clear()
        logger.debug("Parser cache cleared")
