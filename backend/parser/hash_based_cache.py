"""
Hash-based Caching System for Task 2.3.

This module implements incremental parsing using content-based hashing to avoid
re-parsing unchanged files. Adapted from example_code/hash_based_file_tracker.py
to integrate with the parallel processing and memory-efficient parsing architecture.

# AI-Intent: Infrastructure:Performance
# Intent: Caching system that tracks file changes and enables incremental parsing
# Confidence: High
# @layer: infrastructure
# @component: caching
# @performance: incremental-parsing
"""

import hashlib
import json
import logging
import gc
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from .config import ParserConfig
from .models import ParsedModule

# Import CodeRelationship - handle import gracefully if not available
try:
    from backend.graph_builder.relationship_extractor import CodeRelationship
except ImportError:
    # Create a simple stub if the relationship extractor is not available
    from dataclasses import dataclass
    from typing import Any, Dict
    
    @dataclass
    class CodeRelationship:
        """Stub for CodeRelationship when relationship extractor is not available."""
        source: str = ""
        target: str = ""
        relationship_type: str = ""
        metadata: Dict[str, Any] = None
        
        def __post_init__(self):
            if self.metadata is None:
                self.metadata = {}

logger = logging.getLogger(__name__)


def _serialize_with_enum_support(obj: Any) -> Any:
    """Recursively serialize objects, converting enums to their values."""
    if isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, dict):
        return {key: _serialize_with_enum_support(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return [_serialize_with_enum_support(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        # Handle dataclass-like objects
        return {key: _serialize_with_enum_support(value) for key, value in obj.__dict__.items()}
    else:
        return obj


@dataclass
class FileHash:
    """Represents a file's hash and metadata."""
    file_path: str
    content_hash: str
    last_modified: float
    size: int
    parsed_at: datetime
    parse_duration: float = 0.0
    relationship_count: int = 0


@dataclass
class CacheEntry:
    """Represents a cached parsing result."""
    file_hash: FileHash
    parsed_module: Optional[ParsedModule]
    relationships: List[CodeRelationship]
    metadata: Dict[str, Any]


class HashBasedCache:
    """
    Hash-based caching system for incremental parsing.
    
    This cache tracks file content hashes to determine if files have changed
    since the last parsing run, enabling efficient incremental processing
    of large codebases.
    """
    
    def __init__(self, config: ParserConfig, cache_dir: Optional[str] = None):
        self.config = config
        
        # Cache configuration
        self.cache_enabled = config.cache_results
        self.cache_dir = Path(cache_dir or ".parser_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache files
        self.hash_cache_file = self.cache_dir / "file_hashes.json"
        self.parsed_cache_dir = self.cache_dir / "parsed_modules"
        self.parsed_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory caches
        self.file_hashes: Dict[str, FileHash] = {}
        self.cached_results: Dict[str, CacheEntry] = {}
        
        # Statistics
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'files_parsed': 0,
            'files_skipped': 0,
            'total_time_saved': 0.0
        }
        
        # Load existing cache
        self._load_hash_cache()
    
    def calculate_file_hash(self, file_path: str) -> Optional[FileHash]:
        """
        Calculate content hash for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            FileHash object or None if file doesn't exist
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.warning(f"File not found for hashing: {file_path}")
            return None
        
        try:
            stat = path.stat()
            
            # Read and hash file content
            with open(path, 'rb') as f:
                content = f.read()
                content_hash = hashlib.sha256(content).hexdigest()
            
            return FileHash(
                file_path=str(path.absolute()),
                content_hash=content_hash,
                last_modified=stat.st_mtime,
                size=stat.st_size,
                parsed_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return None
    
    def has_file_changed(self, file_path: str) -> bool:
        """
        Check if a file has changed since last parsing.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file has changed or is not cached, False otherwise
        """
        if not self.cache_enabled:
            return True
        
        abs_path = str(Path(file_path).absolute())
        
        # Check if we have a cached hash
        if abs_path not in self.file_hashes:
            return True
        
        # Calculate current hash
        current_hash = self.calculate_file_hash(file_path)
        if not current_hash:
            return True
        
        cached_hash = self.file_hashes[abs_path]
        
        # Compare hashes and modification times
        return (current_hash.content_hash != cached_hash.content_hash or
                current_hash.last_modified != cached_hash.last_modified)
    
    def get_cached_result(self, file_path: str) -> Optional[CacheEntry]:
        """
        Get cached parsing result for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            CacheEntry if cached and valid, None otherwise
        """
        if not self.cache_enabled:
            return None
        
        abs_path = str(Path(file_path).absolute())
        
        # Check if file has changed
        if self.has_file_changed(file_path):
            return None
        
        # Try to load cached result
        cached_file = self.parsed_cache_dir / f"{hashlib.md5(abs_path.encode()).hexdigest()}.json"
        
        if not cached_file.exists():
            return None
        
        try:
            with open(cached_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Deserialize the cached entry
            cache_entry = self._deserialize_cache_entry(data)
            self.cached_results[abs_path] = cache_entry
            
            self.stats['cache_hits'] += 1
            logger.debug(f"Cache hit for {file_path}")
            return cache_entry
            
        except Exception as e:
            logger.warning(f"Error loading cached result for {file_path}: {e}")
            # Remove corrupt cache file
            try:
                cached_file.unlink()
            except:
                pass
            return None
    
    def store_result(self, file_path: str, parsed_module: Optional[ParsedModule], 
                    relationships: List[CodeRelationship], parse_duration: float = 0.0) -> bool:
        """
        Store parsing result in cache.
        
        Args:
            file_path: Path to the file
            parsed_module: Parsed module result
            relationships: Extracted relationships
            parse_duration: Time taken to parse (for statistics)
            
        Returns:
            True if stored successfully, False otherwise
        """
        if not self.cache_enabled:
            return False
        
        abs_path = str(Path(file_path).absolute())
        
        try:
            # Calculate file hash
            file_hash = self.calculate_file_hash(file_path)
            if not file_hash:
                return False
            
            file_hash.parse_duration = parse_duration
            file_hash.relationship_count = len(relationships)
            
            # Create cache entry
            cache_entry = CacheEntry(
                file_hash=file_hash,
                parsed_module=parsed_module,
                relationships=relationships,
                metadata={
                    'cached_at': datetime.now().isoformat(),
                    'parser_version': '2.3',
                    'config_hash': self._get_config_hash()
                }
            )
            
            # Store in memory
            self.file_hashes[abs_path] = file_hash
            self.cached_results[abs_path] = cache_entry
            
            # Persist to disk
            cached_file = self.parsed_cache_dir / f"{hashlib.md5(abs_path.encode()).hexdigest()}.json"
            
            with open(cached_file, 'w', encoding='utf-8') as f:
                json.dump(self._serialize_cache_entry(cache_entry), f, indent=2)
            
            self.stats['files_parsed'] += 1
            logger.debug(f"Cached result for {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing cache for {file_path}: {e}")
            return False
    
    def get_changed_files(self, file_paths: List[str]) -> Tuple[List[str], List[str]]:
        """
        Determine which files have changed and which can be loaded from cache.
        
        Args:
            file_paths: List of file paths to check
            
        Returns:
            Tuple of (changed_files, cached_files)
        """
        changed_files = []
        cached_files = []
        
        for file_path in file_paths:
            if self.has_file_changed(file_path):
                changed_files.append(file_path)
            else:
                cached_files.append(file_path)
                self.stats['files_skipped'] += 1
        
        logger.info(f"Cache analysis: {len(changed_files)} changed, {len(cached_files)} cached")
        return changed_files, cached_files
    
    def bulk_load_cached_results(self, file_paths: List[str]) -> Dict[str, CacheEntry]:
        """
        Load multiple cached results efficiently.
        
        Args:
            file_paths: List of file paths to load
            
        Returns:
            Dictionary mapping file paths to cache entries
        """
        results = {}
        
        for file_path in file_paths:
            cache_entry = self.get_cached_result(file_path)
            if cache_entry:
                results[file_path] = cache_entry
                
                # Add to statistics - estimate time saved
                if cache_entry.file_hash.parse_duration > 0:
                    self.stats['total_time_saved'] += cache_entry.file_hash.parse_duration
        
        return results
    
    def invalidate_file(self, file_path: str) -> bool:
        """
        Invalidate cache for a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if invalidated successfully
        """
        abs_path = str(Path(file_path).absolute())
        
        try:
            # Remove from memory caches
            if abs_path in self.file_hashes:
                del self.file_hashes[abs_path]
            if abs_path in self.cached_results:
                del self.cached_results[abs_path]
            
            # Remove cached file
            cached_file = self.parsed_cache_dir / f"{hashlib.md5(abs_path.encode()).hexdigest()}.json"
            if cached_file.exists():
                cached_file.unlink()
            
            logger.debug(f"Invalidated cache for {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error invalidating cache for {file_path}: {e}")
            return False
    
    def clear_cache(self) -> bool:
        """
        Clear all cached data.
        
        Returns:
            True if cleared successfully
        """
        try:
            # Clear memory caches
            self.file_hashes.clear()
            self.cached_results.clear()
            
            # Remove cache files
            if self.hash_cache_file.exists():
                self.hash_cache_file.unlink()
            
            for cache_file in self.parsed_cache_dir.glob("*.json"):
                cache_file.unlink()
            
            # Reset statistics
            self.stats = {
                'cache_hits': 0,
                'cache_misses': 0,
                'files_parsed': 0,
                'files_skipped': 0,
                'total_time_saved': 0.0
            }
            
            logger.info("Cache cleared successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_files = self.stats['cache_hits'] + self.stats['cache_misses']
        hit_rate = (self.stats['cache_hits'] / total_files * 100) if total_files > 0 else 0
        
        return {
            **self.stats,
            'hit_rate_percent': hit_rate,
            'total_cached_files': len(self.file_hashes),
            'cache_size_mb': self._get_cache_size_mb()
        }
    
    def cleanup_stale_cache(self, max_age_days: int = 30) -> int:
        """
        Remove cache entries older than specified age.
        
        Args:
            max_age_days: Maximum age of cache entries in days
            
        Returns:
            Number of entries removed
        """
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
        removed_count = 0
        
        stale_files = []
        for file_path, file_hash in self.file_hashes.items():
            if file_hash.parsed_at.timestamp() < cutoff_time:
                stale_files.append(file_path)
        
        for file_path in stale_files:
            if self.invalidate_file(file_path):
                removed_count += 1
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} stale cache entries")
        
        return removed_count
    
    def _load_hash_cache(self):
        """Load hash cache from disk."""
        if not self.hash_cache_file.exists():
            return
        
        try:
            with open(self.hash_cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for file_path, hash_data in data.get('file_hashes', {}).items():
                self.file_hashes[file_path] = FileHash(
                    file_path=hash_data['file_path'],
                    content_hash=hash_data['content_hash'],
                    last_modified=hash_data['last_modified'],
                    size=hash_data['size'],
                    parsed_at=datetime.fromisoformat(hash_data['parsed_at']),
                    parse_duration=hash_data.get('parse_duration', 0.0),
                    relationship_count=hash_data.get('relationship_count', 0)
                )
            
            logger.debug(f"Loaded {len(self.file_hashes)} cached file hashes")
            
        except Exception as e:
            logger.warning(f"Error loading hash cache: {e}")
            self.file_hashes.clear()
    
    def save_hash_cache(self):
        """Save hash cache to disk."""
        if not self.cache_enabled:
            return
        
        try:
            cache_data = {
                'version': '2.3',
                'saved_at': datetime.now().isoformat(),
                'file_hashes': {}
            }
            
            for file_path, file_hash in self.file_hashes.items():
                cache_data['file_hashes'][file_path] = asdict(file_hash)
                # Convert datetime to string
                cache_data['file_hashes'][file_path]['parsed_at'] = file_hash.parsed_at.isoformat()
            
            with open(self.hash_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.debug(f"Saved hash cache with {len(self.file_hashes)} entries")
            
        except Exception as e:
            logger.error(f"Error saving hash cache: {e}")
    
    def _get_config_hash(self) -> str:
        """Generate hash of parser configuration for cache validation."""
        config_str = json.dumps(asdict(self.config), sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()[:8]
    
    def _get_cache_size_mb(self) -> float:
        """Calculate total cache size in MB."""
        total_size = 0
        
        try:
            if self.hash_cache_file.exists():
                total_size += self.hash_cache_file.stat().st_size
            
            for cache_file in self.parsed_cache_dir.glob("*.json"):
                total_size += cache_file.stat().st_size
        except:
            pass
        
        return total_size / (1024 * 1024)
    
    def _serialize_cache_entry(self, entry: CacheEntry) -> Dict[str, Any]:
        """Serialize cache entry for JSON storage."""
        return {
            'file_hash': {
                **_serialize_with_enum_support(asdict(entry.file_hash)),
                'parsed_at': entry.file_hash.parsed_at.isoformat()
            },
            'parsed_module': _serialize_with_enum_support(asdict(entry.parsed_module)) if entry.parsed_module else None,
            'relationships': [_serialize_with_enum_support(asdict(rel)) for rel in entry.relationships],
            'metadata': _serialize_with_enum_support(entry.metadata)
        }
    
    def _deserialize_cache_entry(self, data: Dict[str, Any]) -> CacheEntry:
        """Deserialize cache entry from JSON data."""
        file_hash_data = data['file_hash']
        file_hash = FileHash(
            file_path=file_hash_data['file_path'],
            content_hash=file_hash_data['content_hash'],
            last_modified=file_hash_data['last_modified'],
            size=file_hash_data['size'],
            parsed_at=datetime.fromisoformat(file_hash_data['parsed_at']),
            parse_duration=file_hash_data.get('parse_duration', 0.0),
            relationship_count=file_hash_data.get('relationship_count', 0)
        )
        
        # Deserialize parsed module
        parsed_module = None
        if data['parsed_module']:
            # This would need proper deserialization of ParsedModule
            # For now, storing as dict - full implementation would recreate object
            parsed_module = data['parsed_module']
        
        # Deserialize relationships
        relationships = []
        for rel_data in data['relationships']:
            relationships.append(CodeRelationship(**rel_data))
        
        return CacheEntry(
            file_hash=file_hash,
            parsed_module=parsed_module,
            relationships=relationships,
            metadata=data['metadata']
        )
    
    def __del__(self):
        """Ensure hash cache is saved on cleanup."""
        try:
            # Only try to save if we have the necessary attributes and builtins are still available
            if hasattr(self, 'cache_enabled') and hasattr(self, 'file_hashes') and hasattr(self, 'hash_cache_file'):
                self.save_hash_cache()
        except:
            # Silently ignore all errors during cleanup
            pass
