"""
Basic functionality tests for performance optimization system.

Simple smoke tests to verify the core system works before running comprehensive tests.
"""

import pytest
import tempfile
from pathlib import Path

from backend.parser.config import get_parser_config
from backend.parser.codebase_parser import CodebaseParser


class TestBasicFunctionality:
    """Basic functionality tests."""
    
    @pytest.fixture
    def simple_test_file(self):
        """Create a simple test Python file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
# Simple test file
def hello_world():
    \"\"\"Simple function.\"\"\"
    return "Hello, World!"

class SimpleClass:
    \"\"\"Simple class.\"\"\"
    
    def __init__(self, name):
        self.name = name
    
    def greet(self):
        return f"Hello, {self.name}!"
""")
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        Path(temp_file).unlink()
    
    def test_basic_parsing_works(self, simple_test_file):
        """Test that basic parsing functionality works."""
        config = get_parser_config("minimal")
        config.parallel_processing = False  # Keep it simple
        config.cache_results = False
        
        parser = CodebaseParser(config)
        
        # Parse single file
        result = parser.parse_file(simple_test_file)
        
        # Should return ParsedModule
        assert result is not None
        assert result.name is not None
        assert result.path == simple_test_file
        
        # Should have parsed some content
        assert len(result.functions) > 0 or len(result.classes) > 0
    
    def test_parallel_processor_creation(self):
        """Test that parallel processor can be created."""
        config = get_parser_config("standard")
        config.tool_options['parallel']['max_workers'] = 1
        
        parser = CodebaseParser(config)
        assert parser.parallel_processor is not None
        
        # Get metrics should work
        metrics = parser.parallel_processor.get_metrics()
        assert metrics is not None
    
    def test_cache_creation(self):
        """Test that cache can be created."""
        config = get_parser_config("standard")
        config.cache_results = True
        
        parser = CodebaseParser(config)
        
        # Cache should be initialized
        cache_stats = parser.get_cache_stats()
        assert isinstance(cache_stats, dict)
        assert 'total_cached_files' in cache_stats
    
    def test_configuration_presets(self):
        """Test that all configuration presets work."""
        presets = ['minimal', 'standard', 'performance', 'comprehensive']
        
        for preset_name in presets:
            config = get_parser_config(preset_name)
            assert config is not None
            
            # Should be able to create parser with each preset
            parser = CodebaseParser(config)
            assert parser is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
