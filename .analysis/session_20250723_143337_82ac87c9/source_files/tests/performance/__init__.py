"""
Performance optimization test suite.

This package contains comprehensive tests for all performance optimization
features including parallel processing, memory-efficient parsing, hash-based
caching, and incremental parsing.

Test Structure:
- test_parallel_processor.py: Unit tests for parallel processing system
- test_hash_based_cache.py: Unit tests for hash-based caching system
- test_integration.py: Integration tests for complete system workflows

To run all performance tests:
    pytest tests/performance/ -v

To run specific test categories:
    pytest tests/performance/ -v -k "cache"
    pytest tests/performance/ -v -k "parallel"
    pytest tests/performance/ -v -k "integration"

To run with coverage:
    pytest tests/performance/ --cov=backend.parser --cov-report=html

Performance test markers:
- @pytest.mark.performance: All performance-related tests
- @pytest.mark.integration: Integration tests requiring full system
- @pytest.mark.slow: Tests that may take longer to complete
"""

# Test configuration constants
TEST_TIMEOUT = 30  # seconds
TEST_MAX_WORKERS = 2  # Keep low for test stability
TEST_MEMORY_LIMIT = 512  # MB
TEST_CACHE_SIZE = 100  # MB
