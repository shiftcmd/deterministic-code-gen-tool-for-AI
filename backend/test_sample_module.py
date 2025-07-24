"""
Test sample module for Phase 1 extraction testing.

This module contains various Python constructs to test the extraction
and transformation pipeline comprehensively.
"""

import os
import sys
import json
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from datetime import datetime
from collections import defaultdict


# Module-level variables
MODULE_VERSION = "1.0.0"
DEBUG_MODE = True
CONFIG_PATH = "/etc/config.json"


class BaseProcessor:
    """Base class for all data processors."""
    
    def __init__(self, name: str):
        """Initialize processor with name."""
        self.name = name
        self.created_at = datetime.now()
    
    def process(self, data: Any) -> Any:
        """Process data - to be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement process method")


class DataProcessor(BaseProcessor):
    """Concrete data processor implementation."""
    
    def __init__(self, name: str, config: Optional[Dict] = None):
        """Initialize data processor."""
        super().__init__(name)
        self.config = config or {}
        self._cache = defaultdict(list)
    
    @property
    def cache_size(self) -> int:
        """Get current cache size."""
        return sum(len(v) for v in self._cache.values())
    
    @staticmethod
    def validate_data(data: Any) -> bool:
        """Static method to validate input data."""
        return data is not None
    
    @classmethod
    def create_default(cls) -> "DataProcessor":
        """Class method to create default processor."""
        return cls("default", {"mode": "standard"})
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data and return results."""
        if not self.validate_data(data):
            raise ValueError("Invalid input data")
        
        # Nested function for processing
        def transform_item(key: str, value: Any) -> Any:
            """Transform individual data item."""
            if isinstance(value, str):
                return value.upper()
            elif isinstance(value, (int, float)):
                return value * 2
            else:
                return value
        
        # Process all items
        result = {}
        for key, value in data.items():
            processed_value = transform_item(key, value)
            result[key] = processed_value
            self._cache[key].append(processed_value)
        
        return result
    
    def clear_cache(self):
        """Clear the internal cache."""
        self._cache.clear()


class UtilityMixin:
    """Mixin class with utility methods."""
    
    def log_message(self, message: str) -> None:
        """Log a message."""
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] {message}")


def load_config(config_path: str = CONFIG_PATH) -> Dict[str, Any]:
    """Load configuration from file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"default": True}
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file: {e}")


async def async_fetch_data(url: str) -> Optional[Dict]:
    """Async function to fetch data from URL."""
    # Simulated async operation
    import asyncio
    await asyncio.sleep(0.1)
    return {"url": url, "status": "success"}


@property
def decorated_method(self) -> str:
    """Property decorator example."""
    return f"Property value for {self.name}"


def factory_function(processor_type: str = "default") -> BaseProcessor:
    """Factory function to create processors."""
    if processor_type == "data":
        return DataProcessor.create_default()
    else:
        return BaseProcessor("generic")


# Module-level function with complex signature
def complex_function(
    required_param: str,
    optional_param: Optional[int] = None,
    *args,
    keyword_only: bool = False,
    **kwargs
) -> Union[str, int]:
    """Function with complex parameter signature."""
    if keyword_only:
        return len(required_param) + (optional_param or 0)
    else:
        return f"{required_param}_{optional_param}"


# Exception class
class ProcessingError(Exception):
    """Custom exception for processing errors."""
    
    def __init__(self, message: str, error_code: int = 500):
        """Initialize processing error."""
        super().__init__(message)
        self.error_code = error_code
        self.timestamp = datetime.now()


if __name__ == "__main__":
    # Module execution code
    config = load_config()
    processor = DataProcessor("test_processor", config)
    
    test_data = {
        "string_value": "hello",
        "number_value": 42,
        "boolean_value": True
    }
    
    try:
        result = processor.process(test_data)
        print(f"Processing result: {result}")
    except ProcessingError as e:
        print(f"Processing failed: {e} (code: {e.error_code})")