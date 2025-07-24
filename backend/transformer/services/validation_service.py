"""
Validation service for transformation data.

Provides validation capabilities for input extraction data
and output transformation results.
"""

import logging
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)


class ValidationService:
    """Service for validating transformation data."""
    
    def __init__(self):
        """Initialize validation service."""
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_extraction_data(self, extraction_data: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """
        Validate Phase 1 extraction data format.
        
        Args:
            extraction_data: Raw extraction data from Phase 1
            
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors.clear()
        self.warnings.clear()
        
        # Check top-level structure
        if not isinstance(extraction_data, dict):
            self.errors.append("Extraction data must be a dictionary")
            return False, self.errors, self.warnings
        
        # Check required top-level fields
        if "modules" not in extraction_data:
            self.errors.append("Missing required field 'modules'")
        
        # Validate modules section
        modules = extraction_data.get("modules", {})
        if not isinstance(modules, dict):
            self.errors.append("'modules' field must be a dictionary")
        else:
            for module_path, module_data in modules.items():
                self._validate_module_data(module_path, module_data)
        
        # Check optional metadata
        if "metadata" in extraction_data:
            self._validate_metadata(extraction_data["metadata"])
        
        return len(self.errors) == 0, self.errors.copy(), self.warnings.copy()
    
    def _validate_module_data(self, module_path: str, module_data: Dict[str, Any]) -> None:
        """Validate individual module data."""
        if not isinstance(module_data, dict):
            self.errors.append(f"Module data for {module_path} must be a dictionary")
            return
        
        # Check required module fields
        required_fields = ["name", "path"]
        for field in required_fields:
            if field not in module_data:
                self.errors.append(f"Module {module_path} missing required field '{field}'")
        
        # Validate collections
        collections_to_check = {
            "imports": list,
            "classes": list,
            "functions": list,
            "variables": list
        }
        
        for field_name, expected_type in collections_to_check.items():
            if field_name in module_data:
                field_value = module_data[field_name]
                if not isinstance(field_value, expected_type):
                    self.errors.append(
                        f"Module {module_path} field '{field_name}' must be a {expected_type.__name__}"
                    )
    
    def _validate_metadata(self, metadata: Dict[str, Any]) -> None:
        """Validate extraction metadata."""
        if not isinstance(metadata, dict):
            self.warnings.append("Metadata should be a dictionary")
            return
        
        # Check for recommended metadata fields
        recommended_fields = ["extraction_id", "timestamp", "version"]
        for field in recommended_fields:
            if field not in metadata:
                self.warnings.append(f"Recommended metadata field '{field}' is missing")
    
    def clear(self) -> None:
        """Clear all validation results."""
        self.errors.clear()
        self.warnings.clear()