"""
Codebase Parser module for Python Debug Tool - Production Version.

This module implements the main CodebaseParser class that orchestrates
the parsing process across a Python codebase, utilizing configurable
tool combinations and parallel processing.

Key improvements:
- Removed redundant in-memory cache (delegates to ParallelProcessor)
- Added status reporting integration
- Cleaner separation of concerns
"""

import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from config import ParserConfig, get_parser_config
from models import ParsedModule
from module_parser import ModuleParser
from parallel_processor import ParallelProcessor
from communication import StatusReporter

logger = logging.getLogger(__name__)


class CodebaseParser:
    """
    Main parser class that scans and analyzes Python codebases.
    
    This class orchestrates the parsing process, applying the appropriate parsers
    based on configuration, and manages parallel processing through the ParallelProcessor.
    """

    def __init__(self, config: Optional[ParserConfig] = None):
        """
        Initialize the codebase parser.

        Args:
            config: Configuration for the parser. If None, the standard preset is used.
        """
        self.config = config or get_parser_config("standard")
        self.module_parser = ModuleParser(self.config)
        # Note: Removed redundant self._cache - all caching is handled by ParallelProcessor
        
        # Initialize parallel processor
        self.parallel_processor = ParallelProcessor(self.config)

    def parse_codebase(
        self, 
        root_path: str,
        status_reporter: Optional[StatusReporter] = None
    ) -> Dict[str, ParsedModule]:
        """
        Parse an entire Python codebase starting from a root directory.

        Args:
            root_path: Path to the root directory of the codebase
            status_reporter: Optional status reporter for progress updates

        Returns:
            Dictionary mapping file paths to parsed modules
        """
        root_path = os.path.abspath(root_path)
        logger.info(f"Parsing codebase at {root_path}")

        # Report discovery phase
        if status_reporter:
            status_reporter.report_status(
                phase="extraction",
                status="discovering",
                message=f"Discovering Python files in {root_path}"
            )

        python_files = self._discover_python_files(root_path)
        logger.info(f"Discovered {len(python_files)} Python files")
        
        if status_reporter:
            status_reporter.report_status(
                phase="extraction",
                status="discovered",
                message=f"Found {len(python_files)} Python files",
                metadata={"file_count": len(python_files)}
            )

        parsed_modules = {}

        # Use parallel processing architecture if configured
        if self.config.parallel_processing and len(python_files) > 1:
            logger.info("Using enhanced parallel processing architecture")
            
            # Create a wrapper function that includes status reporting
            def parse_with_status(file_path: str) -> Optional[ParsedModule]:
                return self.parse_file(file_path, status_reporter)
            
            parsed_modules = self.parallel_processor.process_files(
                python_files, 
                parse_with_status
            )
            
            # Report progress updates from parallel processor
            if status_reporter:
                self.parallel_processor.add_progress_observer(
                    lambda progress: status_reporter.report_progress(
                        current=progress["processed"],
                        total=progress["total"],
                        message=f"Processing files: {progress['processed']}/{progress['total']}"
                    )
                )
        else:
            # Sequential processing for small codebases or when disabled
            for i, file_path in enumerate(python_files):
                if status_reporter:
                    status_reporter.report_progress(
                        current=i,
                        total=len(python_files),
                        message=f"Processing {os.path.basename(file_path)}"
                    )
                    
                try:
                    parsed_module = self.parse_file(file_path, status_reporter)
                    if parsed_module:
                        parsed_modules[file_path] = parsed_module
                except Exception as e:
                    logger.error(f"Error parsing {file_path}: {e}")
                    if status_reporter:
                        status_reporter.report_file_processing(
                            file_path=file_path,
                            status="error",
                            error=str(e)
                        )

        logger.info(f"Successfully parsed {len(parsed_modules)} modules")
        
        # Log processing metrics if parallel processing was used
        if self.config.parallel_processing and len(python_files) > 1:
            metrics = self.parallel_processor.get_metrics()
            logger.info(
                f"Parsing metrics: {metrics.processed_files}/{metrics.total_files} files processed "
                f"({metrics.success_rate:.1f}% success rate) in {metrics.duration:.2f}s "
                f"({metrics.files_per_second:.1f} files/sec)"
            )
            
            if status_reporter:
                status_reporter.report_status(
                    phase="extraction",
                    status="metrics",
                    message="Processing completed",
                    metadata={
                        "total_files": metrics.total_files,
                        "processed_files": metrics.processed_files,
                        "failed_files": metrics.failed_files,
                        "success_rate": metrics.success_rate,
                        "duration": metrics.duration,
                        "files_per_second": metrics.files_per_second
                    }
                )
                
        return parsed_modules

    def parse_file(
        self, 
        file_path: str,
        status_reporter: Optional[StatusReporter] = None
    ) -> Optional[ParsedModule]:
        """
        Parse a single Python file.

        Args:
            file_path: Path to the Python file
            status_reporter: Optional status reporter for progress updates

        Returns:
            Parsed module or None if parsing failed
        """
        file_path = os.path.abspath(file_path)

        # Note: Cache checking is now handled by ParallelProcessor
        # The parse_file method is kept simple and focused

        # Check file size if limit is set
        if self.config.max_file_size > 0:
            file_size = os.path.getsize(file_path)
            if file_size > self.config.max_file_size:
                logger.warning(
                    f"Skipping {file_path}: exceeds size limit "
                    f"({file_size} > {self.config.max_file_size} bytes)"
                )
                if status_reporter:
                    status_reporter.report_file_processing(
                        file_path=file_path,
                        status="skipped",
                        error=f"File too large: {file_size} bytes"
                    )
                return None

        try:
            if status_reporter:
                status_reporter.report_file_processing(
                    file_path=file_path,
                    status="started"
                )
                
            # Use the module parser to parse the file
            parsed_module = self.module_parser.parse(file_path, status_reporter)
            
            if status_reporter:
                status_reporter.report_file_processing(
                    file_path=file_path,
                    status="completed"
                )

            return parsed_module

        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            if status_reporter:
                status_reporter.report_file_processing(
                    file_path=file_path,
                    status="error",
                    error=str(e)
                )
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
                    d for d in dirnames 
                    if d not in ["site-packages", "dist-packages", "node_modules"]
                ]

            for filename in filenames:
                if filename.endswith(".py"):
                    full_path = os.path.join(dirpath, filename)
                    python_files.append(full_path)

        return sorted(python_files)  # Sort for consistent ordering

    def add_progress_observer(self, callback: Callable[[Dict[str, Any]], None]) -> None:
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
        
        Note: This method now delegates to ParallelProcessor's cache.
        The redundant self._cache has been removed.
        
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