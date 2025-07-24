#!/usr/bin/env python3
"""
Hallucination Detection Framework

Multi-layered approach to detect AI code hallucinations while avoiding self-validation bias.
Uses independent validation sources and adversarial testing.
"""

import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    SYNTAX = "syntax"
    STATIC_ANALYSIS = "static_analysis"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    RUNTIME = "runtime"
    HUMAN_REVIEW = "human_review"

@dataclass
class HallucinationReport:
    is_hallucination: bool
    confidence: float
    issues: List[Dict[str, Any]]
    validation_layers: Dict[ValidationLevel, bool]
    suggestions: List[str]

class IndependentValidationLayer:
    """Base class for independent validation layers"""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
    
    async def validate(self, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

class SyntaxValidationLayer(IndependentValidationLayer):
    """Validates basic Python syntax"""
    
    def __init__(self):
        super().__init__("syntax")
    
    async def validate(self, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            ast.parse(code)
            return {"valid": True, "issues": []}
        except SyntaxError as e:
            return {
                "valid": False,
                "issues": [{
                    "type": "syntax_error",
                    "message": str(e),
                    "line": e.lineno,
                    "offset": e.offset
                }]
            }

class StaticAnalysisLayer(IndependentValidationLayer):
    """Uses external static analysis tools"""
    
    def __init__(self):
        super().__init__("static_analysis")
    
    async def validate(self, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        issues = []
        
        # Write code to temp file for analysis
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Run pylint
            result = subprocess.run(
                [sys.executable, '-m', 'pylint', temp_file, '--output-format=json'],
                capture_output=True, text=True
            )
            
            if result.returncode != 0:
                try:
                    import json
                    pylint_issues = json.loads(result.stdout)
                    for issue in pylint_issues:
                        issues.append({
                            "type": "pylint_" + issue.get("type", "unknown"),
                            "message": issue.get("message", ""),
                            "line": issue.get("line", 0),
                            "symbol": issue.get("symbol", "")
                        })
                except json.JSONDecodeError:
                    logger.warning("Failed to parse pylint output")
            
            # Run mypy for type checking
            result = subprocess.run(
                [sys.executable, '-m', 'mypy', temp_file, '--show-error-codes'],
                capture_output=True, text=True
            )
            
            if result.returncode != 0:
                for line in result.stdout.split('\n'):
                    if ':' in line and 'error:' in line:
                        issues.append({
                            "type": "mypy_error",
                            "message": line.split('error:')[-1].strip(),
                            "line": line.split(':')[1] if ':' in line else 0
                        })
        
        finally:
            # Cleanup
            Path(temp_file).unlink(missing_ok=True)
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }

class KnowledgeGraphLayer(IndependentValidationLayer):
    """Validates against your Neo4j knowledge graph"""
    
    def __init__(self, neo4j_extractor):
        super().__init__("knowledge_graph")
        self.extractor = neo4j_extractor
    
    async def validate(self, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        issues = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"valid": False, "issues": [{"type": "syntax_error", "message": "Cannot parse code"}]}
        
        # Check function calls against knowledge graph
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    # Method call
                    method_name = node.func.attr
                    class_name = context.get('class_context')
                    module_name = context.get('module_context')
                    
                    if class_name and module_name:
                        validation = await self.extractor.validate_function_signature(
                            module_name, method_name, class_name
                        )
                        if not validation['has_stub_definition']:
                            issues.append({
                                "type": "unknown_method",
                                "method": method_name,
                                "class": class_name,
                                "line": node.lineno,
                                "confidence": 0.8
                            })
                
                elif isinstance(node.func, ast.Name):
                    # Function call
                    func_name = node.func.id
                    module_name = context.get('module_context')
                    
                    if module_name:
                        validation = await self.extractor.validate_function_signature(
                            module_name, func_name
                        )
                        if not validation['has_stub_definition']:
                            issues.append({
                                "type": "unknown_function",
                                "function": func_name,
                                "line": node.lineno,
                                "confidence": 0.7
                            })
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }

class RuntimeValidationLayer(IndependentValidationLayer):
    """Attempts to import and validate runtime behavior"""
    
    def __init__(self):
        super().__init__("runtime")
    
    async def validate(self, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        issues = []
        
        # Extract imports
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"valid": False, "issues": [{"type": "syntax_error"}]}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    try:
                        importlib.import_module(alias.name)
                    except ImportError:
                        issues.append({
                            "type": "import_error",
                            "module": alias.name,
                            "line": node.lineno
                        })
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    try:
                        module = importlib.import_module(node.module)
                        for alias in node.names:
                            if not hasattr(module, alias.name):
                                issues.append({
                                    "type": "missing_attribute",
                                    "module": node.module,
                                    "attribute": alias.name,
                                    "line": node.lineno
                                })
                    except ImportError:
                        issues.append({
                            "type": "import_error",
                            "module": node.module,
                            "line": node.lineno
                        })
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }

class HallucinationDetector:
    """Main hallucination detection orchestrator"""
    
    def __init__(self, neo4j_extractor=None):
        self.layers = [
            SyntaxValidationLayer(),
            StaticAnalysisLayer(),
            RuntimeValidationLayer()
        ]
        
        if neo4j_extractor:
            self.layers.append(KnowledgeGraphLayer(neo4j_extractor))
    
    async def detect_hallucinations(self, code: str, context: Dict[str, Any]) -> HallucinationReport:
        """Run all validation layers and compile report"""
        all_issues = []
        layer_results = {}
        
        for layer in self.layers:
            if layer.enabled:
                try:
                    result = await layer.validate(code, context)
                    layer_results[ValidationLevel(layer.name)] = result["valid"]
                    all_issues.extend(result["issues"])
                except Exception as e:
                    logger.error(f"Layer {layer.name} failed: {e}")
                    layer_results[ValidationLevel(layer.name)] = False
        
        # Calculate confidence and determine if hallucination
        total_issues = len(all_issues)
        critical_issues = sum(1 for issue in all_issues if issue.get("type") in [
            "syntax_error", "import_error", "unknown_method", "unknown_function"
        ])
        
        is_hallucination = critical_issues > 0
        confidence = max(0.0, 1.0 - (total_issues * 0.1) - (critical_issues * 0.3))
        
        # Generate suggestions
        suggestions = []
        if critical_issues > 0:
            suggestions.append("Review function/method names against codebase")
        if any(issue.get("type") == "import_error" for issue in all_issues):
            suggestions.append("Verify import statements and dependencies")
        if any(issue.get("type").startswith("pylint_") for issue in all_issues):
            suggestions.append("Address static analysis warnings")
        
        return HallucinationReport(
            is_hallucination=is_hallucination,
            confidence=confidence,
            issues=all_issues,
            validation_layers=layer_results,
            suggestions=suggestions
        )

# Example usage and testing
async def test_hallucination_detection():
    """Test the hallucination detection system"""
    detector = HallucinationDetector()
    
    # Test case 1: Valid code
    valid_code = """
import os
import sys

def hello_world():
    print("Hello, world!")
    return True
"""
    
    result = await detector.detect_hallucinations(valid_code, {})
    print(f"Valid code result: {result}")
    
    # Test case 2: Invalid imports
    invalid_code = """
import nonexistent_module
from fake_package import fake_function

def test():
    fake_function()
    return nonexistent_module.some_method()
"""
    
    result = await detector.detect_hallucinations(invalid_code, {})
    print(f"Invalid code result: {result}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_hallucination_detection())