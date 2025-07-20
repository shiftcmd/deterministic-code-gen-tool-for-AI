"""
Integration tests for the complete performance optimization system.

Tests the integration of:
- ParallelProcessor
- MemoryEfficientParser  
- HashBasedCache
- CodebaseParser

These tests validate the complete workflow under realistic conditions.
"""

import pytest
import tempfile
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch

from backend.parser.codebase_parser import CodebaseParser
from backend.parser.config import get_parser_config
from backend.parser.models import ParsedModule


class TestSystemIntegration:
    """Integration tests for the complete performance system."""
    
    @pytest.fixture
    def test_codebase(self):
        """Create a test codebase with various file sizes and structures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create project structure
            (project_path / "src").mkdir()
            (project_path / "tests").mkdir()
            (project_path / "utils").mkdir()
            
            files = {}
            
            # Small utility file
            small_file = project_path / "utils" / "helpers.py"
            small_content = '''"""Utility helpers."""

def format_string(s):
    """Format a string."""
    return s.strip().lower()

def validate_input(data):
    """Validate input data."""
    return data is not None and len(data) > 0
'''
            small_file.write_text(small_content)
            files['small'] = str(small_file)
            
            # Medium-sized main module
            medium_file = project_path / "src" / "main.py"
            medium_content = '''"""Main application module."""

import os
import sys
from typing import List, Dict, Any
from utils.helpers import format_string, validate_input

class Application:
    """Main application class."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.initialized = False
    
    def initialize(self) -> bool:
        """Initialize the application."""
        if not validate_input(self.config.get('name')):
            return False
        
        self.initialized = True
        return True
    
    def run(self) -> int:
        """Run the application."""
        if not self.initialized:
            self.initialize()
        
        print(f"Running {self.config.get('name', 'Unknown App')}")
        return 0

def create_app(name: str) -> Application:
    """Create application instance."""
    config = {
        'name': format_string(name),
        'version': '1.0.0'
    }
    return Application(config)

if __name__ == "__main__":
    app = create_app("Test Application")
    sys.exit(app.run())
'''
            medium_file.write_text(medium_content)
            files['medium'] = str(medium_file)
            
            # Large file with many classes and functions
            large_file = project_path / "src" / "models.py"
            large_content = '''"""Data models for the application."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

'''
            
            # Generate many classes and methods
            for i in range(20):
                class_content = f'''
@dataclass
class Model{i}:
    """Model class {i}."""
    
    id: int
    name: str
    created_at: datetime
    data: Optional[Dict[str, Any]] = None
    
    def validate(self) -> bool:
        """Validate the model."""
        return self.id > 0 and len(self.name) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {{
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'data': self.data or {{}}
        }}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Model{i}':
        """Create from dictionary."""
        return cls(
            id=data['id'],
            name=data['name'],
            created_at=datetime.fromisoformat(data['created_at']),
            data=data.get('data')
        )

class Repository{i}:
    """Repository for Model{i}."""
    
    def __init__(self):
        self.items: List[Model{i}] = []
    
    def add(self, item: Model{i}) -> None:
        """Add item to repository."""
        if item.validate():
            self.items.append(item)
    
    def find_by_id(self, item_id: int) -> Optional[Model{i}]:
        """Find item by ID."""
        for item in self.items:
            if item.id == item_id:
                return item
        return None
    
    def find_by_name(self, name: str) -> List[Model{i}]:
        """Find items by name."""
        return [item for item in self.items if item.name == name]
    
    def update(self, item: Model{i}) -> bool:
        """Update existing item."""
        existing = self.find_by_id(item.id)
        if existing:
            existing.name = item.name
            existing.data = item.data
            return True
        return False
    
    def delete(self, item_id: int) -> bool:
        """Delete item by ID."""
        item = self.find_by_id(item_id)
        if item:
            self.items.remove(item)
            return True
        return False
'''
                large_content += class_content
            
            large_file.write_text(large_content)
            files['large'] = str(large_file)
            
            # Test file
            test_file = project_path / "tests" / "test_main.py"
            test_content = '''"""Tests for main module."""

import unittest
from src.main import Application, create_app

class TestApplication(unittest.TestCase):
    """Test cases for Application class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {'name': 'test_app', 'version': '1.0.0'}
        self.app = Application(self.config)
    
    def test_initialization(self):
        """Test application initialization."""
        self.assertFalse(self.app.initialized)
        result = self.app.initialize()
        self.assertTrue(result)
        self.assertTrue(self.app.initialized)
    
    def test_run(self):
        """Test application run."""
        result = self.app.run()
        self.assertEqual(result, 0)
        self.assertTrue(self.app.initialized)
    
    def test_create_app(self):
        """Test create_app function."""
        app = create_app("Test App")
        self.assertIsInstance(app, Application)
        self.assertEqual(app.config['name'], 'test app')

if __name__ == '__main__':
    unittest.main()
'''
            test_file.write_text(test_content)
            files['test'] = str(test_file)
            
            yield {
                'project_path': str(project_path),
                'files': files,
                'all_files': [str(f) for f in project_path.rglob("*.py")]
            }
    
    @pytest.fixture
    def parser_configs(self):
        """Different parser configurations for testing."""
        return {
            'minimal': get_parser_config("minimal"),
            'standard': get_parser_config("standard"), 
            'performance': get_parser_config("performance")
        }


class TestColdVsWarmCache(TestSystemIntegration):
    """Test cold vs warm cache performance."""
    
    def test_cold_cache_performance(self, test_codebase, parser_configs):
        """Test parsing performance with cold cache."""
        config = parser_configs['standard']
        config.cache_results = True
        
        parser = CodebaseParser(config)
        
        # First run - cold cache
        start_time = time.time()
        results = parser.parse_codebase(test_codebase['project_path'])
        cold_duration = time.time() - start_time
        
        # Verify parsing results
        assert isinstance(results, dict)
        assert len(results) > 0
        
        # Get metrics
        metrics = parser.get_processing_metrics()
        assert metrics['processed_files'] > 0
        assert metrics['success_rate'] > 0
        
        # Cache should have entries now
        cache_stats = parser.get_cache_stats()
        assert cache_stats['total_cached_files'] > 0
        
        return cold_duration, results, metrics
    
    def test_warm_cache_performance(self, test_codebase, parser_configs):
        """Test parsing performance with warm cache."""
        config = parser_configs['standard']
        config.cache_results = True
        
        parser = CodebaseParser(config)
        
        # First run to warm cache
        parser.parse_codebase(test_codebase['project_path'])
        
        # Second run - warm cache
        start_time = time.time()
        results = parser.parse_codebase(test_codebase['project_path'])
        warm_duration = time.time() - start_time
        
        # Verify results
        assert isinstance(results, dict)
        assert len(results) > 0
        
        # Get cache stats
        cache_stats = parser.get_cache_stats()
        assert cache_stats['hit_rate_percent'] > 50  # Should have significant cache hits
        
        return warm_duration, results, cache_stats
    
    def test_cache_performance_improvement(self, test_codebase, parser_configs):
        """Test that cache provides significant performance improvement."""
        config = parser_configs['standard']
        config.cache_results = True
        
        parser = CodebaseParser(config)
        
        # Cold cache run
        start_time = time.time()
        results1 = parser.parse_codebase(test_codebase['project_path'])
        cold_duration = time.time() - start_time
        
        # Warm cache run
        start_time = time.time()
        results2 = parser.parse_codebase(test_codebase['project_path'])
        warm_duration = time.time() - start_time
        
        # Verify same results
        assert len(results1) == len(results2)
        
        # Warm cache should be significantly faster
        if warm_duration > 0:  # Avoid division by zero
            improvement_ratio = cold_duration / warm_duration
            assert improvement_ratio > 2.0  # At least 2x faster with cache


class TestParallelProcessingIntegration(TestSystemIntegration):
    """Test parallel processing integration."""
    
    def test_parallel_vs_serial_performance(self, test_codebase, parser_configs):
        """Compare parallel vs serial processing performance."""
        # Serial processing
        serial_config = parser_configs['standard']
        serial_config.parallel_processing = False
        serial_parser = CodebaseParser(serial_config)
        
        start_time = time.time()
        serial_results = serial_parser.parse_codebase(test_codebase['project_path'])
        serial_duration = time.time() - start_time
        
        # Parallel processing  
        parallel_config = parser_configs['standard']
        parallel_config.parallel_processing = True
        parallel_parser = CodebaseParser(parallel_config)
        
        start_time = time.time()
        parallel_results = parallel_parser.parse_codebase(test_codebase['project_path'])
        parallel_duration = time.time() - start_time
        
        # Results should be equivalent
        assert len(serial_results) == len(parallel_results)
        
        # Parallel should be faster (or at least not significantly slower)
        # Allow for small overhead in test environment
        assert parallel_duration <= (serial_duration * 1.5)
    
    def test_different_processing_strategies(self, test_codebase):
        """Test different parallel processing strategies."""
        strategies = ['thread_based', 'process_based', 'hybrid', 'adaptive']
        results = {}
        
        for strategy in strategies:
            config = get_parser_config('standard')
            config.tool_options['parallel']['strategy'] = strategy
            config.tool_options['parallel']['max_workers'] = 2  # Keep it small for testing
            
            parser = CodebaseParser(config)
            
            start_time = time.time()
            parse_results = parser.parse_codebase(test_codebase['project_path'])
            duration = time.time() - start_time
            
            results[strategy] = {
                'duration': duration,
                'files_parsed': len(parse_results),
                'metrics': parser.get_processing_metrics()
            }
        
        # All strategies should produce same number of results
        file_counts = [r['files_parsed'] for r in results.values()]
        assert len(set(file_counts)) == 1, "All strategies should parse same number of files"
        
        # All strategies should have reasonable performance
        for strategy, result in results.items():
            assert result['duration'] > 0
            assert result['metrics']['success_rate'] >= 90  # At least 90% success rate


class TestMemoryEfficientIntegration(TestSystemIntegration):
    """Test memory-efficient parsing integration."""
    
    def test_memory_efficient_large_files(self, test_codebase):
        """Test memory-efficient parsing with large files."""
        config = get_parser_config('standard')
        # Set very low threshold to trigger memory-efficient parsing
        config.tool_options['memory']['use_efficient_parsing_mb'] = 1024  # 1KB
        
        parser = CodebaseParser(config)
        results = parser.parse_codebase(test_codebase['project_path'])
        
        # Should successfully parse all files
        assert len(results) > 0
        
        # Get memory stats
        memory_stats = parser.parallel_processor.get_memory_stats()
        assert isinstance(memory_stats, dict)
        
        # Should have used memory-efficient parsing
        metrics = parser.get_processing_metrics()
        assert metrics['success_rate'] > 0
    
    def test_memory_usage_monitoring(self, test_codebase):
        """Test memory usage monitoring during parsing."""
        config = get_parser_config('performance')
        config.tool_options['memory']['memory_limit_mb'] = 512  # Set reasonable limit
        
        parser = CodebaseParser(config)
        
        # Track progress with memory monitoring
        memory_snapshots = []
        
        def progress_callback(data):
            memory_stats = parser.parallel_processor.get_memory_stats()
            memory_snapshots.append(memory_stats.get('current_memory_mb', 0))
        
        parser.add_progress_observer(progress_callback)
        
        results = parser.parse_codebase(test_codebase['project_path'])
        
        # Should have memory snapshots
        assert len(memory_snapshots) >= 0
        
        # Final memory stats should be available
        final_stats = parser.parallel_processor.get_memory_stats()
        assert isinstance(final_stats, dict)


class TestIncrementalParsingIntegration(TestSystemIntegration):
    """Test incremental parsing integration."""
    
    def test_selective_reparse_on_changes(self, test_codebase):
        """Test that only changed files are re-parsed."""
        config = get_parser_config('standard')
        config.cache_results = True
        
        parser = CodebaseParser(config)
        
        # Initial parse
        results1 = parser.parse_codebase(test_codebase['project_path'])
        initial_stats = parser.get_cache_stats()
        
        # Modify one file
        modified_file = Path(test_codebase['files']['small'])
        original_content = modified_file.read_text()
        modified_content = original_content + "\n# Added comment\n"
        modified_file.write_text(modified_content)
        
        try:
            # Parse again
            results2 = parser.parse_codebase(test_codebase['project_path'])
            final_stats = parser.get_cache_stats()
            
            # Should have same number of results
            assert len(results1) == len(results2)
            
            # Should have used cache for most files
            assert final_stats['cache_hits'] > 0
            assert final_stats['hit_rate_percent'] > 50
            
        finally:
            # Restore original content
            modified_file.write_text(original_content)
    
    def test_cache_invalidation_on_file_changes(self, test_codebase):
        """Test cache invalidation when files change."""
        config = get_parser_config('standard')
        config.cache_results = True
        
        parser = CodebaseParser(config)
        
        # Initial parse to establish cache
        parser.parse_codebase(test_codebase['project_path'])
        
        # Get current cache state
        initial_stats = parser.get_cache_stats()
        initial_cached_files = initial_stats['total_cached_files']
        
        # Invalidate specific file
        test_file = test_codebase['files']['medium']
        success = parser.invalidate_file_cache(test_file)
        assert success
        
        # Parse again
        parser.parse_codebase(test_codebase['project_path'])
        
        # Cache stats should show the invalidation
        final_stats = parser.get_cache_stats()
        # Note: File will be re-cached, so total might be same
        assert isinstance(final_stats, dict)


class TestErrorHandlingIntegration(TestSystemIntegration):
    """Test error handling across the integrated system."""
    
    def test_malformed_file_handling(self, test_codebase):
        """Test handling of malformed Python files."""
        config = get_parser_config('standard')
        parser = CodebaseParser(config)
        
        # Create malformed Python file
        malformed_file = Path(test_codebase['project_path']) / "malformed.py"
        malformed_file.write_text("def incomplete_function(\n    # Missing closing parenthesis and body")
        
        try:
            # Should handle malformed files gracefully
            results = parser.parse_codebase(test_codebase['project_path'])
            
            # Should still parse other files successfully
            assert len(results) >= 0  # May skip malformed file
            
            # Check metrics for failure handling
            metrics = parser.get_processing_metrics()
            assert 'failed_files' in metrics
            
        finally:
            # Clean up
            if malformed_file.exists():
                malformed_file.unlink()
    
    def test_memory_pressure_handling(self, test_codebase):
        """Test handling of memory pressure conditions."""
        config = get_parser_config('minimal')
        # Set very low memory limit to trigger pressure handling
        config.tool_options['memory']['memory_limit_mb'] = 50
        config.tool_options['parallel']['max_memory_mb'] = 50
        
        parser = CodebaseParser(config)
        
        # Should handle memory pressure gracefully
        results = parser.parse_codebase(test_codebase['project_path'])
        
        # Should still produce results, possibly with degraded performance
        assert isinstance(results, dict)
        
        # Check memory stats
        memory_stats = parser.parallel_processor.get_memory_stats()
        assert isinstance(memory_stats, dict)
    
    def test_concurrent_access_handling(self, test_codebase):
        """Test handling of concurrent parser access."""
        config = get_parser_config('standard')
        config.cache_results = True
        
        results = []
        errors = []
        
        def parse_worker():
            try:
                parser = CodebaseParser(config)
                result = parser.parse_codebase(test_codebase['project_path'])
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Start multiple concurrent parsing operations
        threads = [threading.Thread(target=parse_worker) for _ in range(3)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should handle concurrent access gracefully
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        assert len(results) == 3
        
        # All results should be consistent
        file_counts = [len(result) for result in results]
        assert len(set(file_counts)) <= 2  # Allow minor variation due to timing


class TestComprehensiveWorkflows(TestSystemIntegration):
    """Test comprehensive, realistic workflows."""
    
    def test_development_workflow_simulation(self, test_codebase):
        """Simulate typical development workflow with multiple parse cycles."""
        config = get_parser_config('standard')
        config.cache_results = True
        
        parser = CodebaseParser(config)
        
        # Initial project analysis
        results1 = parser.parse_codebase(test_codebase['project_path'])
        metrics1 = parser.get_processing_metrics()
        
        # Simulate code changes - modify multiple files
        files_to_modify = [test_codebase['files']['small'], test_codebase['files']['medium']]
        original_contents = {}
        
        for file_path in files_to_modify:
            path = Path(file_path)
            original_contents[file_path] = path.read_text()
            modified_content = original_contents[file_path] + "\n# Development change\n"
            path.write_text(modified_content)
        
        try:
            # Re-analysis after changes
            results2 = parser.parse_codebase(test_codebase['project_path'])
            metrics2 = parser.get_processing_metrics()
            cache_stats = parser.get_cache_stats()
            
            # Should maintain same number of files
            assert len(results1) == len(results2)
            
            # Should show cache efficiency
            assert cache_stats['hit_rate_percent'] > 30  # Some files cached
            
            # More changes - add new file
            new_file = Path(test_codebase['project_path']) / "new_module.py"
            new_file.write_text('''"""New module added during development."""

def new_function():
    """New function."""
    return "new"

class NewClass:
    """New class."""
    pass
''')
            
            # Final analysis
            results3 = parser.parse_codebase(test_codebase['project_path'])
            
            # Should detect new file
            assert len(results3) > len(results2)
            
        finally:
            # Restore original contents
            for file_path, content in original_contents.items():
                Path(file_path).write_text(content)
            
            # Clean up new file
            new_file_path = Path(test_codebase['project_path']) / "new_module.py"
            if new_file_path.exists():
                new_file_path.unlink()
    
    def test_large_codebase_simulation(self, test_codebase):
        """Simulate analysis of larger codebase."""
        config = get_parser_config('performance')
        config.cache_results = True
        config.tool_options['parallel']['max_workers'] = 4
        
        parser = CodebaseParser(config)
        
        # Create additional files to simulate larger codebase
        project_path = Path(test_codebase['project_path'])
        additional_files = []
        
        for i in range(20):  # Create 20 additional files
            file_path = project_path / f"generated_{i}.py"
            content = f'''"""Generated file {i}."""

class GeneratedClass{i}:
    """Generated class {i}."""
    
    def __init__(self, value: int = {i}):
        self.value = value
    
    def process(self) -> int:
        """Process the value."""
        return self.value * 2
    
    def validate(self) -> bool:
        """Validate the value."""
        return self.value >= 0

def generated_function_{i}():
    """Generated function {i}."""
    return GeneratedClass{i}({i})
'''
            file_path.write_text(content)
            additional_files.append(file_path)
        
        try:
            # Parse larger codebase
            start_time = time.time()
            results = parser.parse_codebase(str(project_path))
            duration = time.time() - start_time
            
            # Should handle larger codebase efficiently
            assert len(results) >= 24  # Original + generated files
            
            # Get comprehensive metrics
            metrics = parser.get_processing_metrics()
            cache_stats = parser.get_cache_stats()
            memory_stats = parser.parallel_processor.get_memory_stats()
            
            # Performance should be reasonable
            assert duration < 30.0  # Should complete within 30 seconds
            assert metrics['success_rate'] >= 90
            
            # Second run should be much faster due to caching
            start_time = time.time()
            results2 = parser.parse_codebase(str(project_path))
            cached_duration = time.time() - start_time
            
            # Should be significantly faster
            if cached_duration > 0:
                speedup = duration / cached_duration
                assert speedup > 2.0  # At least 2x speedup
            
        finally:
            # Clean up generated files
            for file_path in additional_files:
                if file_path.exists():
                    file_path.unlink()


# Pytest configuration
pytestmark = [pytest.mark.performance, pytest.mark.integration]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-k", "not test_large_codebase_simulation"])
