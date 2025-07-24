"""
Cache service for transformation results.

Provides caching capabilities to avoid redundant transformations
and improve performance for repeated operations.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from ..models.tuples import TupleSet

logger = logging.getLogger(__name__)


class CacheService:
    """Service for caching transformation results."""
    
    def __init__(self, cache_directory: str = ".cache", ttl_hours: int = 24):
        """
        Initialize cache service.
        
        Args:
            cache_directory: Directory to store cache files
            ttl_hours: Time-to-live for cached results in hours
        """
        self.cache_dir = Path(cache_directory)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
    
    def get_cache_key(self, extraction_data: Dict[str, Any]) -> str:
        """
        Generate cache key for extraction data.
        
        Args:
            extraction_data: Extraction data to generate key for
            
        Returns:
            Cache key string
        """
        # Create a deterministic hash of the extraction data
        data_str = json.dumps(extraction_data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def is_cached(self, cache_key: str) -> bool:
        """
        Check if results are cached and still valid.
        
        Args:
            cache_key: Cache key to check
            
        Returns:
            True if cached and valid, False otherwise
        """
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return False
        
        try:
            # Check if cache is still valid (not expired)
            cache_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if datetime.now() - cache_time > self.ttl:
                logger.debug(f"Cache expired for key: {cache_key}")
                cache_file.unlink()  # Remove expired cache
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error checking cache validity: {e}")
            return False
    
    def get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached transformation result.
        
        Args:
            cache_key: Cache key to retrieve
            
        Returns:
            Cached result data or None if not found
        """
        if not self.is_cached(cache_key):
            return None
        
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
            
            logger.debug(f"Retrieved cached result for key: {cache_key}")
            return cached_data
            
        except Exception as e:
            logger.error(f"Error reading cached result: {e}")
            return None
    
    def cache_result(
        self, 
        cache_key: str, 
        tuple_set: TupleSet, 
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Cache transformation result.
        
        Args:
            cache_key: Cache key to store under
            tuple_set: TupleSet to cache
            metadata: Additional metadata to cache
            
        Returns:
            True if cached successfully, False otherwise
        """
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            cache_data = {
                "tuple_set": tuple_set.to_dict(),
                "metadata": metadata,
                "cached_at": datetime.now().isoformat()
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.debug(f"Cached result for key: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching result: {e}")
            return False
    
    def clear_cache(self) -> int:
        """
        Clear all cached results.
        
        Returns:
            Number of cache files removed
        """
        removed_count = 0
        
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
                removed_count += 1
            
            logger.info(f"Cleared {removed_count} cached results")
            return removed_count
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return removed_count
    
    def clear_expired_cache(self) -> int:
        """
        Clear only expired cached results.
        
        Returns:
            Number of expired cache files removed
        """
        removed_count = 0
        
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if datetime.now() - cache_time > self.ttl:
                    cache_file.unlink()
                    removed_count += 1
            
            logger.info(f"Cleared {removed_count} expired cached results")
            return removed_count
            
        except Exception as e:
            logger.error(f"Error clearing expired cache: {e}")
            return removed_count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            total_size = sum(f.stat().st_size for f in cache_files)
            
            valid_count = 0
            expired_count = 0
            
            for cache_file in cache_files:
                cache_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if datetime.now() - cache_time > self.ttl:
                    expired_count += 1
                else:
                    valid_count += 1
            
            return {
                "total_files": len(cache_files),
                "valid_files": valid_count,
                "expired_files": expired_count,
                "total_size_bytes": total_size,
                "cache_directory": str(self.cache_dir),
                "ttl_hours": self.ttl.total_seconds() / 3600
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}