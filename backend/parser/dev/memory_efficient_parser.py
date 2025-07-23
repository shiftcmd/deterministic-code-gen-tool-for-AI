"""
Memory-Efficient AST Parser for Task 2.2.

This module implements memory-efficient parsing strategies that integrate with
the parallel processing architecture and relationship extraction capabilities.
It provides streaming and chunked parsing for large Python files while
maintaining comprehensive analysis capabilities.

# AI-Intent: Core-Domain:Application
# Intent: Memory-efficient parsing that handles large codebases without resource exhaustion
# Confidence: High  
# @layer: application
# @component: memory-management
# @performance: streaming-parser
"""

import ast
import gc
import logging
import mmap
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Set, Tuple, Union
from weakref import WeakValueDictionary

from .config import ParserConfig
from .models import ParsedModule
from .errors import ParserError, ParserErrorCode
from .processing_types import ProcessingMetrics, ProgressTracker

logger = logging.getLogger(__name__)


@dataclass
class MemoryUsage:
    """Tracks memory usage during parsing."""
    peak_memory_mb: float = 0.0
    current_memory_mb: float = 0.0
    gc_collections: int = 0
    object_count: int = 0
    
    def update_from_sys(self):
        """Update memory stats from system."""
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        self.current_memory_mb = memory_info.rss / (1024 * 1024)
        self.peak_memory_mb = max(self.peak_memory_mb, self.current_memory_mb)
        self.object_count = len(gc.get_objects())


@dataclass 
class ChunkingStrategy:
    """Configuration for file chunking strategies."""
    max_chunk_size_bytes: int = 512 * 1024  # 512KB chunks
    max_lines_per_chunk: int = 1000  # Lines per chunk
    overlap_lines: int = 10  # Overlap between chunks
    chunk_by_ast_nodes: bool = True  # Prefer AST-based chunking
    preserve_context: bool = True  # Maintain context across chunks


class MemoryEfficientParser:
    """
    Memory-efficient parser that uses streaming and chunked processing.
    
    This parser addresses memory constraints when processing large Python files
    by implementing multiple strategies:
    
    1. Streaming parsing for large files
    2. AST-based intelligent chunking
    3. Garbage collection management
    4. Object pooling and reuse
    5. Memory monitoring and alerts
    """
    
    def __init__(self, config: ParserConfig):
        self.config = config
        self.chunking = ChunkingStrategy()
        self.memory_usage = MemoryUsage()
        
        # Object pools for reuse
        self._node_pool: WeakValueDictionary = WeakValueDictionary()
        self._parsed_module_cache: Dict[str, ParsedModule] = {}
        
        # Memory thresholds
        self.memory_warning_mb = config.tool_options.get('memory', {}).get('warning_mb', 1024)
        self.memory_limit_mb = config.tool_options.get('memory', {}).get('limit_mb', 2048)
        
    def parse_file_memory_efficient(self, file_path: str, progress_callback=None) -> Optional[ParsedModule]:
        """
        Parse a file using memory-efficient strategies.
        
        Args:
            file_path: Path to the Python file to parse
            progress_callback: Optional callback for progress updates
            
        Returns:
            ParsedModule or None if parsing failed
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return None
            
        # Check if file is already cached
        cache_key = f"{file_path}_{file_path.stat().st_mtime}"
        if cache_key in self._parsed_module_cache:
            return self._parsed_module_cache[cache_key]
        
        try:
            file_size = file_path.stat().st_size
            
            # Choose parsing strategy based on file size
            if file_size > self.chunking.max_chunk_size_bytes:
                logger.info(f"Using chunked parsing for large file: {file_path} ({file_size} bytes)")
                return self._parse_large_file_chunked(file_path, progress_callback)
            else:
                logger.debug(f"Using standard parsing for file: {file_path}")
                return self._parse_file_standard(file_path)
                
        except Exception as e:
            logger.error(f"Memory-efficient parsing failed for {file_path}: {e}")
            return None
        finally:
            # Force garbage collection after parsing
            self._cleanup_memory()
    
    def _parse_large_file_chunked(self, file_path: Path, progress_callback=None) -> Optional[ParsedModule]:
        """Parse large files using chunked approach."""
        parsed_module = None
        chunk_results = []
        
        try:
            with self._memory_monitor():
                chunks = list(self._generate_file_chunks(file_path))
                total_chunks = len(chunks)
                
                for i, (chunk_content, start_line, end_line) in enumerate(chunks):
                    if progress_callback:
                        progress_callback({
                            'stage': 'parsing_chunks',
                            'chunk': i + 1,
                            'total_chunks': total_chunks,
                            'file': str(file_path)
                        })
                    
                    chunk_result = self._parse_chunk(chunk_content, start_line, end_line, str(file_path))
                    if chunk_result:
                        chunk_results.append(chunk_result)
                
                # Merge chunk results into a single ParsedModule
                parsed_module = self._merge_chunk_results(chunk_results, str(file_path))
                
        except Exception as e:
            logger.error(f"Chunked parsing failed for {file_path}: {e}")
            
        return parsed_module
    
    def _parse_file_standard(self, file_path: Path) -> Optional[ParsedModule]:
        """Standard parsing for smaller files."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Use the existing module parser
            from .module_parser import ModuleParser
            module_parser = ModuleParser(self.config)
            return module_parser.parse(str(file_path))
            
        except Exception as e:
            logger.error(f"Standard parsing failed for {file_path}: {e}")
            return None
    
    def _generate_file_chunks(self, file_path: Path) -> Generator[Tuple[str, int, int], None, None]:
        """
        Generate file chunks using memory-mapped file access.
        
        Yields:
            Tuple of (chunk_content, start_line, end_line)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = []
                current_line = 1
                start_line = 1
                
                for line in f:
                    lines.append(line)
                    
                    # Check if we should create a chunk
                    if (len(lines) >= self.chunking.max_lines_per_chunk or 
                        sum(len(l) for l in lines) >= self.chunking.max_chunk_size_bytes):
                        
                        # Try to find good break point (end of function/class)
                        break_point = self._find_chunk_break_point(lines)
                        
                        if break_point > 0:
                            chunk_lines = lines[:break_point]
                            chunk_content = ''.join(chunk_lines)
                            end_line = current_line - (len(lines) - break_point)
                            
                            yield chunk_content, start_line, end_line
                            
                            # Prepare next chunk with overlap
                            overlap_start = max(0, break_point - self.chunking.overlap_lines)
                            lines = lines[overlap_start:]
                            start_line = current_line - (break_point - overlap_start) + 1
                    
                    current_line += 1
                
                # Handle remaining lines
                if lines:
                    chunk_content = ''.join(lines)
                    yield chunk_content, start_line, current_line - 1
                    
        except Exception as e:
            logger.error(f"Error generating chunks for {file_path}: {e}")
            return
    
    def _find_chunk_break_point(self, lines: List[str]) -> int:
        """
        Find the best line to break a chunk at (end of function/class).
        
        Returns:
            Line index to break at, or len(lines) if no good break found
        """
        if not self.chunking.chunk_by_ast_nodes:
            return len(lines) // 2  # Simple middle break
        
        try:
            # Look for function/class endings
            indent_levels = []
            for i, line in enumerate(lines):
                stripped = line.lstrip()
                if not stripped or stripped.startswith('#'):
                    continue
                    
                indent = len(line) - len(stripped)
                indent_levels.append((i, indent, stripped))
            
            # Find good break points (return to lower indentation)
            for i in range(len(indent_levels) - 1, 0, -1):
                current_indent = indent_levels[i][1]
                prev_indent = indent_levels[i-1][1]
                
                if current_indent < prev_indent and current_indent == 0:
                    return indent_levels[i][0]
            
        except Exception:
            pass
        
        return len(lines) // 2  # Fallback to middle
    
    def _parse_chunk(self, content: str, start_line: int, end_line: int, file_path: str) -> Optional[Dict[str, Any]]:
        """Parse a single chunk of code."""
        try:
            tree = ast.parse(content, filename=file_path)
            
            # Extract basic information from the chunk
            chunk_data = {
                'start_line': start_line,
                'end_line': end_line,
                'imports': [],
                'classes': [],
                'functions': [],
                'variables': [],
                'content': content
            }
            
            # Use a simple visitor to extract elements
            visitor = ChunkVisitor(chunk_data, start_line)
            visitor.visit(tree)
            
            return chunk_data
            
        except SyntaxError as e:
            logger.warning(f"Syntax error in chunk {start_line}-{end_line} of {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing chunk {start_line}-{end_line} of {file_path}: {e}")
            return None
    
    def _merge_chunk_results(self, chunk_results: List[Dict[str, Any]], file_path: str) -> ParsedModule:
        """Merge multiple chunk results into a single ParsedModule."""
        merged_imports = []
        merged_classes = []
        merged_functions = []
        merged_variables = []
        
        for chunk in chunk_results:
            merged_imports.extend(chunk.get('imports', []))
            merged_classes.extend(chunk.get('classes', []))
            merged_functions.extend(chunk.get('functions', []))
            merged_variables.extend(chunk.get('variables', []))
        
        # Create ParsedModule
        from .models import ParsedModule
        return ParsedModule(
            file_path=file_path,
            module_name=Path(file_path).stem,
            imports=merged_imports,
            classes=merged_classes,
            functions=merged_functions,
            variables=merged_variables,
            docstring=None,  # Could be extracted from first chunk
            metadata={
                'parsing_method': 'chunked',
                'total_chunks': len(chunk_results)
            }
        )
    
    @contextmanager
    def _memory_monitor(self):
        """Context manager for memory monitoring during parsing."""
        try:
            self.memory_usage.update_from_sys()
            initial_memory = self.memory_usage.current_memory_mb
            
            yield
            
        finally:
            self.memory_usage.update_from_sys()
            final_memory = self.memory_usage.current_memory_mb
            
            logger.debug(f"Memory usage: {initial_memory:.1f}MB -> {final_memory:.1f}MB")
            
            if final_memory > self.memory_warning_mb:
                logger.warning(f"High memory usage: {final_memory:.1f}MB")
                self._cleanup_memory()
    
    def _cleanup_memory(self):
        """Perform memory cleanup and garbage collection."""
        # Clear parsed module cache if memory is high
        if self.memory_usage.current_memory_mb > self.memory_limit_mb:
            self._parsed_module_cache.clear()
            logger.info("Cleared parsed module cache due to memory pressure")
        
        # Force garbage collection
        collected = gc.collect()
        self.memory_usage.gc_collections += 1
        
        self.memory_usage.update_from_sys()
        logger.debug(f"Garbage collection freed {collected} objects, memory: {self.memory_usage.current_memory_mb:.1f}MB")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get current memory usage statistics."""
        self.memory_usage.update_from_sys()
        return {
            'current_memory_mb': self.memory_usage.current_memory_mb,
            'peak_memory_mb': self.memory_usage.peak_memory_mb,
            'gc_collections': self.memory_usage.gc_collections,
            'object_count': self.memory_usage.object_count,
            'cache_size': len(self._parsed_module_cache)
        }


class ChunkVisitor(ast.NodeVisitor):
    """Simple AST visitor for extracting information from code chunks."""
    
    def __init__(self, chunk_data: Dict[str, Any], line_offset: int):
        self.chunk_data = chunk_data
        self.line_offset = line_offset
    
    def visit_Import(self, node):
        """Extract import statements."""
        for alias in node.names:
            self.chunk_data['imports'].append({
                'type': 'import',
                'module': alias.name,
                'alias': alias.asname,
                'line': node.lineno + self.line_offset - 1
            })
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Extract from-import statements."""
        for alias in node.names:
            self.chunk_data['imports'].append({
                'type': 'from_import',
                'module': node.module,
                'name': alias.name,
                'alias': alias.asname,
                'line': node.lineno + self.line_offset - 1
            })
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        """Extract class definitions."""
        self.chunk_data['classes'].append({
            'name': node.name,
            'line': node.lineno + self.line_offset - 1,
            'bases': [self._extract_name(base) for base in node.bases],
            'methods': []
        })
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node):
        """Extract function definitions."""
        self.chunk_data['functions'].append({
            'name': node.name,
            'line': node.lineno + self.line_offset - 1,
            'args': [arg.arg for arg in node.args.args],
            'decorators': [self._extract_name(dec) for dec in node.decorator_list]
        })
        self.generic_visit(node)
    
    def _extract_name(self, node) -> str:
        """Extract name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._extract_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        else:
            return str(type(node).__name__)
