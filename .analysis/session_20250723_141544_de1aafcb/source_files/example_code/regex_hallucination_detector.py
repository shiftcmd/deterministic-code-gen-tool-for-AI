#!/usr/bin/env python3
"""
Regex-based Hallucination Detection with Manual Review Flags

Detects suspicious patterns that often indicate AI hallucinations using regex patterns.
Creates flags for manual review of questionable code patterns.
"""

import re
import ast
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

class SuspicionLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SuspiciousPattern:
    """Represents a suspicious pattern found in code"""
    pattern_type: str
    pattern_name: str
    line_number: int
    column: int
    matched_text: str
    context: str
    suspicion_level: SuspicionLevel
    reason: str
    manual_review_required: bool
    suggestions: List[str]

class RegexHallucinationDetector:
    """Detects hallucinations using regex patterns and AST analysis"""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.suspicious_findings = []
    
    def _initialize_patterns(self) -> Dict[str, Dict]:
        """Initialize regex patterns for different types of hallucinations"""
        return {
            # AI-generated "helpful" method names
            "fake_methods": {
                "patterns": [
                    r'\b\w+\.(auto_\w+)\(',
                    r'\b\w+\.(smart_\w+)\(',
                    r'\b\w+\.(enhanced_\w+)\(',
                    r'\b\w+\.(super_\w+)\(',
                    r'\b\w+\.(magic_\w+)\(',
                    r'\b\w+\.(intelligent_\w+)\(',
                    r'\b\w+\.(advanced_\w+)\(',
                    r'\b\w+\.(optimized_\w+)\(',
                    r'\b\w+\.(better_\w+)\(',
                    r'\b\w+\.(improved_\w+)\(',
                    r'\b\w+\.(efficient_\w+)\(',
                    r'\b\w+\.(fast_\w+)\(',
                    r'\b\w+\.(quick_\w+)\(',
                    r'\b\w+\.(easy_\w+)\(',
                    r'\b\w+\.(simple_\w+)\(',
                ],
                "suspicion_level": SuspicionLevel.HIGH,
                "reason": "AI commonly generates 'helpful' method names that don't exist",
                "manual_review": True
            },
            
            # Fake string methods
            "fake_string_methods": {
                "patterns": [
                    r'\b\w*str\w*\.(super_\w+)\(',
                    r'\.(?:smart_split|super_split|enhanced_split|auto_split)\(',
                    r'\.(?:smart_join|super_join|enhanced_join|auto_join)\(',
                    r'\.(?:smart_replace|super_replace|enhanced_replace|auto_replace)\(',
                    r'\.(?:smart_format|super_format|enhanced_format|auto_format)\(',
                    r'\.(?:clean_whitespace|normalize_text|sanitize_text)\(',
                ],
                "suspicion_level": SuspicionLevel.HIGH,
                "reason": "String methods that don't exist in Python standard library",
                "manual_review": True
            },
            
            # Fake list/dict methods
            "fake_collection_methods": {
                "patterns": [
                    r'\.(?:smart_append|auto_append|enhanced_append)\(',
                    r'\.(?:smart_sort|auto_sort|enhanced_sort)\(',
                    r'\.(?:smart_filter|auto_filter|enhanced_filter)\(',
                    r'\.(?:smart_merge|auto_merge|enhanced_merge)\(',
                    r'\.(?:flatten|deep_copy|smart_copy)\(',
                    r'\.(?:unique|deduplicate|remove_duplicates)\(',
                ],
                "suspicion_level": SuspicionLevel.HIGH,
                "reason": "Collection methods that don't exist in Python standard library",
                "manual_review": True
            },
            
            # Fake OS/filesystem methods
            "fake_os_methods": {
                "patterns": [
                    r'os\.(?:get_all_files|list_all_files|find_files)\(',
                    r'os\.(?:create_directory|make_dirs|ensure_directory)\(',
                    r'os\.(?:copy_file|move_file|delete_file)\(',
                    r'os\.(?:get_file_size|get_file_info|file_exists)\(',
                    r'os\.(?:get_permissions|set_permissions|check_permissions)\(',
                ],
                "suspicion_level": SuspicionLevel.CRITICAL,
                "reason": "OS methods that don't exist - could cause runtime errors",
                "manual_review": True
            },
            
            # Fake request/HTTP methods
            "fake_http_methods": {
                "patterns": [
                    r'requests\.(?:get_with_retry|post_with_retry|put_with_retry)\(',
                    r'requests\.(?:safe_get|safe_post|safe_put)\(',
                    r'\.(?:get_json_safely|post_json_safely|put_json_safely)\(',
                    r'\.(?:with_timeout|with_retries|with_headers)\(',
                ],
                "suspicion_level": SuspicionLevel.HIGH,
                "reason": "HTTP methods that don't exist in requests library",
                "manual_review": True
            },
            
            # Suspicious parameter names
            "suspicious_parameters": {
                "patterns": [
                    r'\b(?:auto_retry|smart_retry|enhanced_retry)\s*=',
                    r'\b(?:auto_timeout|smart_timeout|enhanced_timeout)\s*=',
                    r'\b(?:auto_headers|smart_headers|enhanced_headers)\s*=',
                    r'\b(?:auto_validate|smart_validate|enhanced_validate)\s*=',
                    r'\b(?:auto_format|smart_format|enhanced_format)\s*=',
                    r'\b(?:auto_cache|smart_cache|enhanced_cache)\s*=',
                    r'\b(?:auto_compression|smart_compression|enhanced_compression)\s*=',
                    r'\b(?:intelligent_mode|smart_mode|enhanced_mode)\s*=',
                    r'\b(?:auto_optimization|smart_optimization|enhanced_optimization)\s*=',
                ],
                "suspicion_level": SuspicionLevel.MEDIUM,
                "reason": "Parameter names commonly hallucinated by AI",
                "manual_review": True
            },
            
            # Fake ML/AI library methods
            "fake_ml_methods": {
                "patterns": [
                    r'\.(?:auto_train|smart_train|enhanced_train)\(',
                    r'\.(?:auto_predict|smart_predict|enhanced_predict)\(',
                    r'\.(?:auto_fit|smart_fit|enhanced_fit)\(',
                    r'\.(?:optimize_automatically|auto_optimize|smart_optimize)\(',
                    r'\.(?:auto_tune|smart_tune|enhanced_tune)\(',
                ],
                "suspicion_level": SuspicionLevel.HIGH,
                "reason": "ML methods that are commonly hallucinated",
                "manual_review": True
            },
            
            # Fake database methods
            "fake_db_methods": {
                "patterns": [
                    r'\.(?:execute_safely|execute_with_retry|safe_execute)\(',
                    r'\.(?:fetch_all_optimized|fetch_optimized|smart_fetch)\(',
                    r'\.(?:auto_commit|smart_commit|enhanced_commit)\(',
                    r'\.(?:auto_rollback|smart_rollback|enhanced_rollback)\(',
                ],
                "suspicion_level": SuspicionLevel.HIGH,
                "reason": "Database methods that don't exist in standard libraries",
                "manual_review": True
            },
            
            # Suspicious imports
            "suspicious_imports": {
                "patterns": [
                    r'from\s+(\w+)\s+import\s+(?:auto_\w+|smart_\w+|enhanced_\w+)',
                    r'import\s+(\w+\.(?:auto_\w+|smart_\w+|enhanced_\w+))',
                    r'from\s+(\w+\.helpers?)\s+import',
                    r'from\s+(\w+\.utils?)\s+import',
                ],
                "suspicion_level": SuspicionLevel.MEDIUM,
                "reason": "Import patterns that might indicate hallucinated modules",
                "manual_review": True
            },
            
            # Chained method calls that look suspicious
            "suspicious_chaining": {
                "patterns": [
                    r'\.(?:auto_\w+|smart_\w+|enhanced_\w+)\.(?:auto_\w+|smart_\w+|enhanced_\w+)',
                    r'\.(?:with_\w+)\.(?:with_\w+)\.(?:with_\w+)',
                    r'\.(?:then_\w+)\.(?:then_\w+)',
                ],
                "suspicion_level": SuspicionLevel.MEDIUM,
                "reason": "Chained method calls that might be hallucinated",
                "manual_review": True
            },
            
            # Context managers that don't exist
            "fake_context_managers": {
                "patterns": [
                    r'with\s+\w+\.(?:auto_\w+|smart_\w+|enhanced_\w+)\(',
                    r'with\s+\w+\.(?:safe_\w+|protected_\w+|managed_\w+)\(',
                ],
                "suspicion_level": SuspicionLevel.HIGH,
                "reason": "Context managers that likely don't exist",
                "manual_review": True
            },
            
            # Decorators that might be hallucinated
            "suspicious_decorators": {
                "patterns": [
                    r'@(?:auto_\w+|smart_\w+|enhanced_\w+)',
                    r'@(?:cached_property|memoized|auto_retry)',
                    r'@(?:validate_input|validate_output|auto_validate)',
                ],
                "suspicion_level": SuspicionLevel.MEDIUM,
                "reason": "Decorators that might be hallucinated",
                "manual_review": True
            }
        }
    
    def analyze_code(self, code: str, filename: str = "unknown") -> List[SuspiciousPattern]:
        """Analyze code for suspicious patterns"""
        self.suspicious_findings = []
        lines = code.split('\n')
        
        # Run regex pattern detection
        for pattern_type, pattern_info in self.patterns.items():
            for pattern in pattern_info["patterns"]:
                self._check_pattern(pattern, code, lines, pattern_type, pattern_info)
        
        # Additional AST-based analysis
        try:
            tree = ast.parse(code)
            self._analyze_ast(tree, code, lines)
        except SyntaxError as e:
            logger.warning(f"Could not parse AST for {filename}: {e}")
        
        return self.suspicious_findings
    
    def _check_pattern(self, pattern: str, code: str, lines: List[str], 
                      pattern_type: str, pattern_info: Dict):
        """Check a specific regex pattern against the code"""
        for match in re.finditer(pattern, code, re.MULTILINE):
            line_num = code[:match.start()].count('\n') + 1
            col_num = match.start() - code.rfind('\n', 0, match.start())
            
            # Get context (surrounding lines)
            context_start = max(0, line_num - 3)
            context_end = min(len(lines), line_num + 2)
            context = '\n'.join(lines[context_start:context_end])
            
            # Generate suggestions
            suggestions = self._generate_suggestions(pattern_type, match.group(0))
            
            finding = SuspiciousPattern(
                pattern_type=pattern_type,
                pattern_name=pattern,
                line_number=line_num,
                column=col_num,
                matched_text=match.group(0),
                context=context,
                suspicion_level=pattern_info["suspicion_level"],
                reason=pattern_info["reason"],
                manual_review_required=pattern_info["manual_review"],
                suggestions=suggestions
            )
            
            self.suspicious_findings.append(finding)
    
    def _analyze_ast(self, tree: ast.AST, code: str, lines: List[str]):
        """Additional AST-based analysis for complex patterns"""
        for node in ast.walk(tree):
            # Check for suspicious function calls
            if isinstance(node, ast.Call):
                self._check_suspicious_call(node, code, lines)
            
            # Check for suspicious attribute access
            elif isinstance(node, ast.Attribute):
                self._check_suspicious_attribute(node, code, lines)
    
    def _check_suspicious_call(self, node: ast.Call, code: str, lines: List[str]):
        """Check for suspicious function calls in AST"""
        if isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr
            
            # Check for methods with too many parameters (potential hallucination)
            if len(node.args) + len(node.keywords) > 8:
                self._add_ast_finding(
                    "excessive_parameters",
                    f"Function call with {len(node.args) + len(node.keywords)} parameters",
                    node.lineno,
                    node.col_offset,
                    lines,
                    SuspicionLevel.MEDIUM,
                    "Functions with excessive parameters might be hallucinated",
                    ["Verify function signature", "Check official documentation"]
                )
            
            # Check for methods that return 'self' in a suspicious way
            if attr_name in ['then', 'and_then', 'also', 'chain', 'pipe']:
                self._add_ast_finding(
                    "suspicious_fluent_interface",
                    f"Fluent interface method: {attr_name}",
                    node.lineno,
                    node.col_offset,
                    lines,
                    SuspicionLevel.MEDIUM,
                    "Fluent interface methods might be hallucinated",
                    ["Check if library actually supports fluent interface"]
                )
    
    def _check_suspicious_attribute(self, node: ast.Attribute, code: str, lines: List[str]):
        """Check for suspicious attribute access"""
        attr_name = node.attr
        
        # Check for attributes that follow suspicious patterns
        if any(prefix in attr_name for prefix in ['auto_', 'smart_', 'enhanced_', 'magic_']):
            self._add_ast_finding(
                "suspicious_attribute",
                f"Suspicious attribute: {attr_name}",
                node.lineno,
                node.col_offset,
                lines,
                SuspicionLevel.HIGH,
                "Attributes with AI-like prefixes are often hallucinated",
                [f"Verify {attr_name} exists in the object's class"]
            )
    
    def _add_ast_finding(self, pattern_type: str, matched_text: str, line_num: int, 
                        col_num: int, lines: List[str], suspicion_level: SuspicionLevel,
                        reason: str, suggestions: List[str]):
        """Add a finding from AST analysis"""
        context_start = max(0, line_num - 3)
        context_end = min(len(lines), line_num + 2)
        context = '\n'.join(lines[context_start:context_end])
        
        finding = SuspiciousPattern(
            pattern_type=pattern_type,
            pattern_name="ast_analysis",
            line_number=line_num,
            column=col_num,
            matched_text=matched_text,
            context=context,
            suspicion_level=suspicion_level,
            reason=reason,
            manual_review_required=True,
            suggestions=suggestions
        )
        
        self.suspicious_findings.append(finding)
    
    def _generate_suggestions(self, pattern_type: str, matched_text: str) -> List[str]:
        """Generate suggestions for fixing suspicious patterns"""
        suggestions = []
        
        if pattern_type == "fake_methods":
            method_name = matched_text.split('.')[-1].replace('(', '')
            suggestions.extend([
                f"Check if {method_name} actually exists in the class documentation",
                f"Consider using standard library methods instead",
                f"Search for {method_name} in official documentation"
            ])
        
        elif pattern_type == "fake_string_methods":
            suggestions.extend([
                "Check Python string methods documentation",
                "Use built-in string methods like split(), join(), replace()",
                "Consider using regex module for complex string operations"
            ])
        
        elif pattern_type == "fake_collection_methods":
            suggestions.extend([
                "Check Python list/dict methods documentation",
                "Use built-in methods like append(), sort(), filter()",
                "Consider using collections module for advanced operations"
            ])
        
        elif pattern_type == "fake_os_methods":
            suggestions.extend([
                "Check os module documentation",
                "Use pathlib.Path for file operations",
                "Consider using shutil for file operations"
            ])
        
        elif pattern_type == "suspicious_parameters":
            param_name = matched_text.split('=')[0].strip()
            suggestions.extend([
                f"Check if {param_name} is a valid parameter",
                "Review function signature in documentation",
                "Remove if parameter doesn't exist"
            ])
        
        else:
            suggestions.append("Verify this pattern exists in official documentation")
        
        return suggestions
    
    def generate_report(self, findings: List[SuspiciousPattern], filename: str) -> Dict[str, Any]:
        """Generate a comprehensive report of findings"""
        
        # Group findings by suspicion level
        by_level = {}
        for level in SuspicionLevel:
            by_level[level.value] = [f for f in findings if f.suspicion_level == level]
        
        # Group findings by pattern type
        by_type = {}
        for finding in findings:
            if finding.pattern_type not in by_type:
                by_type[finding.pattern_type] = []
            by_type[finding.pattern_type].append(finding)
        
        # Calculate statistics
        total_findings = len(findings)
        manual_review_count = sum(1 for f in findings if f.manual_review_required)
        
        report = {
            "filename": filename,
            "analysis_timestamp": str(Path(__file__).stat().st_mtime),
            "summary": {
                "total_findings": total_findings,
                "manual_review_required": manual_review_count,
                "critical_findings": len(by_level.get("critical", [])),
                "high_findings": len(by_level.get("high", [])),
                "medium_findings": len(by_level.get("medium", [])),
                "low_findings": len(by_level.get("low", []))
            },
            "findings_by_level": {
                level: [self._finding_to_dict(f) for f in findings_list]
                for level, findings_list in by_level.items()
            },
            "findings_by_type": {
                ptype: [self._finding_to_dict(f) for f in findings_list]
                for ptype, findings_list in by_type.items()
            },
            "manual_review_flags": [
                self._finding_to_dict(f) for f in findings if f.manual_review_required
            ]
        }
        
        return report
    
    def _finding_to_dict(self, finding: SuspiciousPattern) -> Dict[str, Any]:
        """Convert finding to dictionary for JSON serialization"""
        return {
            "pattern_type": finding.pattern_type,
            "pattern_name": finding.pattern_name,
            "line_number": finding.line_number,
            "column": finding.column,
            "matched_text": finding.matched_text,
            "context": finding.context,
            "suspicion_level": finding.suspicion_level.value,
            "reason": finding.reason,
            "manual_review_required": finding.manual_review_required,
            "suggestions": finding.suggestions
        }
    
    def save_report(self, report: Dict[str, Any], output_path: str):
        """Save report to JSON file"""
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Regex hallucination report saved to {output_path}")
    
    def print_summary(self, report: Dict[str, Any]):
        """Print a summary of findings"""
        summary = report["summary"]
        
        print(f"\n{'='*60}")
        print("🔍 REGEX HALLUCINATION DETECTION SUMMARY")
        print(f"{'='*60}")
        print(f"File: {report['filename']}")
        print(f"Total Findings: {summary['total_findings']}")
        print(f"Manual Review Required: {summary['manual_review_required']}")
        print(f"  🔴 Critical: {summary['critical_findings']}")
        print(f"  🟠 High: {summary['high_findings']}")
        print(f"  🟡 Medium: {summary['medium_findings']}")
        print(f"  🟢 Low: {summary['low_findings']}")
        
        if summary['manual_review_required'] > 0:
            print(f"\n⚠️  {summary['manual_review_required']} items require manual review!")
            
            # Show top 5 manual review items
            manual_items = report['manual_review_flags'][:5]
            for i, item in enumerate(manual_items, 1):
                print(f"\n{i}. {item['pattern_type']} (Line {item['line_number']})")
                print(f"   Found: {item['matched_text']}")
                print(f"   Reason: {item['reason']}")
                if item['suggestions']:
                    print(f"   Suggestion: {item['suggestions'][0]}")
        
        print(f"{'='*60}")

# CLI interface
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Regex-based Hallucination Detection")
    parser.add_argument("file", help="Python file to analyze")
    parser.add_argument("--output", help="Output JSON file path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    
    detector = RegexHallucinationDetector()
    
    try:
        with open(args.file, 'r') as f:
            code = f.read()
        
        findings = detector.analyze_code(code, args.file)
        report = detector.generate_report(findings, args.file)
        
        detector.print_summary(report)
        
        if args.output:
            detector.save_report(report, args.output)
        
    except Exception as e:
        print(f"Error analyzing {args.file}: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())