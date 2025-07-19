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

        # Use parallel processing if configured
        if self.config.parallel_processing and len(python_files) > 1:
            parsed_modules = self._parse_in_parallel(python_files)
        else:
            for file_path in python_files:
                try:
                    parsed_module = self.parse_file(file_path)
                    if parsed_module:
                        parsed_modules[file_path] = parsed_module
                except Exception as e:
                    logger.error(f"Error parsing {file_path}: {e}")

        logger.info(f"Successfully parsed {len(parsed_modules)} modules")
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
        Parse multiple files in parallel using thread pool.

        Args:
            file_paths: List of file paths to parse

        Returns:
            Dictionary mapping file paths to parsed modules
        """
        parsed_modules = {}
        max_workers = min(os.cpu_count() or 1, len(file_paths))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_path = {
                executor.submit(self.parse_file, path): path for path in file_paths
            }

            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    result = future.result()
                    if result:
                        parsed_modules[path] = result
                except Exception as e:
                    logger.error(f"Error parsing {path}: {e}")

        return parsed_modules

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
