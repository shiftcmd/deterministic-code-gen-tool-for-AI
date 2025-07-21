#!/usr/bin/env python3
"""
Developer Validation Tool

A practical tool for validating AI-generated code against the project's knowledge graph.
Can be used as a pre-commit hook, IDE integration, or standalone validator.
"""

import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict, Tuple
import ast
import re
import logging
from neo4j import GraphDatabase
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QuickValidator:
    """Lightweight validator for rapid code checking"""
    
    def __init__(self, config_path: str = ".validator.yml"):
        self.config = self._load_config(config_path)
        self._init_neo4j()
        self._load_patterns()
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        default_config = {
            "neo4j": {
                "uri": "bolt://localhost:7687",
                "user": "neo4j",
                "password": "password"
            },
            "validation": {
                "check_imports": True,
                "check_methods": True,
                "check_hallucinations": True,
                "max_risk_level": "medium"
            },
            "patterns": {
                "suspicious_prefixes": ["auto_", "smart_", "enhanced_", "magic_"],
                "blocked_imports": ["magic", "utils.helpers"],
                "placeholder_patterns": ["TODO", "FIXME", "Your code here", "..."]
            }
        }
        
        try:
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                # Merge with defaults
                return {**default_config, **user_config}
        except FileNotFoundError:
            logger.info(f"Config file not found, using defaults")
            return default_config
    
    def _init_neo4j(self):
        """Initialize Neo4j connection"""
        neo4j_config = self.config["neo4j"]
        self.neo4j_driver = GraphDatabase.driver(
            neo4j_config["uri"],
            auth=(neo4j_config["user"], neo4j_config["password"])
        )
    
    def _load_patterns(self):
        """Load suspicious patterns from config"""
        patterns_config = self.config["patterns"]
        self.suspicious_patterns = []
        
        # Add prefix patterns
        for prefix in patterns_config["suspicious_prefixes"]:
            self.suspicious_patterns.append(
                (f'\\.{prefix}[a-zA-Z_]+\\(', f"Suspicious '{prefix}' method")
            )
        
        # Add blocked imports
        for imp in patterns_config["blocked_imports"]:
            self.suspicious_patterns.append(
                (f'import\\s+{imp}|from\\s+{imp}', f"Blocked import '{imp}'")
            )
    
    def validate_file(self, file_path: str) -> Tuple[bool, List[str], Dict]:
        """Validate a single Python file"""
        logger.info(f"Validating {file_path}")
        
        try:
            with open(file_path, 'r') as f:
                code = f.read()
        except Exception as e:
            return False, [f"Failed to read file: {e}"], {}
        
        issues = []
        metadata = {"file": file_path}
        
        # Parse AST
        try:
            tree = ast.parse(code)
            metadata["ast_valid"] = True
        except SyntaxError as e:
            issues.append(f"Syntax error: {e}")
            metadata["ast_valid"] = False
            return False, issues, metadata
        
        # Run validations
        if self.config["validation"]["check_imports"]:
            import_issues = self._validate_imports(tree)
            issues.extend(import_issues)
        
        if self.config["validation"]["check_methods"]:
            method_issues = self._validate_methods(tree)
            issues.extend(method_issues)
        
        if self.config["validation"]["check_hallucinations"]:
            hallucination_issues = self._check_hallucinations(code)
            issues.extend(hallucination_issues)
        
        # Check for placeholders
        placeholder_issues = self._check_placeholders(code)
        issues.extend(placeholder_issues)
        
        metadata["issue_count"] = len(issues)
        metadata["risk_level"] = self._calculate_risk_level(issues)
        
        # Check if risk level is acceptable
        max_risk = self.config["validation"]["max_risk_level"]
        risk_order = ["low", "medium", "high", "critical"]
        current_risk_index = risk_order.index(metadata["risk_level"])
        max_risk_index = risk_order.index(max_risk)
        
        valid = len(issues) == 0 or current_risk_index <= max_risk_index
        
        return valid, issues, metadata
    
    def _validate_imports(self, tree: ast.AST) -> List[str]:
        """Validate imports against knowledge graph"""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if not self._module_exists(alias.name):
                        issues.append(f"Unknown module: {alias.name}")
            
            elif isinstance(node, ast.ImportFrom):
                if node.module and not self._module_exists(node.module):
                    issues.append(f"Unknown module: {node.module}")
                
                # Check specific imports
                for alias in node.names:
                    if not self._api_exists(node.module, alias.name):
                        issues.append(f"Unknown API: {node.module}.{alias.name}")
        
        return issues
    
    def _validate_methods(self, tree: ast.AST) -> List[str]:
        """Validate method calls against knowledge graph"""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    method_name = node.func.attr
                    
                    # Check against suspicious patterns
                    for pattern, desc in self.suspicious_patterns:
                        if re.match(pattern.replace('\\.', ''), f".{method_name}("):
                            issues.append(desc)
                            break
        
        return issues
    
    def _check_hallucinations(self, code: str) -> List[str]:
        """Check for common AI hallucinations"""
        issues = []
        
        for pattern, description in self.suspicious_patterns:
            if re.search(pattern, code):
                issues.append(description)
        
        return issues
    
    def _check_placeholders(self, code: str) -> List[str]:
        """Check for placeholder code"""
        issues = []
        
        for placeholder in self.config["patterns"]["placeholder_patterns"]:
            if placeholder in code:
                # Check if it's in a comment (acceptable) or in code (not acceptable)
                lines = code.split('\n')
                for i, line in enumerate(lines):
                    if placeholder in line:
                        # Simple check: if # appears before placeholder, it's a comment
                        if '#' not in line or line.index('#') > line.index(placeholder):
                            issues.append(f"Placeholder '{placeholder}' found in code at line {i+1}")
        
        return issues
    
    def _module_exists(self, module_name: str) -> bool:
        """Check if module exists in knowledge graph"""
        # First check standard library modules
        if module_name in sys.stdlib_module_names:
            return True
        
        # Check knowledge graph
        query = "MATCH (m:Module {name: $name}) RETURN COUNT(m) > 0 as exists"
        with self.neo4j_driver.session() as session:
            try:
                result = session.run(query, name=module_name)
                return result.single()["exists"]
            except:
                # If Neo4j fails, assume module is valid (fail open)
                return True
    
    def _api_exists(self, module: str, api_name: str) -> bool:
        """Check if specific API exists in module"""
        query = """
        MATCH (m:Module {name: $module})-[:DEFINES]->(api {name: $api_name})
        WHERE api:Function OR api:Class
        RETURN COUNT(api) > 0 as exists
        """
        with self.neo4j_driver.session() as session:
            try:
                result = session.run(query, module=module, api_name=api_name)
                return result.single()["exists"]
            except:
                return True  # Fail open
    
    def _calculate_risk_level(self, issues: List[str]) -> str:
        """Calculate risk level based on issues"""
        if not issues:
            return "low"
        
        # Check for critical patterns
        critical_keywords = ["Unknown module", "Blocked import", "Syntax error"]
        if any(keyword in issue for issue in issues for keyword in critical_keywords):
            return "critical"
        
        # Risk based on issue count
        if len(issues) > 5:
            return "high"
        elif len(issues) > 2:
            return "medium"
        else:
            return "low"
    
    def validate_directory(self, directory: str) -> Tuple[int, int, List[Dict]]:
        """Validate all Python files in a directory"""
        path = Path(directory)
        python_files = list(path.rglob("*.py"))
        
        results = []
        valid_count = 0
        
        for file_path in python_files:
            valid, issues, metadata = self.validate_file(str(file_path))
            if valid:
                valid_count += 1
            
            results.append({
                "file": str(file_path),
                "valid": valid,
                "issues": issues,
                "metadata": metadata
            })
        
        return valid_count, len(python_files), results
    
    def close(self):
        """Close connections"""
        if hasattr(self, 'neo4j_driver'):
            self.neo4j_driver.close()


def format_validation_output(results: List[Dict], verbose: bool = False) -> str:
    """Format validation results for display"""
    output = []
    
    # Summary
    total = len(results)
    valid = sum(1 for r in results if r["valid"])
    invalid = total - valid
    
    output.append(f"\n{'='*60}")
    output.append(f"Validation Summary")
    output.append(f"{'='*60}")
    output.append(f"Total files: {total}")
    output.append(f"Valid: {valid} ✓")
    output.append(f"Invalid: {invalid} ✗")
    output.append(f"{'='*60}\n")
    
    # Details for invalid files
    if invalid > 0:
        output.append("Issues Found:")
        output.append("-" * 60)
        
        for result in results:
            if not result["valid"]:
                output.append(f"\n📄 {result['file']}")
                output.append(f"   Risk Level: {result['metadata']['risk_level'].upper()}")
                output.append(f"   Issues ({len(result['issues'])}):")
                
                for issue in result['issues']:
                    output.append(f"   ❌ {issue}")
    
    # Verbose mode shows all files
    if verbose and valid > 0:
        output.append("\n\nValid Files:")
        output.append("-" * 60)
        for result in results:
            if result["valid"]:
                output.append(f"✓ {result['file']}")
    
    return "\n".join(output)


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Validate Python code against project knowledge graph"
    )
    parser.add_argument(
        "path",
        help="File or directory to validate"
    )
    parser.add_argument(
        "-c", "--config",
        default=".validator.yml",
        help="Configuration file path"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show verbose output"
    )
    parser.add_argument(
        "-j", "--json",
        action="store_true",
        help="Output results as JSON"
    )
    parser.add_argument(
        "--fail-on-issues",
        action="store_true",
        help="Exit with non-zero code if any issues found"
    )
    
    args = parser.parse_args()
    
    # Initialize validator
    validator = QuickValidator(args.config)
    
    try:
        path = Path(args.path)
        
        if path.is_file():
            # Validate single file
            valid, issues, metadata = validator.validate_file(str(path))
            results = [{
                "file": str(path),
                "valid": valid,
                "issues": issues,
                "metadata": metadata
            }]
        elif path.is_dir():
            # Validate directory
            valid_count, total_count, results = validator.validate_directory(str(path))
        else:
            print(f"Error: {path} is not a valid file or directory")
            sys.exit(1)
        
        # Output results
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print(format_validation_output(results, args.verbose))
        
        # Exit code
        if args.fail_on_issues:
            invalid_count = sum(1 for r in results if not r["valid"])
            sys.exit(1 if invalid_count > 0 else 0)
        
    finally:
        validator.close()


if __name__ == "__main__":
    main()