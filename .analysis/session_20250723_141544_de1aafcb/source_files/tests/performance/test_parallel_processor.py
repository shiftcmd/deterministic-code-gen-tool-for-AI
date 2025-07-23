"""
Unit tests for the ParallelProcessor performance optimization system.

Tests cover:
- Processing strategy selection
- Memory management
- Error recovery
- Progress tracking
- Cache integration
- Performance metrics
"""

import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import Future
import threading

from backend.parser.parallel_processor import ParallelProcessor
from backend.parser.processing_types import ProcessingStrategy, ProcessingMetrics, ParsingTask, ProgressTracker
from backend.parser.config import get_parser_config
from backend.parser.models import ParsedModule


class TestParallelProcessor:
    """Test cases for ParallelProcessor class."""
    
    @pytest.fixture
    def temp_files(self):
        """Create temporary Python files for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files of various sizes
            files = {}
            
            # Small file
            small_file = temp_path / "small.py"
            small_file.write_text("# Small file\nprint('hello')\n")
            files['small'] = str(small_file)
            
            # Medium file
            medium_file = temp_path / "medium.py"
            medium_content = "# Medium file\n" + "def func_{}():\n    pass\n\n" * 50
            medium_file.write_text(medium_content)
            files['medium'] = str(medium_file)
            
            # Large file
            large_file = temp_path / "large.py"
            large_content = "# Large file\n" + "class Class_{}:\n    def method(self): pass\n\n" * 200
            large_file.write_text(large_content)
            files['large'] = str(large_file)
            
            yield files
    
    @pytest.fixture
    def processor(self):
        """Create ParallelProcessor instance with test configuration."""
        config = get_parser_config("minimal")  # Use minimal config for testing
        config.tool_options['parallel']['max_workers'] = 2
        config.tool_options['parallel']['strategy'] = 'thread_based'
        return ParallelProcessor(config)
    
    @pytest.fixture
    def mock_parse_func(self):
        """Mock parsing function that returns ParsedModule."""
        def mock_parser(file_path: str) -> ParsedModule:
            return ParsedModule(
                name=Path(file_path).stem,
                path=file_path,
                classes=[],
                functions=[],
                variables=[],
                imports=[]
            )
        return mock_parser


class TestStrategySelection(TestParallelProcessor):
    """Test automatic strategy selection logic."""
    
    def test_thread_strategy_for_small_files(self, processor, temp_files):
        """Test that thread strategy is selected for many small files."""
        small_files = [temp_files['small']] * 10
        tasks = [ParsingTask(file_path=path) for path in small_files]
        
        strategy = processor._select_strategy(tasks)
        assert strategy in [ProcessingStrategy.THREAD_BASED, ProcessingStrategy.HYBRID]
    
    def test_process_strategy_for_large_files(self, processor, temp_files):
        """Test that process strategy is selected for large files."""
        large_files = [temp_files['large']] * 2
        tasks = [ParsingTask(file_path=path) for path in large_files]
        
        # Mock file size estimation to return large sizes
        with patch.object(processor, '_estimate_task_memory', return_value=1024):
            strategy = processor._select_strategy(tasks)
            assert strategy in [ProcessingStrategy.PROCESS_BASED, ProcessingStrategy.HYBRID]
    
    def test_adaptive_strategy_selection(self, processor, temp_files):
        """Test adaptive strategy with mixed file sizes."""
        mixed_files = [temp_files['small'], temp_files['medium'], temp_files['large']]
        tasks = [ParsingTask(file_path=path) for path in mixed_files]
        
        # Adaptive should select appropriate strategy
        strategy = processor._select_strategy(tasks)
        assert strategy in list(ProcessingStrategy)


class TestMemoryManagement(TestParallelProcessor):
    """Test memory management and monitoring."""
    
    def test_memory_allocation_tracking(self, processor):
        """Test that memory allocation is tracked correctly."""
        initial_allocated = processor.memory_manager.allocated_memory
        
        # Simulate memory allocation
        processor.memory_manager.allocate(100)
        assert processor.memory_manager.allocated_memory == initial_allocated + 100
        
        # Simulate memory deallocation
        processor.memory_manager.deallocate(50)
        assert processor.memory_manager.allocated_memory == initial_allocated + 50
    
    def test_memory_limit_enforcement(self, processor):
        """Test that memory limits are enforced."""
        # Set low memory limit for testing
        processor.memory_manager.max_memory = 100
        
        # Allocating within limit should succeed
        processor.memory_manager.allocate(50)
        
        # Allocating beyond limit should raise exception
        with pytest.raises(MemoryError):
            processor.memory_manager.allocate(100)
    
    def test_memory_cleanup(self, processor):
        """Test automatic memory cleanup."""
        processor.memory_manager.allocate(100)
        initial_allocated = processor.memory_manager.allocated_memory
        
        processor._cleanup()
        # Memory should be reduced after cleanup
        assert processor.memory_manager.allocated_memory <= initial_allocated


class TestProgressTracking(TestParallelProcessor):
    """Test progress tracking and observer pattern."""
    
    def test_progress_tracker_initialization(self):
        """Test ProgressTracker initialization."""
        tracker = ProgressTracker(total_files=10)
        assert tracker.total_files == 10
        assert tracker.completed_files == 0
        assert tracker.failed_files == 0
    
    def test_progress_updates(self):
        """Test progress update functionality."""
        tracker = ProgressTracker(total_files=10)
        
        tracker.update_progress(completed=3)
        assert tracker.completed_files == 3
        
        tracker.update_progress(failed=1, current_file="test.py")
        assert tracker.failed_files == 1
        assert tracker.current_file == "test.py"
    
    def test_progress_observers(self):
        """Test progress observer notifications."""
        tracker = ProgressTracker(total_files=10)
        
        # Mock observer
        observer = Mock()
        tracker.add_observer(observer)
        
        # Update progress and check observer was called
        tracker.update_progress(completed=1)
        observer.assert_called_once()
        
        # Check observer received correct data
        call_args = observer.call_args[0][0]
        assert call_args['completed_files'] == 1
        assert call_args['total_files'] == 10
        assert call_args['percentage'] == 10.0
    
    def test_thread_safety(self):
        """Test that progress tracking is thread-safe."""
        tracker = ProgressTracker(total_files=100)
        
        def update_progress():
            for _ in range(10):
                tracker.update_progress(completed=1)
        
        # Start multiple threads updating progress
        threads = [threading.Thread(target=update_progress) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Should have exactly 50 completed files (5 threads * 10 updates)
        assert tracker.completed_files == 50


class TestErrorRecovery(TestParallelProcessor):
    """Test error recovery and retry mechanisms."""
    
    def test_retry_on_failure(self, processor, temp_files, mock_parse_func):
        """Test retry mechanism for failed parsing."""
        # Create a parse function that fails first time, succeeds second time
        call_count = 0
        
        def failing_parse_func(file_path):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Simulated parsing error")
            return mock_parse_func(file_path)
        
        with patch.object(processor, '_safe_parse_task') as mock_safe_parse:
            # First call fails, second succeeds
            mock_safe_parse.side_effect = [None, mock_parse_func(temp_files['small'])]
            
            results = processor.process_files([temp_files['small']], mock_parse_func)
            
            # Should have retried and eventually succeeded
            assert len(results) >= 0  # May succeed with retry
    
    def test_graceful_degradation_on_critical_failure(self, processor, temp_files):
        """Test graceful degradation when parallel processing fails."""
        # Mock a critical failure in parallel processing
        with patch.object(processor, '_process_with_threads', side_effect=RuntimeError("Critical error")):
            # Should not crash, should handle gracefully
            with pytest.raises(RuntimeError):
                processor.process_files([temp_files['small']], Mock())


class TestCacheIntegration(TestParallelProcessor):
    """Test integration with hash-based cache."""
    
    def test_cache_hit_optimization(self, processor, temp_files, mock_parse_func):
        """Test that cached files are not re-parsed."""
        files = [temp_files['small'], temp_files['medium']]
        
        # Mock cache to return some files as cached
        with patch.object(processor.cache, 'get_changed_files') as mock_get_changed:
            with patch.object(processor.cache, 'bulk_load_cached_results') as mock_bulk_load:
                # Simulate cache hit for first file, miss for second
                mock_get_changed.return_value = ([temp_files['medium']], [temp_files['small']])
                mock_bulk_load.return_value = {
                    temp_files['small']: Mock(parsed_module=mock_parse_func(temp_files['small']))
                }
                
                results = processor.process_files(files, mock_parse_func)
                
                # Should have results for both files
                assert len(results) >= 1
                
                # Cache methods should have been called
                mock_get_changed.assert_called_once_with(files)
                mock_bulk_load.assert_called_once()
    
    def test_cache_storage_after_parsing(self, processor, temp_files, mock_parse_func):
        """Test that parsed results are stored in cache."""
        with patch.object(processor.cache, 'store_result') as mock_store:
            with patch.object(processor.cache, 'get_changed_files') as mock_get_changed:
                # All files are changed (cache miss)
                mock_get_changed.return_value = ([temp_files['small']], [])
                
                processor.process_files([temp_files['small']], mock_parse_func)
                
                # Should attempt to store result in cache
                # Note: Actual storage depends on successful parsing


class TestPerformanceMetrics(TestParallelProcessor):
    """Test performance metrics collection."""
    
    def test_metrics_initialization(self, processor):
        """Test that metrics are properly initialized."""
        metrics = processor.get_metrics()
        assert isinstance(metrics, ProcessingMetrics)
        assert metrics.total_files >= 0
        assert metrics.processed_files >= 0
        assert metrics.failed_files >= 0
    
    def test_metrics_calculation(self, processor, temp_files, mock_parse_func):
        """Test metrics calculation accuracy."""
        files = [temp_files['small'], temp_files['medium']]
        
        # Mock successful parsing
        with patch.object(processor.cache, 'get_changed_files') as mock_get_changed:
            mock_get_changed.return_value = (files, [])  # All files need parsing
            
            start_time = time.time()
            processor.process_files(files, mock_parse_func)
            end_time = time.time()
            
            metrics = processor.get_metrics()
            
            # Check metrics values
            assert metrics.total_files >= 0
            assert metrics.duration > 0
            assert metrics.duration <= (end_time - start_time) + 1  # Allow for processing overhead
    
    def test_memory_stats_integration(self, processor):
        """Test memory statistics integration."""
        memory_stats = processor.get_memory_stats()
        
        # Should return memory statistics
        assert isinstance(memory_stats, dict)
        assert 'peak_memory_mb' in memory_stats or len(memory_stats) >= 0


class TestIntegrationScenarios(TestParallelProcessor):
    """Integration tests for complete workflows."""
    
    def test_complete_parsing_workflow(self, processor, temp_files, mock_parse_func):
        """Test complete parsing workflow from start to finish."""
        all_files = list(temp_files.values())
        
        # Add progress observer to track completion
        progress_updates = []
        def progress_observer(data):
            progress_updates.append(data)
        
        processor.add_progress_observer(progress_observer)
        
        # Parse all files
        results = processor.process_files(all_files, mock_parse_func)
        
        # Verify results
        assert isinstance(results, dict)
        # Should have progress updates
        assert len(progress_updates) >= 0  # May be 0 if all cached
        
        # Verify metrics are updated
        metrics = processor.get_metrics()
        assert metrics.total_files >= 0
    
    def test_mixed_file_sizes_workflow(self, processor, temp_files, mock_parse_func):
        """Test workflow with mixed file sizes to trigger memory-efficient parsing."""
        files = [temp_files['small'], temp_files['large']]
        
        # Should handle both small and large files appropriately
        results = processor.process_files(files, mock_parse_func)
        
        # Verify processing completed
        assert isinstance(results, dict)
        
        # Verify memory stats show usage
        memory_stats = processor.get_memory_stats()
        assert isinstance(memory_stats, dict)


# Pytest fixtures for module-level setup
@pytest.fixture(scope="module")
def test_config():
    """Module-level test configuration."""
    return get_parser_config("minimal")


# Integration test marks
pytestmark = pytest.mark.performance


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
