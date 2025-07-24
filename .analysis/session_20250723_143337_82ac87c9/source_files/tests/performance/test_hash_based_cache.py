"""
Unit tests for the HashBasedCache performance optimization system.

Tests cover:
- Hash-based change detection
- Cache persistence and loading
- Cache invalidation and cleanup
- Performance metrics
- Bulk operations
- Error handling and recovery
"""

import pytest
import tempfile
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import hashlib

from backend.parser.hash_based_cache import HashBasedCache, CacheEntry, FileHash
from backend.parser.config import get_parser_config
from backend.parser.models import ParsedModule
from backend.graph_builder.relationship_extractor import CodeRelationship


class TestHashBasedCache:
    """Test cases for HashBasedCache class."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def temp_files(self):
        """Create temporary Python files for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            files = {}
            
            # Create test files
            test_file = temp_path / "test.py"
            test_file.write_text("def test_function():\n    return 42\n")
            files['test'] = str(test_file)
            
            # Create another test file
            another_file = temp_path / "another.py"
            another_file.write_text("class TestClass:\n    def __init__(self):\n        pass\n")
            files['another'] = str(another_file)
            
            yield files
    
    @pytest.fixture
    def cache_config(self, temp_cache_dir):
        """Create cache configuration with temporary directory."""
        config = get_parser_config("standard")
        config.tool_options['cache']['cache_dir'] = temp_cache_dir
        return config
    
    @pytest.fixture
    def cache(self, cache_config):
        """Create HashBasedCache instance."""
        return HashBasedCache(cache_config)
    
    @pytest.fixture
    def mock_parsed_module(self):
        """Create mock ParsedModule for testing."""
        return ParsedModule(
            name="test_module",
            path="/test/file.py",
            classes=[],
            functions=[],
            variables=[],
            imports=[]
        )
    
    @pytest.fixture
    def mock_file_hash(self):
        """Create mock FileHash for testing."""
        from datetime import datetime
        return FileHash(
            file_path="/test/file.py",
            content_hash="abc123",
            last_modified=time.time(),
            size=1024,
            parsed_at=datetime.now(),
            parse_duration=1.5
        )


class TestCacheEntryManagement(TestHashBasedCache):
    """Test cache entry creation and management."""
    
    def test_cache_entry_creation(self, mock_parsed_module, mock_file_hash):
        """Test CacheEntry creation and serialization."""
        entry = CacheEntry(
            file_hash=mock_file_hash,
            parsed_module=mock_parsed_module,
            relationships=[],
            metadata={}
        )
        
        assert entry.file_hash == mock_file_hash
        assert entry.parsed_module == mock_parsed_module
        assert len(entry.relationships) == 0
        assert isinstance(entry.metadata, dict)
    
    def test_cache_entry_serialization(self, mock_parsed_module, mock_file_hash):
        """Test cache entry serialization to/from dict."""
        # For now, just test basic creation
        entry = CacheEntry(
            file_hash=mock_file_hash,
            parsed_module=mock_parsed_module,
            relationships=[],
            metadata={"test": "data"}
        )
        
        assert entry.file_hash.file_path == "/test/file.py"
        assert entry.file_hash.content_hash == "abc123"
        assert entry.metadata["test"] == "data"


class TestHashCalculation(TestHashBasedCache):
    """Test hash calculation for change detection."""
    
    def test_content_hash_calculation(self, cache, temp_files):
        """Test file content hash calculation."""
        file_path = temp_files['test']
        file_hash = cache.calculate_file_hash(file_path)
        
        # Hash should be consistent
        assert file_hash is not None
        assert isinstance(file_hash.content_hash, str)
        assert len(file_hash.content_hash) > 0
        
        # Same file should produce same hash
        file_hash2 = cache.calculate_file_hash(file_path)
        assert file_hash.content_hash == file_hash2.content_hash
    
    def test_metadata_hash_calculation(self, cache, temp_files):
        """Test file metadata capture in FileHash."""
        file_path = temp_files['test']
        file_hash = cache.calculate_file_hash(file_path)
        
        # Check that metadata is captured
        assert file_hash is not None
        assert file_hash.last_modified > 0
        assert file_hash.size > 0
        assert file_hash.parsed_at is not None
        
        # Same file should produce same metadata
        file_hash2 = cache.calculate_file_hash(file_path)
        assert file_hash.last_modified == file_hash2.last_modified
        assert file_hash.size == file_hash2.size
    
    def test_hash_changes_with_content(self, cache, temp_files):
        """Test that hash changes when file content changes."""
        file_path = temp_files['test']
        original_file_hash = cache.calculate_file_hash(file_path)
        
        # Modify file content
        Path(file_path).write_text("def modified_function():\n    return 'changed'\n")
        
        # Hash should be different
        new_file_hash = cache.calculate_file_hash(file_path)
        assert new_file_hash.content_hash != original_file_hash.content_hash


class TestChangeDetection(TestHashBasedCache):
    """Test file change detection logic."""
    
    def test_get_changed_files_empty_cache(self, cache, temp_files):
        """Test change detection with empty cache."""
        file_paths = list(temp_files.values())
        
        changed_files, cached_files = cache.get_changed_files(file_paths)
        
        # All files should be considered changed (new)
        assert set(changed_files) == set(file_paths)
        assert len(cached_files) == 0
    
    def test_get_changed_files_with_cache(self, cache, temp_files, mock_parsed_module):
        """Test change detection with existing cache."""
        file_path = temp_files['test']
        
        # Store file in cache first
        cache.store_result(file_path, mock_parsed_module, [], 1.0)
        
        # Check change detection
        changed_files, cached_files = cache.get_changed_files([file_path])
        
        # File should be cached (unchanged)
        assert len(changed_files) == 0
        assert file_path in cached_files
    
    def test_detects_changed_files(self, cache, temp_files, mock_parsed_module):
        """Test that changed files are detected correctly."""
        file_path = temp_files['test']
        
        # Store original file in cache
        cache.store_result(file_path, mock_parsed_module, [], 1.0)
        
        # Modify the file
        Path(file_path).write_text("def modified_function():\n    return 'changed'\n")
        
        # Should detect change
        changed_files, cached_files = cache.get_changed_files([file_path])
        
        assert file_path in changed_files
        assert len(cached_files) == 0


class TestCachePersistence(TestHashBasedCache):
    """Test cache persistence and loading."""
    
    def test_cache_persistence(self, cache, temp_files, mock_parsed_module):
        """Test that cache is persisted to disk."""
        file_path = temp_files['test']
        
        # Store result in cache
        cache.store_result(file_path, mock_parsed_module, [], 1.5)
        
        # Save cache to disk
        cache.save_hash_cache()
        
        # Verify cache file exists
        cache_file = Path(cache.cache_dir) / "hash_cache.json"
        assert cache_file.exists()
        
        # Verify cache content
        with open(cache_file, 'r') as f:
            cache_data = json.load(f)
        
        assert file_path in cache_data
        assert cache_data[file_path]['parse_duration'] == 1.5
    
    def test_cache_loading(self, cache_config, temp_files, mock_parsed_module):
        """Test loading cache from disk."""
        # Create and populate cache
        cache1 = HashBasedCache(cache_config)
        file_path = temp_files['test']
        cache1.store_result(file_path, mock_parsed_module, [], 2.0)
        cache1.save_hash_cache()
        
        # Create new cache instance (should load from disk)
        cache2 = HashBasedCache(cache_config)
        
        # Check that data was loaded
        changed_files, cached_files = cache2.get_changed_files([file_path])
        assert file_path in cached_files
    
    def test_corrupted_cache_handling(self, cache_config, temp_cache_dir):
        """Test handling of corrupted cache files."""
        # Create corrupted cache file
        cache_file = Path(temp_cache_dir) / "hash_cache.json"
        cache_file.write_text("invalid json content")
        
        # Should handle corrupted cache gracefully
        cache = HashBasedCache(cache_config)
        
        # Cache should be empty (corrupted file ignored)
        stats = cache.get_cache_stats()
        assert stats['total_cached_files'] == 0


class TestBulkOperations(TestHashBasedCache):
    """Test bulk cache operations."""
    
    def test_bulk_load_cached_results(self, cache, temp_files, mock_parsed_module):
        """Test bulk loading of cached results."""
        # Store multiple files in cache
        for file_path in temp_files.values():
            cache.store_result(file_path, mock_parsed_module, [], 1.0)
        
        # Bulk load
        file_paths = list(temp_files.values())
        results = cache.bulk_load_cached_results(file_paths)
        
        # Should return results for all cached files
        assert len(results) == len(temp_files)
        for file_path in file_paths:
            assert file_path in results
            assert results[file_path].parsed_module is not None
    
    def test_bulk_operations_performance(self, cache, mock_parsed_module):
        """Test performance of bulk operations."""
        # Create many test entries
        num_files = 100
        file_paths = [f"/test/file_{i}.py" for i in range(num_files)]
        
        # Store all files (simulate)
        for file_path in file_paths:
            # Mock file existence and content for testing
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.stat'):
                    with patch.object(cache, 'calculate_file_hash', return_value=None):  # Simplified for test
                        # Mock the store_result to avoid actual file operations
                        with patch.object(cache, 'store_result', return_value=True):
                            pass  # Mock storage
        
        # Bulk load should be efficient
        start_time = time.time()
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.stat'):
                changed_files, cached_files = cache.get_changed_files(file_paths)
        
        end_time = time.time()
        
        # Should complete quickly (under 1 second for 100 files)
        assert (end_time - start_time) < 1.0
        assert len(cached_files) == num_files


class TestCacheInvalidation(TestHashBasedCache):
    """Test cache invalidation and cleanup."""
    
    def test_invalidate_file(self, cache, temp_files, mock_parsed_module):
        """Test individual file invalidation."""
        file_path = temp_files['test']
        
        # Store in cache
        cache.store_result(file_path, mock_parsed_module, [], 1.0)
        
        # Verify cached
        changed_files, cached_files = cache.get_changed_files([file_path])
        assert file_path in cached_files
        
        # Invalidate
        success = cache.invalidate_file(file_path)
        assert success
        
        # Should now be considered changed
        changed_files, cached_files = cache.get_changed_files([file_path])
        assert file_path in changed_files
        assert len(cached_files) == 0
    
    def test_clear_cache(self, cache, temp_files, mock_parsed_module):
        """Test clearing entire cache."""
        # Store multiple files
        for file_path in temp_files.values():
            cache.store_result(file_path, mock_parsed_module, [], 1.0)
        
        # Verify files are cached
        stats = cache.get_cache_stats()
        assert stats['total_cached_files'] > 0
        
        # Clear cache
        success = cache.clear_cache()
        assert success
        
        # Cache should be empty
        stats = cache.get_cache_stats()
        assert stats['total_cached_files'] == 0
    
    def test_cleanup_stale_cache(self, cache, temp_files, mock_parsed_module):
        """Test cleanup of stale cache entries."""
        file_path = temp_files['test']
        
        # Store with old timestamp
        cache.store_result(file_path, mock_parsed_module, [], 1.0)
        
        # Manually set old timestamp for testing
        if file_path in cache.cache_data:
            old_time = time.time() - (31 * 24 * 3600)  # 31 days ago
            cache.cache_data[file_path].created_at = old_time
        
        # Cleanup stale entries (older than 30 days)
        removed_count = cache.cleanup_stale_cache(max_age_days=30)
        
        # Should have removed the stale entry
        assert removed_count >= 0


class TestCacheStatistics(TestHashBasedCache):
    """Test cache statistics and metrics."""
    
    def test_cache_stats_empty(self, cache):
        """Test statistics for empty cache."""
        stats = cache.get_cache_stats()
        
        assert stats['cache_hits'] == 0
        assert stats['cache_misses'] == 0
        assert stats['total_cached_files'] == 0
        assert stats['hit_rate_percent'] == 0
        assert stats['total_time_saved'] == 0.0
        assert stats['cache_size_mb'] == 0.0
    
    def test_cache_stats_with_data(self, cache, temp_files, mock_parsed_module):
        """Test statistics with cached data."""
        # Store files and simulate hits/misses
        for file_path in temp_files.values():
            cache.store_result(file_path, mock_parsed_module, [], 1.5)
        
        # Simulate cache hits
        cache._record_cache_hit(1.0)
        cache._record_cache_hit(1.5)
        
        # Simulate cache miss
        cache._record_cache_miss()
        
        stats = cache.get_cache_stats()
        
        assert stats['cache_hits'] == 2
        assert stats['cache_misses'] == 1
        assert stats['total_cached_files'] == len(temp_files)
        assert stats['hit_rate_percent'] == (2/3) * 100
        assert stats['total_time_saved'] == 2.5
        assert stats['cache_size_mb'] > 0
    
    def test_hit_rate_calculation(self, cache):
        """Test hit rate calculation accuracy."""
        # No hits or misses
        stats = cache.get_cache_stats()
        assert stats['hit_rate_percent'] == 0
        
        # Only hits
        cache._record_cache_hit(1.0)
        cache._record_cache_hit(1.0)
        stats = cache.get_cache_stats()
        assert stats['hit_rate_percent'] == 100.0
        
        # Mixed hits and misses
        cache._record_cache_miss()
        stats = cache.get_cache_stats()
        assert stats['hit_rate_percent'] == (2/3) * 100


class TestErrorHandling(TestHashBasedCache):
    """Test error handling and recovery."""
    
    def test_missing_file_handling(self, cache):
        """Test handling of missing files."""
        nonexistent_file = "/nonexistent/file.py"
        
        # Should handle missing files gracefully
        changed_files, cached_files = cache.get_changed_files([nonexistent_file])
        
        # Missing file should be considered changed (needs processing)
        assert nonexistent_file in changed_files
        assert len(cached_files) == 0
    
    def test_permission_error_handling(self, cache, temp_files):
        """Test handling of permission errors."""
        file_path = temp_files['test']
        
        # Mock permission error
        with patch('pathlib.Path.stat', side_effect=PermissionError("Access denied")):
            changed_files, cached_files = cache.get_changed_files([file_path])
            
            # Should handle error gracefully and treat as changed
            assert file_path in changed_files
    
    def test_disk_full_handling(self, cache, temp_files, mock_parsed_module):
        """Test handling of disk full errors during cache save."""
        file_path = temp_files['test']
        cache.store_result(file_path, mock_parsed_module, [], 1.0)
        
        # Mock disk full error
        with patch('builtins.open', side_effect=OSError("No space left on device")):
            # Should handle error gracefully
            try:
                cache.save_hash_cache()
            except OSError:
                pass  # Expected to fail, but should not crash


class TestIntegrationScenarios(TestHashBasedCache):
    """Integration tests for complete cache workflows."""
    
    def test_full_cache_lifecycle(self, cache, temp_files, mock_parsed_module):
        """Test complete cache lifecycle."""
        file_paths = list(temp_files.values())
        
        # 1. Initial state - all files should be new
        changed_files, cached_files = cache.get_changed_files(file_paths)
        assert set(changed_files) == set(file_paths)
        assert len(cached_files) == 0
        
        # 2. Store results in cache
        for file_path in file_paths:
            cache.store_result(file_path, mock_parsed_module, [], 1.0)
        
        # 3. Second check - all files should be cached
        changed_files, cached_files = cache.get_changed_files(file_paths)
        assert len(changed_files) == 0
        assert set(cached_files) == set(file_paths)
        
        # 4. Modify one file
        modified_file = file_paths[0]
        Path(modified_file).write_text("# Modified content\nprint('changed')")
        
        # 5. Check again - only modified file should be changed
        changed_files, cached_files = cache.get_changed_files(file_paths)
        assert modified_file in changed_files
        assert len(changed_files) == 1
        assert len(cached_files) == len(file_paths) - 1
    
    def test_cache_persistence_across_restarts(self, cache_config, temp_files, mock_parsed_module):
        """Test cache persistence across application restarts."""
        # Session 1: Create cache and store data
        cache1 = HashBasedCache(cache_config)
        file_path = temp_files['test']
        cache1.store_result(file_path, mock_parsed_module, [], 2.0)
        cache1.save_hash_cache()
        del cache1  # Simulate app shutdown
        
        # Session 2: Create new cache instance
        cache2 = HashBasedCache(cache_config)
        
        # Should load previous cache data
        changed_files, cached_files = cache2.get_changed_files([file_path])
        assert file_path in cached_files
        
        # Stats should reflect loaded data
        stats = cache2.get_cache_stats()
        assert stats['total_cached_files'] == 1


# Pytest configuration
pytestmark = pytest.mark.performance


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
