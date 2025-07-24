"""
Validation Service for Neo4j Uploader

Validates Cypher files and commands before upload to ensure data integrity.
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..models.upload_result import ValidationResult

logger = logging.getLogger(__name__)


class ValidationService:
    """Service for validating Cypher files and commands."""
    
    def __init__(self):
        # Common Cypher patterns for estimation
        self.node_creation_patterns = [
            re.compile(r'CREATE\s*\([^)]*\)', re.IGNORECASE),
            re.compile(r'MERGE\s*\([^)]*\)', re.IGNORECASE)
        ]
        
        self.relationship_creation_patterns = [
            re.compile(r'CREATE\s*\([^)]*\)-\[[^\]]*\]->\([^)]*\)', re.IGNORECASE),
            re.compile(r'MERGE\s*\([^)]*\)-\[[^\]]*\]->\([^)]*\)', re.IGNORECASE),
            re.compile(r'-\[[^\]]*\]->', re.IGNORECASE)
        ]
        
        # Potentially dangerous patterns
        self.dangerous_patterns = [
            re.compile(r'DROP\s+DATABASE', re.IGNORECASE),
            re.compile(r'DROP\s+CONSTRAINT', re.IGNORECASE),
            re.compile(r'DROP\s+INDEX', re.IGNORECASE),
            re.compile(r'CALL\s+dbms\.shutdown', re.IGNORECASE),
            re.compile(r'CALL\s+dbms\.killConnection', re.IGNORECASE)
        ]
        
        # Required patterns for valid files
        self.required_patterns = [
            re.compile(r'CREATE|MERGE|MATCH', re.IGNORECASE)
        ]
    
    async def validate_cypher_file(self, file_path: str) -> ValidationResult:
        """
        Validate a Cypher commands file.
        
        Args:
            file_path: Path to the Cypher file
            
        Returns:
            ValidationResult with validation status and statistics
        """
        result = ValidationResult(
            is_valid=True,
            file_path=file_path
        )
        
        try:
            cypher_file = Path(file_path)
            
            # Check if file exists
            if not cypher_file.exists():
                result.add_error(f"File does not exist: {file_path}")
                return result
            
            # Check file size
            result.file_size_bytes = cypher_file.stat().st_size
            if result.file_size_bytes == 0:
                result.add_error("File is empty")
                return result
            
            # Read and validate file contents
            with open(cypher_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse commands
            commands = self._parse_cypher_commands(content)
            result.total_commands = len(commands)
            
            if result.total_commands == 0:
                result.add_error("No valid Cypher commands found in file")
                return result
            
            # Validate each command
            for i, command in enumerate(commands):
                command_errors = self._validate_command(command, i + 1)
                result.errors.extend(command_errors)
            
            # Estimate nodes and relationships
            result.estimated_nodes = self._estimate_nodes(commands)
            result.estimated_relationships = self._estimate_relationships(commands)
            
            # Check for dangerous patterns
            dangerous_warnings = self._check_dangerous_patterns(commands)
            result.warnings.extend(dangerous_warnings)
            
            # Check for required patterns
            if not self._has_required_patterns(content):
                result.add_warning("No CREATE, MERGE, or MATCH statements found - file may not contain valid Cypher")
            
            # Final validation
            if result.errors:
                result.is_valid = False
            
            logger.info(f"Validation completed: {file_path} - Valid: {result.is_valid}, Commands: {result.total_commands}")
            
            return result
            
        except Exception as e:
            logger.error(f"Validation failed for {file_path}: {e}")
            result.add_error(f"Validation error: {str(e)}")
            return result
    
    async def validate_cypher_commands(self, commands: List[str]) -> ValidationResult:
        """
        Validate a list of Cypher commands.
        
        Args:
            commands: List of Cypher command strings
            
        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(
            is_valid=True,
            file_path="<in_memory>",
            total_commands=len(commands)
        )
        
        try:
            if not commands:
                result.add_error("No commands provided")
                return result
            
            # Validate each command
            for i, command in enumerate(commands):
                command_errors = self._validate_command(command, i + 1)
                result.errors.extend(command_errors)
            
            # Estimate nodes and relationships
            result.estimated_nodes = self._estimate_nodes(commands)
            result.estimated_relationships = self._estimate_relationships(commands)
            
            # Check for dangerous patterns
            dangerous_warnings = self._check_dangerous_patterns(commands)
            result.warnings.extend(dangerous_warnings)
            
            # Final validation
            if result.errors:
                result.is_valid = False
            
            return result
            
        except Exception as e:
            logger.error(f"Command validation failed: {e}")
            result.add_error(f"Validation error: {str(e)}")
            return result
    
    def _parse_cypher_commands(self, content: str) -> List[str]:
        """Parse Cypher commands from file content."""
        commands = []
        current_command = []
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('//') or line.startswith('#'):
                continue
            
            # Add line to current command
            current_command.append(line)
            
            # Check if command is complete (ends with semicolon)
            if line.endswith(';'):
                command = ' '.join(current_command)
                commands.append(command)
                current_command = []
        
        # Handle final command without semicolon
        if current_command:
            command = ' '.join(current_command).strip()
            if command:
                commands.append(command)
        
        return commands
    
    def _validate_command(self, command: str, line_number: int) -> List[str]:
        """Validate a single Cypher command."""
        errors = []
        
        # Basic syntax checks
        if not command.strip():
            errors.append(f"Line {line_number}: Empty command")
            return errors
        
        # Check for balanced parentheses
        if command.count('(') != command.count(')'):
            errors.append(f"Line {line_number}: Unbalanced parentheses")
        
        # Check for balanced brackets
        if command.count('[') != command.count(']'):
            errors.append(f"Line {line_number}: Unbalanced brackets")
        
        # Check for balanced braces
        if command.count('{') != command.count('}'):
            errors.append(f"Line {line_number}: Unbalanced braces")
        
        # Check for basic Cypher keywords
        cypher_keywords = ['CREATE', 'MERGE', 'MATCH', 'RETURN', 'WHERE', 'SET', 'DELETE', 'REMOVE']
        has_keyword = any(keyword in command.upper() for keyword in cypher_keywords)
        
        if not has_keyword:
            errors.append(f"Line {line_number}: No recognized Cypher keywords found")
        
        return errors
    
    def _estimate_nodes(self, commands: List[str]) -> int:
        """Estimate number of nodes to be created."""
        total_nodes = 0
        
        for command in commands:
            for pattern in self.node_creation_patterns:
                matches = pattern.findall(command)
                total_nodes += len(matches)
        
        return total_nodes
    
    def _estimate_relationships(self, commands: List[str]) -> int:
        """Estimate number of relationships to be created."""
        total_relationships = 0
        
        for command in commands:
            for pattern in self.relationship_creation_patterns:
                matches = pattern.findall(command)
                total_relationships += len(matches)
        
        return total_relationships
    
    def _check_dangerous_patterns(self, commands: List[str]) -> List[str]:
        """Check for potentially dangerous Cypher patterns."""
        warnings = []
        
        for i, command in enumerate(commands):
            for pattern in self.dangerous_patterns:
                if pattern.search(command):
                    warnings.append(f"Command {i+1}: Contains potentially dangerous operation: {pattern.pattern}")
        
        return warnings
    
    def _has_required_patterns(self, content: str) -> bool:
        """Check if content has required Cypher patterns."""
        for pattern in self.required_patterns:
            if pattern.search(content):
                return True
        return False
    
    def get_validation_summary(self, result: ValidationResult) -> Dict[str, Any]:
        """Get a summary of validation results."""
        return {
            "file_path": result.file_path,
            "is_valid": result.is_valid,
            "file_size_mb": result.file_size_bytes / (1024 * 1024) if result.file_size_bytes else 0,
            "total_commands": result.total_commands,
            "estimated_nodes": result.estimated_nodes,
            "estimated_relationships": result.estimated_relationships,
            "error_count": len(result.errors),
            "warning_count": len(result.warnings),
            "errors": result.errors[:5],  # First 5 errors
            "warnings": result.warnings[:5]  # First 5 warnings
        }