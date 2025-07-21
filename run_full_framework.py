#!/usr/bin/env python3
"""
Full Framework Execution on Python Debug Tool Codebase

Runs the complete deterministic AI framework end-to-end on the entire
/home/amo/coding_projects/python_debug_tool/ directory structure.
"""

import os
import ast
import re
import json
import time
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class FileAnalysis:
    """Complete analysis result for a single file"""
    file_path: str
    relative_path: str
    directory: str
    file_size: int
    lines_of_code: int
    syntax_valid: bool
    imports: List[str]
    classes: List[str]
    functions: List[str]
    complexity_score: int
    issues: List[str]
    suggestions: List[str]
    confidence: float
    risk_level: str
    metadata: Dict[str, Any]

@dataclass
class DirectoryAnalysis:
    """Analysis of a directory"""
    path: str
    python_files: int
    total_lines: int
    total_classes: int
    total_functions: int
    avg_confidence: float
    risk_distribution: Dict[str, int]
    common_issues: List[Tuple[str, int]]

class FullFrameworkRunner:
    """Complete framework execution on entire codebase"""
    
    def __init__(self, root_path: str = "/home/amo/coding_projects/python_debug_tool"):
        self.root_path = Path(root_path)
        self.start_time = datetime.now()
        self.file_analyses: List[FileAnalysis] = []
        self.directory_analyses: Dict[str, DirectoryAnalysis] = {}
        
        # Validation patterns
        self.hallucination_patterns = [
            (r'\.auto_[a-zA-Z_]+\(', "Suspicious 'auto_' method"),
            (r'\.smart_[a-zA-Z_]+\(', "Suspicious 'smart_' method"),
            (r'\.enhanced_[a-zA-Z_]+\(', "Suspicious 'enhanced_' method"),
            (r'\.magic_[a-zA-Z_]+\(', "Suspicious 'magic_' method"),
            (r'import\s+magic\b', "Suspicious 'magic' import"),
            (r'from\s+utils\.helpers', "Generic 'utils.helpers' import"),
            (r'from\s+magic', "Suspicious 'magic' module import"),
            (r'\.strip_all\(', "Non-existent string method 'strip_all'"),
            (r'\.remove_whitespace\(', "Non-existent string method 'remove_whitespace'"),
        ]
        
        # Exclude patterns
        self.exclude_patterns = [
            "venv/", "__pycache__/", ".git/", "node_modules/", 
            ".pytest_cache/", "*.pyc", "*.pyo", "*.egg-info/"
        ]
    
    def should_exclude_path(self, path: Path) -> bool:
        """Check if path should be excluded"""
        path_str = str(path)
        for pattern in self.exclude_patterns:
            if pattern.replace("*", "") in path_str:
                return True
        return False
    
    def discover_python_files(self) -> List[Path]:
        """Discover all Python files in the codebase"""
        logger.info(f"Discovering Python files in {self.root_path}")
        
        python_files = []
        
        # Walk through all directories
        for root, dirs, files in os.walk(self.root_path):
            root_path = Path(root)
            
            # Skip excluded directories
            if self.should_exclude_path(root_path):
                continue
            
            # Filter out excluded directories for further traversal
            dirs[:] = [d for d in dirs if not self.should_exclude_path(root_path / d)]
            
            # Find Python files
            for file in files:
                if file.endswith(('.py', '.pyi')):
                    file_path = root_path / file
                    if not self.should_exclude_path(file_path):
                        python_files.append(file_path)
        
        logger.info(f"Found {len(python_files)} Python files")
        return python_files
    
    def analyze_file(self, file_path: Path) -> FileAnalysis:
        """Perform complete analysis on a single file"""
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic file info
            file_size = file_path.stat().st_size
            lines_of_code = len([line for line in content.split('\n') if line.strip()])
            relative_path = str(file_path.relative_to(self.root_path))
            directory = str(file_path.parent.relative_to(self.root_path))
            
            # Parse AST
            syntax_valid = True
            tree = None
            syntax_error = None
            
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                syntax_valid = False
                syntax_error = str(e)
            
            # Extract code elements
            imports = []
            classes = []
            functions = []
            complexity_score = 0
            
            if tree:
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module or ""
                        for alias in node.names:
                            imports.append(f"{module}.{alias.name}" if module else alias.name)
                    elif isinstance(node, ast.ClassDef):
                        classes.append(node.name)
                    elif isinstance(node, ast.FunctionDef):
                        functions.append(node.name)
                    elif isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
                        complexity_score += 1
            
            # Check for issues
            issues = []
            suggestions = []
            
            if not syntax_valid:
                issues.append(f"Syntax error: {syntax_error}")
            
            # Check hallucination patterns
            for pattern, description in self.hallucination_patterns:
                if re.search(pattern, content):
                    issues.append(description)
            
            # Check for placeholders
            placeholder_patterns = ["TODO", "FIXME", "XXX", "HACK", "raise NotImplementedError"]
            for placeholder in placeholder_patterns:
                if placeholder in content:
                    # Check if it's in a comment or string
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if placeholder in line:
                            # Simple heuristic: if # appears before placeholder, likely a comment
                            if '#' not in line or line.index('#') > line.index(placeholder):
                                issues.append(f"Placeholder '{placeholder}' in code at line {i}")
            
            # Generate suggestions
            if tree:
                # Check for docstrings
                functions_with_docs = sum(1 for node in ast.walk(tree) 
                                        if isinstance(node, ast.FunctionDef) and ast.get_docstring(node))
                classes_with_docs = sum(1 for node in ast.walk(tree) 
                                      if isinstance(node, ast.ClassDef) and ast.get_docstring(node))
                
                if len(functions) > 0 and functions_with_docs / len(functions) < 0.5:
                    suggestions.append("Consider adding docstrings to more functions")
                
                if len(classes) > 0 and classes_with_docs / len(classes) < 0.5:
                    suggestions.append("Consider adding docstrings to more classes")
                
                # Check for type hints
                functions_with_annotations = sum(1 for node in ast.walk(tree)
                                               if isinstance(node, ast.FunctionDef) and 
                                               (node.returns or any(arg.annotation for arg in node.args.args)))
                
                if len(functions) > 0 and functions_with_annotations / len(functions) < 0.3:
                    suggestions.append("Consider adding type annotations")
                
                if complexity_score > 20:
                    suggestions.append("Consider breaking down complex functions")
            
            # Calculate confidence and risk
            confidence = self._calculate_confidence(syntax_valid, len(issues), complexity_score, lines_of_code)
            risk_level = self._calculate_risk_level(syntax_valid, issues)
            
            # Metadata
            metadata = {
                "last_modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                "encoding": "utf-8",
                "ast_nodes": len(list(ast.walk(tree))) if tree else 0,
                "import_count": len(imports),
                "class_count": len(classes),
                "function_count": len(functions),
                "complexity_score": complexity_score
            }
            
            return FileAnalysis(
                file_path=str(file_path),
                relative_path=relative_path,
                directory=directory,
                file_size=file_size,
                lines_of_code=lines_of_code,
                syntax_valid=syntax_valid,
                imports=imports,
                classes=classes,
                functions=functions,
                complexity_score=complexity_score,
                issues=issues,
                suggestions=suggestions,
                confidence=confidence,
                risk_level=risk_level,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze {file_path}: {e}")
            return FileAnalysis(
                file_path=str(file_path),
                relative_path=str(file_path.relative_to(self.root_path)),
                directory=str(file_path.parent.relative_to(self.root_path)),
                file_size=0,
                lines_of_code=0,
                syntax_valid=False,
                imports=[],
                classes=[],
                functions=[],
                complexity_score=0,
                issues=[f"Analysis failed: {e}"],
                suggestions=[],
                confidence=0.0,
                risk_level="critical",
                metadata={"error": str(e)}
            )
    
    def _calculate_confidence(self, syntax_valid: bool, issue_count: int, 
                            complexity: int, lines: int) -> float:
        """Calculate confidence score"""
        if not syntax_valid:
            return 0.0
        
        base_confidence = 1.0
        
        # Reduce for issues
        confidence = base_confidence - (issue_count * 0.1)
        
        # Reduce for high complexity
        if complexity > 15:
            confidence -= 0.1
        if complexity > 30:
            confidence -= 0.1
        
        # Slight bonus for reasonable file size
        if 50 <= lines <= 500:
            confidence += 0.05
        
        return max(0.0, min(1.0, confidence))
    
    def _calculate_risk_level(self, syntax_valid: bool, issues: List[str]) -> str:
        """Calculate risk level"""
        if not syntax_valid:
            return "critical"
        
        # Check for critical patterns
        critical_keywords = ["Syntax error", "magic import", "Analysis failed"]
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
    
    def analyze_directory(self, directory_files: List[FileAnalysis]) -> DirectoryAnalysis:
        """Analyze a directory based on its files"""
        if not directory_files:
            return DirectoryAnalysis("", 0, 0, 0, 0, 0.0, {}, [])
        
        directory = directory_files[0].directory
        python_files = len(directory_files)
        total_lines = sum(f.lines_of_code for f in directory_files)
        total_classes = sum(len(f.classes) for f in directory_files)
        total_functions = sum(len(f.functions) for f in directory_files)
        avg_confidence = sum(f.confidence for f in directory_files) / python_files
        
        # Risk distribution
        risk_distribution = {}
        for file_analysis in directory_files:
            risk = file_analysis.risk_level
            risk_distribution[risk] = risk_distribution.get(risk, 0) + 1
        
        # Common issues
        all_issues = []
        for file_analysis in directory_files:
            all_issues.extend(file_analysis.issues)
        
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        common_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return DirectoryAnalysis(
            path=directory,
            python_files=python_files,
            total_lines=total_lines,
            total_classes=total_classes,
            total_functions=total_functions,
            avg_confidence=avg_confidence,
            risk_distribution=risk_distribution,
            common_issues=common_issues
        )
    
    def run_full_analysis(self, selected_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run complete framework analysis"""
        logger.info("Starting full framework analysis...")
        
        # Discover files
        if selected_files:
            # Filter to only analyze selected files
            python_files = []
            for file_path in selected_files:
                full_path = self.root_path / file_path if not os.path.isabs(file_path) else Path(file_path)
                if full_path.exists() and full_path.suffix in ['.py', '.pyi']:
                    python_files.append(full_path)
            logger.info(f"Analyzing {len(python_files)} selected files out of {len(selected_files)} provided")
        else:
            python_files = self.discover_python_files()
        
        if not python_files:
            logger.warning("No Python files found!")
            return {"error": "No Python files found"}
        
        # Analyze each file
        logger.info(f"Analyzing {len(python_files)} files...")
        
        for i, file_path in enumerate(python_files, 1):
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{len(python_files)} files analyzed")
            
            analysis = self.analyze_file(file_path)
            self.file_analyses.append(analysis)
        
        # Group by directory
        directory_groups = {}
        for analysis in self.file_analyses:
            directory = analysis.directory
            if directory not in directory_groups:
                directory_groups[directory] = []
            directory_groups[directory].append(analysis)
        
        # Analyze directories
        for directory, files in directory_groups.items():
            self.directory_analyses[directory] = self.analyze_directory(files)
        
        # Generate summary
        summary = self._generate_summary()
        
        logger.info("Full analysis complete!")
        return summary
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate comprehensive summary"""
        total_files = len(self.file_analyses)
        total_directories = len(self.directory_analyses)
        
        # Overall statistics
        syntax_valid_files = sum(1 for f in self.file_analyses if f.syntax_valid)
        total_lines = sum(f.lines_of_code for f in self.file_analyses)
        total_classes = sum(len(f.classes) for f in self.file_analyses)
        total_functions = sum(len(f.functions) for f in self.file_analyses)
        avg_confidence = sum(f.confidence for f in self.file_analyses) / total_files if total_files else 0
        
        # Risk distribution
        risk_distribution = {}
        for analysis in self.file_analyses:
            risk = analysis.risk_level
            risk_distribution[risk] = risk_distribution.get(risk, 0) + 1
        
        # File size distribution
        size_distribution = {"small": 0, "medium": 0, "large": 0, "very_large": 0}
        for analysis in self.file_analyses:
            lines = analysis.lines_of_code
            if lines < 100:
                size_distribution["small"] += 1
            elif lines < 300:
                size_distribution["medium"] += 1
            elif lines < 1000:
                size_distribution["large"] += 1
            else:
                size_distribution["very_large"] += 1
        
        # Most common issues
        all_issues = []
        for analysis in self.file_analyses:
            all_issues.extend(analysis.issues)
        
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        common_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Top directories by complexity
        top_complex_dirs = sorted(
            [(dir_name, analysis.total_lines) for dir_name, analysis in self.directory_analyses.items()],
            key=lambda x: x[1], reverse=True
        )[:10]
        
        # Files with highest risk
        high_risk_files = [
            {"file": f.relative_path, "risk": f.risk_level, "issues": len(f.issues)}
            for f in self.file_analyses 
            if f.risk_level in ["critical", "high"]
        ]
        high_risk_files.sort(key=lambda x: (x["risk"] == "critical", x["issues"]), reverse=True)
        
        execution_time = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "analysis_metadata": {
                "start_time": self.start_time.isoformat(),
                "execution_time_seconds": execution_time,
                "root_path": str(self.root_path),
                "framework_version": "1.0.0"
            },
            "overall_statistics": {
                "total_files": total_files,
                "total_directories": total_directories,
                "syntax_valid_files": syntax_valid_files,
                "validation_rate": syntax_valid_files / total_files if total_files else 0,
                "total_lines_of_code": total_lines,
                "total_classes": total_classes,
                "total_functions": total_functions,
                "average_confidence": avg_confidence
            },
            "risk_assessment": {
                "distribution": risk_distribution,
                "high_risk_files": high_risk_files[:20],  # Top 20 high-risk files
                "total_issues": len(all_issues),
                "unique_issue_types": len(issue_counts)
            },
            "code_metrics": {
                "file_size_distribution": size_distribution,
                "average_file_size": total_lines / total_files if total_files else 0,
                "largest_files": [
                    {"file": f.relative_path, "lines": f.lines_of_code}
                    for f in sorted(self.file_analyses, key=lambda x: x.lines_of_code, reverse=True)[:10]
                ],
                "most_complex_files": [
                    {"file": f.relative_path, "complexity": f.complexity_score}
                    for f in sorted(self.file_analyses, key=lambda x: x.complexity_score, reverse=True)[:10]
                ]
            },
            "directory_analysis": {
                "top_directories_by_size": top_complex_dirs,
                "directory_details": {
                    name: {
                        "files": analysis.python_files,
                        "lines": analysis.total_lines,
                        "classes": analysis.total_classes,
                        "functions": analysis.total_functions,
                        "avg_confidence": analysis.avg_confidence,
                        "risk_distribution": analysis.risk_distribution
                    }
                    for name, analysis in self.directory_analyses.items()
                }
            },
            "quality_analysis": {
                "common_issues": common_issues,
                "files_needing_attention": len(high_risk_files),
                "overall_health_score": self._calculate_health_score(),
                "recommendations": self._generate_recommendations()
            }
        }
    
    def _calculate_health_score(self) -> float:
        """Calculate overall codebase health score (0-100)"""
        if not self.file_analyses:
            return 0.0
        
        # Base score from average confidence
        avg_confidence = sum(f.confidence for f in self.file_analyses) / len(self.file_analyses)
        base_score = avg_confidence * 70  # 70% weight
        
        # Syntax validity bonus
        syntax_valid_ratio = sum(1 for f in self.file_analyses if f.syntax_valid) / len(self.file_analyses)
        syntax_score = syntax_valid_ratio * 20  # 20% weight
        
        # Risk penalty
        risk_penalty = 0
        for analysis in self.file_analyses:
            if analysis.risk_level == "critical":
                risk_penalty += 2
            elif analysis.risk_level == "high":
                risk_penalty += 1
            elif analysis.risk_level == "medium":
                risk_penalty += 0.5
        
        risk_score = max(0, 10 - (risk_penalty / len(self.file_analyses)) * 10)  # 10% weight
        
        return min(100, base_score + syntax_score + risk_score)
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        if not self.file_analyses:
            return ["No files analyzed"]
        
        # Syntax issues
        syntax_invalid = sum(1 for f in self.file_analyses if not f.syntax_valid)
        if syntax_invalid > 0:
            recommendations.append(f"Fix {syntax_invalid} files with syntax errors")
        
        # Risk issues
        risk_counts = {}
        for analysis in self.file_analyses:
            risk = analysis.risk_level
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
        
        if risk_counts.get("critical", 0) > 0:
            recommendations.append(f"Address {risk_counts['critical']} critical risk files immediately")
        
        if risk_counts.get("high", 0) > 0:
            recommendations.append(f"Review {risk_counts['high']} high risk files")
        
        # Code quality
        avg_confidence = sum(f.confidence for f in self.file_analyses) / len(self.file_analyses)
        if avg_confidence < 0.7:
            recommendations.append("Improve overall code quality - confidence below 70%")
        
        # Documentation
        files_without_docs = sum(1 for f in self.file_analyses 
                               if "Consider adding docstrings" in " ".join(f.suggestions))
        if files_without_docs > len(self.file_analyses) * 0.3:
            recommendations.append("Add docstrings to improve documentation coverage")
        
        # Complexity
        complex_files = sum(1 for f in self.file_analyses if f.complexity_score > 20)
        if complex_files > 0:
            recommendations.append(f"Refactor {complex_files} highly complex files")
        
        return recommendations
    
    def save_results(self, results: Dict[str, Any], filename: str = "full_framework_analysis.json"):
        """Save complete results to file"""
        # Add file-level details
        results["file_details"] = []
        for analysis in self.file_analyses:
            results["file_details"].append({
                "file_path": analysis.relative_path,
                "directory": analysis.directory,
                "file_size": analysis.file_size,
                "lines_of_code": analysis.lines_of_code,
                "syntax_valid": analysis.syntax_valid,
                "classes": analysis.classes,
                "functions": analysis.functions,
                "imports": analysis.imports,
                "complexity_score": analysis.complexity_score,
                "confidence": analysis.confidence,
                "risk_level": analysis.risk_level,
                "issues": analysis.issues,
                "suggestions": analysis.suggestions,
                "metadata": analysis.metadata
            })
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Complete analysis saved to: {filename}")
    
    def save_actionable_report(self, results: Dict[str, Any], filename: str = "actionable_framework_report.json"):
        """Save actionable report with key findings and recommendations"""
        # Create focused actionable report
        actionable_report = {
            "run_metadata": {
                "run_id": results.get('run_id'),
                "timestamp": results.get('run_timestamp', datetime.now().isoformat()),
                "project_path": str(self.root_path),
                "files_analyzed": len(self.file_analyses)
            },
            "summary": {
                "total_files": results.get("total_files", 0),
                "health_score": results.get("health_score", 0),
                "total_issues": results.get("risk_assessment", {}).get("total_issues", 0),
                "critical_files": len([f for f in self.file_analyses if f.risk_level == "critical"]),
                "high_risk_files": len([f for f in self.file_analyses if f.risk_level in ["high", "critical"]])
            },
            "priority_actions": self.generate_priority_actions(results),
            "file_recommendations": self.generate_file_recommendations(),
            "next_steps": self.generate_next_steps(results)
        }
        
        with open(filename, 'w') as f:
            json.dump(actionable_report, f, indent=2, default=str)
        
        logger.info(f"Actionable report saved to: {filename}")
    
    def generate_priority_actions(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate priority actions based on analysis results"""
        actions = []
        
        # Critical files requiring immediate attention
        critical_files = [f for f in self.file_analyses if f.risk_level == "critical"]
        if critical_files:
            actions.append({
                "priority": "critical",
                "action": "Fix critical risk files",
                "description": f"Address {len(critical_files)} files with critical risk levels",
                "files": [f.relative_path for f in critical_files[:5]],  # Top 5
                "impact": "high"
            })
        
        # Syntax errors
        syntax_errors = [f for f in self.file_analyses if not f.syntax_valid]
        if syntax_errors:
            actions.append({
                "priority": "high",
                "action": "Fix syntax errors",
                "description": f"Resolve syntax errors in {len(syntax_errors)} files",
                "files": [f.relative_path for f in syntax_errors],
                "impact": "high"
            })
        
        # High complexity files
        complex_files = [f for f in self.file_analyses if f.complexity_score > 10]
        if complex_files:
            actions.append({
                "priority": "medium",
                "action": "Refactor complex files",
                "description": f"Simplify {len(complex_files)} highly complex files",
                "files": [f.relative_path for f in complex_files[:10]],  # Top 10
                "impact": "medium"
            })
        
        return actions
    
    def generate_file_recommendations(self) -> List[Dict[str, Any]]:
        """Generate specific file recommendations"""
        recommendations = []
        
        for analysis in self.file_analyses:
            if analysis.risk_level in ["high", "critical"] or not analysis.syntax_valid:
                recommendations.append({
                    "file": analysis.relative_path,
                    "risk_level": analysis.risk_level,
                    "syntax_valid": analysis.syntax_valid,
                    "confidence": analysis.confidence,
                    "issues": analysis.issues,
                    "suggestions": analysis.suggestions
                })
        
        return recommendations[:20]  # Top 20 files needing attention
    
    def generate_next_steps(self, results: Dict[str, Any]) -> List[str]:
        """Generate next steps for the project"""
        steps = []
        
        if results.get("risk_assessment", {}).get("total_issues", 0) > 0:
            steps.append("1. Review and address all critical and high-priority issues")
        
        syntax_issues = len([f for f in self.file_analyses if not f.syntax_valid])
        if syntax_issues > 0:
            steps.append(f"2. Fix {syntax_issues} syntax errors to ensure code reliability")
        
        complex_files = len([f for f in self.file_analyses if f.complexity_score > 10])
        if complex_files > 0:
            steps.append(f"3. Refactor {complex_files} complex files to improve maintainability")
        
        steps.append("4. Run the analysis again after fixes to track improvement")
        steps.append("5. Set up continuous monitoring for ongoing code quality")
        
        return steps
    
    def print_summary_report(self, results: Dict[str, Any]):
        """Print human-readable summary report"""
        print("\n" + "=" * 80)
        print("🎯 DETERMINISTIC AI FRAMEWORK - FULL CODEBASE ANALYSIS")
        print("=" * 80)
        
        meta = results["analysis_metadata"]
        stats = results["overall_statistics"]
        risk = results["risk_assessment"]
        quality = results["quality_analysis"]
        
        print(f"📁 Root Path: {meta['root_path']}")
        print(f"⏱️  Execution Time: {meta['execution_time_seconds']:.2f} seconds")
        print(f"📊 Health Score: {quality['overall_health_score']:.1f}/100")
        
        print(f"\n📈 OVERALL STATISTICS")
        print("-" * 40)
        print(f"Total Files: {stats['total_files']}")
        print(f"Total Directories: {stats['total_directories']}")
        print(f"Lines of Code: {stats['total_lines_of_code']:,}")
        print(f"Classes: {stats['total_classes']}")
        print(f"Functions: {stats['total_functions']}")
        print(f"Syntax Valid: {stats['syntax_valid_files']}/{stats['total_files']} ({stats['validation_rate']:.1%})")
        print(f"Average Confidence: {stats['average_confidence']:.1%}")
        
        print(f"\n🚨 RISK ASSESSMENT")
        print("-" * 40)
        print(f"Total Issues: {risk['total_issues']}")
        print(f"Unique Issue Types: {risk['unique_issue_types']}")
        print("Risk Distribution:")
        for risk_level, count in risk["distribution"].items():
            emoji = {"critical": "🛑", "high": "🚨", "medium": "⚠️", "low": "📊", "minimal": "✅"}
            print(f"  {emoji.get(risk_level, '•')} {risk_level.upper()}: {count} files")
        
        if risk["high_risk_files"]:
            print(f"\nTop High-Risk Files:")
            for file_info in risk["high_risk_files"][:10]:
                print(f"  🚨 {file_info['file']} - {file_info['risk']} ({file_info['issues']} issues)")
        
        print(f"\n📋 TOP ISSUES")
        print("-" * 40)
        for issue, count in quality["common_issues"][:10]:
            print(f"  • {issue} ({count} files)")
        
        print(f"\n🏗️ DIRECTORY ANALYSIS")
        print("-" * 40)
        dir_details = results["directory_analysis"]["directory_details"]
        for dir_name, details in sorted(dir_details.items(), key=lambda x: x[1]["lines"], reverse=True)[:10]:
            if dir_name:  # Skip root directory
                print(f"  📁 {dir_name}")
                print(f"     Files: {details['files']}, Lines: {details['lines']:,}, Confidence: {details['avg_confidence']:.1%}")
        
        print(f"\n💡 RECOMMENDATIONS")
        print("-" * 40)
        for rec in quality["recommendations"]:
            print(f"  • {rec}")
        
        print(f"\n🎯 FRAMEWORK CAPABILITIES DEMONSTRATED:")
        print("-" * 40)
        print("  ✅ Complete codebase discovery and analysis")
        print("  ✅ Multi-layer validation (syntax, patterns, complexity)")
        print("  ✅ Risk assessment and confidence scoring")
        print("  ✅ Directory-level and file-level insights")
        print("  ✅ Actionable recommendations for improvement")
        print("  ✅ Comprehensive reporting and data export")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run Full Framework Analysis")
    parser.add_argument('--project-path', default='/home/amo/coding_projects/python_debug_tool/',
                       help='Path to the project to analyze')
    parser.add_argument('--file-list', help='Path to file containing list of files to analyze')
    parser.add_argument('--run-id', help='Unique run ID for this analysis')
    parser.add_argument('--output-format', default='json', choices=['json', 'yaml'],
                       help='Output format for results')
    parser.add_argument('--quiet', action='store_true', help='Suppress console output')
    return parser.parse_args()

def main():
    """Main execution function"""
    args = parse_args()
    
    if not args.quiet:
        print("🚀 Starting Full Framework Analysis...")
        print(f"🎯 Target: {args.project_path}")
        print("=" * 60)
    
    try:
        # Initialize runner with custom path
        runner = FullFrameworkRunner(root_path=args.project_path)
        
        # If file list is provided, filter to only those files
        if args.file_list and os.path.exists(args.file_list):
            with open(args.file_list, 'r') as f:
                selected_files = [line.strip() for line in f if line.strip()]
            logger.info(f"Analyzing {len(selected_files)} selected files from {args.file_list}")
        else:
            selected_files = None
            
        # Run analysis
        results = runner.run_full_analysis(selected_files=selected_files)
        
        if "error" in results:
            logger.error(f"Analysis failed: {results['error']}")
            if not args.quiet:
                print(f"❌ Analysis failed: {results['error']}")
            sys.exit(1)
        
        # Add run metadata
        if args.run_id:
            results['run_id'] = args.run_id
            results['run_timestamp'] = datetime.now().isoformat()
        
        # Print summary unless quiet
        if not args.quiet:
            runner.print_summary_report(results)
        
        # Save detailed results with run ID if provided
        output_filename = f"full_framework_analysis_{args.run_id}.json" if args.run_id else "full_framework_analysis.json"
        runner.save_results(results, filename=output_filename)
        
        # Also save actionable report
        actionable_filename = f"actionable_framework_report_{args.run_id}.json" if args.run_id else "actionable_framework_report.json"
        runner.save_actionable_report(results, filename=actionable_filename)
        
        if not args.quiet:
            print(f"\n🎉 Full Framework Analysis Complete!")
            print("=" * 60)
            print(f"📊 Detailed results saved to: {output_filename}")
            print(f"📋 Actionable report saved to: {actionable_filename}")
            print("🚀 Framework successfully analyzed your codebase!")
            
        logger.info(f"Analysis completed successfully. Results saved to {output_filename}")
        
    except Exception as e:
        logger.error(f"Fatal error during analysis: {e}")
        if not args.quiet:
            print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()