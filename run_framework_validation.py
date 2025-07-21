#!/usr/bin/env python3
"""
Run Framework Validation on Python Debug Tool Codebase

This script analyzes the existing codebase using the deterministic AI framework
and provides a comprehensive validation report.
"""

import ast
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class FileAnalysis:
    """Analysis result for a single file"""
    file_path: str
    valid: bool
    syntax_valid: bool
    risk_level: str
    confidence: float
    issues: List[str]
    suggestions: List[str]
    metadata: Dict[str, Any]

class SimpleValidator:
    """Simplified validator that works without external dependencies"""
    
    def __init__(self):
        self.hallucination_patterns = [
            (r'\.auto_[a-zA-Z_]+\(', "Suspicious 'auto_' method"),
            (r'\.smart_[a-zA-Z_]+\(', "Suspicious 'smart_' method"),
            (r'\.enhanced_[a-zA-Z_]+\(', "Suspicious 'enhanced_' method"),
            (r'\.magic_[a-zA-Z_]+\(', "Suspicious 'magic_' method"),
            (r'import\s+magic', "Suspicious 'magic' import"),
            (r'from\s+utils\.helpers', "Generic 'utils.helpers' import"),
            (r'from\s+magic', "Suspicious 'magic' module import"),
        ]
        
        self.placeholder_patterns = [
            "TODO",
            "FIXME", 
            "XXX",
            "HACK",
            "Your code here",
            "pass  # Implement",
            "raise NotImplementedError"
        ]
    
    def analyze_file(self, file_path: str) -> FileAnalysis:
        """Analyze a single Python file"""
        logger.info(f"Analyzing {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return FileAnalysis(
                file_path=file_path,
                valid=False,
                syntax_valid=False,
                risk_level="critical",
                confidence=0.0,
                issues=[f"Failed to read file: {e}"],
                suggestions=[],
                metadata={"error": str(e)}
            )
        
        issues = []
        suggestions = []
        metadata = {}
        
        # 1. Check syntax
        syntax_valid = True
        try:
            tree = ast.parse(content)
            metadata["ast_nodes"] = len(list(ast.walk(tree)))
            metadata["imports"] = self._extract_imports(tree)
            metadata["classes"] = self._extract_classes(tree)
            metadata["functions"] = self._extract_functions(tree)
        except SyntaxError as e:
            syntax_valid = False
            issues.append(f"Syntax error: {e}")
        
        # 2. Check for hallucination patterns
        for pattern, description in self.hallucination_patterns:
            if re.search(pattern, content):
                issues.append(description)
        
        # 3. Check for placeholders
        for placeholder in self.placeholder_patterns:
            if placeholder in content:
                # Check if it's in a comment (acceptable) or code (problematic)
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if placeholder in line:
                        # Simple check: if # appears before placeholder, it's likely a comment
                        if '#' not in line or line.index('#') > line.index(placeholder):
                            issues.append(f"Placeholder '{placeholder}' in code at line {i}")
        
        # 4. Check code quality indicators
        if syntax_valid and tree:
            self._analyze_code_quality(tree, content, issues, suggestions, metadata)
        
        # 5. Calculate confidence and risk
        confidence = self._calculate_confidence(syntax_valid, len(issues), metadata)
        risk_level = self._calculate_risk_level(syntax_valid, issues)
        
        return FileAnalysis(
            file_path=file_path,
            valid=syntax_valid and len(issues) == 0,
            syntax_valid=syntax_valid,
            risk_level=risk_level,
            confidence=confidence,
            issues=issues,
            suggestions=suggestions,
            metadata=metadata
        )
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        return imports
    
    def _extract_classes(self, tree: ast.AST) -> List[str]:
        """Extract class names"""
        return [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    
    def _extract_functions(self, tree: ast.AST) -> List[str]:
        """Extract function names"""
        return [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    
    def _analyze_code_quality(self, tree: ast.AST, content: str, issues: List[str], 
                            suggestions: List[str], metadata: Dict[str, Any]):
        """Analyze code quality aspects"""
        
        # Count different node types
        node_counts = {}
        for node in ast.walk(tree):
            node_type = type(node).__name__
            node_counts[node_type] = node_counts.get(node_type, 0) + 1
        
        metadata["node_counts"] = node_counts
        
        # Check for docstrings
        functions_with_docstrings = 0
        classes_with_docstrings = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if ast.get_docstring(node):
                    functions_with_docstrings += 1
            elif isinstance(node, ast.ClassDef):
                if ast.get_docstring(node):
                    classes_with_docstrings += 1
        
        total_functions = node_counts.get("FunctionDef", 0)
        total_classes = node_counts.get("ClassDef", 0)
        
        if total_functions > 0:
            docstring_ratio = functions_with_docstrings / total_functions
            metadata["function_docstring_ratio"] = docstring_ratio
            if docstring_ratio < 0.5:
                suggestions.append("Consider adding docstrings to more functions")
        
        if total_classes > 0:
            class_docstring_ratio = classes_with_docstrings / total_classes
            metadata["class_docstring_ratio"] = class_docstring_ratio
            if class_docstring_ratio < 0.5:
                suggestions.append("Consider adding docstrings to more classes")
        
        # Check for type hints
        functions_with_annotations = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.returns or any(arg.annotation for arg in node.args.args):
                    functions_with_annotations += 1
        
        if total_functions > 0:
            annotation_ratio = functions_with_annotations / total_functions
            metadata["type_annotation_ratio"] = annotation_ratio
            if annotation_ratio < 0.3:
                suggestions.append("Consider adding type annotations")
        
        # Check complexity (simple heuristic)
        complexity_score = (
            node_counts.get("If", 0) + 
            node_counts.get("For", 0) + 
            node_counts.get("While", 0) + 
            node_counts.get("Try", 0)
        )
        
        metadata["complexity_score"] = complexity_score
        if complexity_score > 20:
            suggestions.append("Consider breaking down complex functions")
        
        # Check for error handling
        try_blocks = node_counts.get("Try", 0)
        if try_blocks == 0 and total_functions > 2:
            suggestions.append("Consider adding error handling")
    
    def _calculate_confidence(self, syntax_valid: bool, issue_count: int, 
                            metadata: Dict[str, Any]) -> float:
        """Calculate confidence score (0.0 to 1.0)"""
        if not syntax_valid:
            return 0.0
        
        base_confidence = 1.0
        
        # Reduce confidence for issues
        confidence = base_confidence - (issue_count * 0.1)
        
        # Bonus for good practices
        if metadata.get("function_docstring_ratio", 0) > 0.7:
            confidence += 0.05
        
        if metadata.get("type_annotation_ratio", 0) > 0.5:
            confidence += 0.05
        
        return max(0.0, min(1.0, confidence))
    
    def _calculate_risk_level(self, syntax_valid: bool, issues: List[str]) -> str:
        """Calculate risk level"""
        if not syntax_valid:
            return "critical"
        
        # Check for critical patterns
        critical_keywords = ["Syntax error", "magic import", "Suspicious 'magic'"]
        if any(keyword in issue for issue in issues for keyword in critical_keywords):
            return "critical"
        
        if len(issues) > 5:
            return "high"
        elif len(issues) > 2:
            return "medium"
        elif len(issues) > 0:
            return "low"
        else:
            return "minimal"

def analyze_project() -> Dict[str, Any]:
    """Analyze the entire project"""
    print("🔍 Running Deterministic AI Framework Validation")
    print("=" * 60)
    
    validator = SimpleValidator()
    results = []
    
    # Main framework files
    main_files = [
        "deterministic_code_framework.py",
        "dev_validator.py", 
        "ai_code_assistant.py",
        "setup_framework.py",
        "demo_framework.py"
    ]
    
    print("📁 Analyzing Main Framework Files:")
    print("-" * 40)
    for file_path in main_files:
        if Path(file_path).exists():
            analysis = validator.analyze_file(file_path)
            results.append(analysis)
            print(f"{'✅' if analysis.valid else '❌'} {file_path}")
            if analysis.issues:
                for issue in analysis.issues[:3]:  # Show first 3 issues
                    print(f"   • {issue}")
    
    # Example code files
    example_files = list(Path("example_code").glob("*.py"))
    
    print(f"\n📁 Analyzing Example Code Files ({len(example_files)} files):")
    print("-" * 40)
    for file_path in example_files:
        analysis = validator.analyze_file(str(file_path))
        results.append(analysis)
        print(f"{'✅' if analysis.valid else '❌'} {file_path.name}")
        if analysis.issues:
            for issue in analysis.issues[:2]:  # Show first 2 issues
                print(f"   • {issue}")
    
    # Generate summary
    summary = generate_summary(results)
    
    return {
        "results": results,
        "summary": summary
    }

def generate_summary(results: List[FileAnalysis]) -> Dict[str, Any]:
    """Generate analysis summary"""
    total_files = len(results)
    valid_files = sum(1 for r in results if r.valid)
    syntax_valid_files = sum(1 for r in results if r.syntax_valid)
    
    # Risk distribution
    risk_counts = {}
    for result in results:
        risk_counts[result.risk_level] = risk_counts.get(result.risk_level, 0) + 1
    
    # Average confidence
    avg_confidence = sum(r.confidence for r in results) / total_files if total_files > 0 else 0
    
    # Most common issues
    all_issues = []
    for result in results:
        all_issues.extend(result.issues)
    
    issue_counts = {}
    for issue in all_issues:
        issue_counts[issue] = issue_counts.get(issue, 0) + 1
    
    common_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "total_files": total_files,
        "valid_files": valid_files,
        "syntax_valid_files": syntax_valid_files,
        "average_confidence": avg_confidence,
        "risk_distribution": risk_counts,
        "common_issues": common_issues,
        "validation_rate": valid_files / total_files if total_files > 0 else 0
    }

def print_detailed_summary(summary: Dict[str, Any]):
    """Print detailed summary report"""
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY REPORT")
    print("=" * 60)
    
    print(f"📁 Total Files Analyzed: {summary['total_files']}")
    print(f"✅ Valid Files: {summary['valid_files']}")
    print(f"🔧 Syntax Valid: {summary['syntax_valid_files']}")
    print(f"📈 Validation Rate: {summary['validation_rate']:.1%}")
    print(f"🎯 Average Confidence: {summary['average_confidence']:.1%}")
    
    print(f"\n🚨 Risk Level Distribution:")
    for risk_level, count in summary['risk_distribution'].items():
        print(f"   {risk_level.upper()}: {count} files")
    
    if summary['common_issues']:
        print(f"\n⚠️  Most Common Issues:")
        for issue, count in summary['common_issues']:
            print(f"   • {issue} ({count} files)")
    
    print(f"\n💡 Framework Assessment:")
    if summary['validation_rate'] > 0.8:
        print("   ✅ Excellent - Most files pass validation")
    elif summary['validation_rate'] > 0.6:
        print("   ⚠️  Good - Some files need attention")
    else:
        print("   🚨 Needs Work - Multiple files require fixes")

def save_results(analysis_data: Dict[str, Any]):
    """Save results to JSON file"""
    # Convert FileAnalysis objects to dictionaries for JSON serialization
    serializable_results = []
    for result in analysis_data["results"]:
        serializable_results.append({
            "file_path": result.file_path,
            "valid": result.valid,
            "syntax_valid": result.syntax_valid,
            "risk_level": result.risk_level,
            "confidence": result.confidence,
            "issues": result.issues,
            "suggestions": result.suggestions,
            "metadata": result.metadata
        })
    
    output_data = {
        "results": serializable_results,
        "summary": analysis_data["summary"]
    }
    
    output_file = "framework_validation_report.json"
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")

def main():
    """Main execution function"""
    try:
        analysis_data = analyze_project()
        print_detailed_summary(analysis_data["summary"])
        save_results(analysis_data)
        
        print("\n🎯 Next Steps:")
        print("   1. Review files with validation issues")
        print("   2. Apply suggested improvements")
        print("   3. Re-run validation to track progress")
        print("   4. Use framework for new code generation")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        print(f"❌ Analysis failed: {e}")

if __name__ == "__main__":
    main()