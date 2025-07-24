#!/usr/bin/env python3
"""
Comprehensive Hallucination Detector

Combines knowledge graph validation, regex pattern detection, and manual review flags
for comprehensive AI hallucination detection.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Import our components
from regex_hallucination_detector import RegexHallucinationDetector, SuspiciousPattern
from hallucination_detection_framework import HallucinationDetector as FrameworkDetector

# Import existing knowledge graph components
import sys
sys.path.append('knowledge_graphs')
from ai_hallucination_detector import AIHallucinationDetector

logger = logging.getLogger(__name__)

@dataclass
class ComprehensiveResult:
    """Combined results from all detection methods"""
    filename: str
    timestamp: str
    
    # Knowledge graph results
    kg_confidence: float
    kg_hallucinations: List[Dict[str, Any]]
    kg_valid: bool
    
    # Framework results
    framework_confidence: float
    framework_issues: List[Dict[str, Any]]
    framework_valid: bool
    
    # Regex results
    regex_findings: List[SuspiciousPattern]
    manual_review_count: int
    critical_patterns: int
    
    # Combined assessment
    overall_confidence: float
    needs_manual_review: bool
    risk_level: str
    recommendations: List[str]

class ComprehensiveHallucinationDetector:
    """Comprehensive detector combining multiple approaches"""
    
    def __init__(self, neo4j_uri: str = "bolt://localhost:7687", 
                 neo4j_user: str = "neo4j", 
                 neo4j_password: str = "no_auth"):
        self.kg_detector = AIHallucinationDetector(neo4j_uri, neo4j_user, neo4j_password)
        self.framework_detector = FrameworkDetector()
        self.regex_detector = RegexHallucinationDetector()
        
    async def initialize(self):
        """Initialize all detection components"""
        await self.kg_detector.initialize()
        logger.info("Comprehensive hallucination detector initialized")
    
    async def analyze_file(self, file_path: str, output_dir: Optional[str] = None) -> ComprehensiveResult:
        """Analyze a file using all detection methods"""
        logger.info(f"Starting comprehensive analysis of {file_path}")
        
        # Read the file
        with open(file_path, 'r') as f:
            code = f.read()
        
        # 1. Knowledge Graph Analysis
        logger.info("Running knowledge graph analysis...")
        kg_result = await self.kg_detector.detect_hallucinations(
            file_path, 
            output_dir=output_dir, 
            save_json=False, 
            save_markdown=False, 
            print_summary=False
        )
        
        # 2. Framework Analysis
        logger.info("Running framework analysis...")
        context = {
            'script_path': file_path,
            'module_context': Path(file_path).stem
        }
        framework_result = await self.framework_detector.detect_hallucinations(code, context)
        
        # 3. Regex Pattern Analysis
        logger.info("Running regex pattern analysis...")
        regex_findings = self.regex_detector.analyze_code(code, file_path)
        
        # 4. Combine Results
        logger.info("Combining results...")
        combined_result = self._combine_results(file_path, kg_result, framework_result, regex_findings)
        
        # 5. Save Combined Report
        if output_dir:
            await self._save_comprehensive_report(combined_result, file_path, output_dir)
        
        return combined_result
    
    def _combine_results(self, file_path: str, kg_result: Dict[str, Any], 
                        framework_result: Any, regex_findings: List[SuspiciousPattern]) -> ComprehensiveResult:
        """Combine results from all detection methods"""
        
        # Extract data from results
        kg_confidence = kg_result.get('validation_summary', {}).get('overall_confidence', 0.0)
        kg_hallucinations = kg_result.get('hallucinations_detected', [])
        kg_valid = len(kg_hallucinations) == 0
        
        framework_confidence = framework_result.confidence
        framework_issues = framework_result.issues
        framework_valid = not framework_result.is_hallucination
        
        # Analyze regex findings
        manual_review_count = sum(1 for f in regex_findings if f.manual_review_required)
        critical_patterns = sum(1 for f in regex_findings if f.suspicion_level.value == 'critical')
        
        # Calculate overall confidence (weighted)
        overall_confidence = (
            kg_confidence * 0.5 +  # Knowledge graph gets highest weight
            framework_confidence * 0.3 +  # Framework analysis
            max(0, 1.0 - (len(regex_findings) * 0.1)) * 0.2  # Regex findings (penalty-based)
        )
        
        # Determine if manual review is needed
        needs_manual_review = (
            manual_review_count > 0 or 
            overall_confidence < 0.8 or 
            critical_patterns > 0 or
            not kg_valid or
            not framework_valid
        )
        
        # Determine risk level
        risk_level = self._calculate_risk_level(
            kg_valid, framework_valid, len(regex_findings), critical_patterns, overall_confidence
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            kg_result, framework_result, regex_findings, overall_confidence
        )
        
        return ComprehensiveResult(
            filename=file_path,
            timestamp=datetime.now().isoformat(),
            kg_confidence=kg_confidence,
            kg_hallucinations=kg_hallucinations,
            kg_valid=kg_valid,
            framework_confidence=framework_confidence,
            framework_issues=framework_issues,
            framework_valid=framework_valid,
            regex_findings=regex_findings,
            manual_review_count=manual_review_count,
            critical_patterns=critical_patterns,
            overall_confidence=overall_confidence,
            needs_manual_review=needs_manual_review,
            risk_level=risk_level,
            recommendations=recommendations
        )
    
    def _calculate_risk_level(self, kg_valid: bool, framework_valid: bool, 
                            regex_count: int, critical_count: int, confidence: float) -> str:
        """Calculate overall risk level"""
        if critical_count > 0 or not kg_valid or confidence < 0.5:
            return "CRITICAL"
        elif not framework_valid or regex_count > 5 or confidence < 0.7:
            return "HIGH"
        elif regex_count > 2 or confidence < 0.9:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_recommendations(self, kg_result: Dict[str, Any], framework_result: Any,
                                regex_findings: List[SuspiciousPattern], confidence: float) -> List[str]:
        """Generate comprehensive recommendations"""
        recommendations = []
        
        # Knowledge graph recommendations
        if kg_result.get('recommendations'):
            recommendations.extend(kg_result['recommendations'])
        
        # Framework recommendations
        if framework_result.suggestions:
            recommendations.extend(framework_result.suggestions)
        
        # Regex-specific recommendations
        if regex_findings:
            recommendations.append(f"Found {len(regex_findings)} suspicious patterns requiring review")
            
            critical_findings = [f for f in regex_findings if f.suspicion_level.value == 'critical']
            if critical_findings:
                recommendations.append(f"URGENT: {len(critical_findings)} critical patterns found - review immediately")
            
            # Add specific suggestions from regex findings
            for finding in regex_findings[:3]:  # Top 3 findings
                if finding.suggestions:
                    recommendations.append(f"Line {finding.line_number}: {finding.suggestions[0]}")
        
        # Confidence-based recommendations
        if confidence < 0.7:
            recommendations.append("Low confidence score - recommend thorough manual review")
        elif confidence < 0.9:
            recommendations.append("Moderate confidence - spot-check suspicious patterns")
        
        return recommendations
    
    async def _save_comprehensive_report(self, result: ComprehensiveResult, 
                                       file_path: str, output_dir: str):
        """Save comprehensive report"""
        Path(output_dir).mkdir(exist_ok=True)
        
        filename = Path(file_path).stem
        
        # Save detailed JSON report
        json_path = Path(output_dir) / f"{filename}_comprehensive_report.json"
        report_data = {
            "filename": result.filename,
            "timestamp": result.timestamp,
            "overall_assessment": {
                "confidence": result.overall_confidence,
                "needs_manual_review": result.needs_manual_review,
                "risk_level": result.risk_level,
                "recommendations": result.recommendations
            },
            "knowledge_graph_analysis": {
                "confidence": result.kg_confidence,
                "valid": result.kg_valid,
                "hallucinations": result.kg_hallucinations
            },
            "framework_analysis": {
                "confidence": result.framework_confidence,
                "valid": result.framework_valid,
                "issues": result.framework_issues
            },
            "regex_analysis": {
                "total_findings": len(result.regex_findings),
                "manual_review_required": result.manual_review_count,
                "critical_patterns": result.critical_patterns,
                "findings": [self._finding_to_dict(f) for f in result.regex_findings]
            }
        }
        
        with open(json_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Save markdown report
        md_path = Path(output_dir) / f"{filename}_comprehensive_report.md"
        md_content = self._generate_markdown_report(result)
        with open(md_path, 'w') as f:
            f.write(md_content)
        
        logger.info(f"Comprehensive reports saved to {output_dir}")
    
    def _finding_to_dict(self, finding: SuspiciousPattern) -> Dict[str, Any]:
        """Convert finding to dictionary"""
        return {
            "pattern_type": finding.pattern_type,
            "line_number": finding.line_number,
            "matched_text": finding.matched_text,
            "suspicion_level": finding.suspicion_level.value,
            "reason": finding.reason,
            "manual_review_required": finding.manual_review_required,
            "suggestions": finding.suggestions
        }
    
    def _generate_markdown_report(self, result: ComprehensiveResult) -> str:
        """Generate markdown report"""
        risk_emoji = {
            "CRITICAL": "🔴",
            "HIGH": "🟠", 
            "MEDIUM": "🟡",
            "LOW": "🟢"
        }
        
        md = [
            "# Comprehensive Hallucination Detection Report",
            "",
            f"**File:** `{result.filename}`",
            f"**Analysis Date:** {result.timestamp}",
            f"**Risk Level:** {risk_emoji.get(result.risk_level, '⚪')} {result.risk_level}",
            f"**Overall Confidence:** {result.overall_confidence:.1%}",
            f"**Manual Review Required:** {'✅ YES' if result.needs_manual_review else '❌ NO'}",
            "",
            "## Executive Summary",
            "",
            f"- **Knowledge Graph Confidence:** {result.kg_confidence:.1%}",
            f"- **Framework Confidence:** {result.framework_confidence:.1%}",
            f"- **Regex Findings:** {len(result.regex_findings)} patterns detected",
            f"- **Critical Patterns:** {result.critical_patterns}",
            f"- **Manual Review Items:** {result.manual_review_count}",
            "",
        ]
        
        # Recommendations
        if result.recommendations:
            md.extend([
                "## 🎯 Recommendations",
                "",
            ])
            for rec in result.recommendations:
                md.append(f"- {rec}")
            md.append("")
        
        # Knowledge Graph Results
        md.extend([
            "## 📊 Knowledge Graph Analysis",
            "",
            f"**Confidence:** {result.kg_confidence:.1%}",
            f"**Valid:** {'✅' if result.kg_valid else '❌'}",
            f"**Hallucinations Found:** {len(result.kg_hallucinations)}",
            "",
        ])
        
        # Framework Results
        md.extend([
            "## 🔧 Framework Analysis",
            "",
            f"**Confidence:** {result.framework_confidence:.1%}",
            f"**Valid:** {'✅' if result.framework_valid else '❌'}",
            f"**Issues Found:** {len(result.framework_issues)}",
            "",
        ])
        
        # Regex Results
        md.extend([
            "## 🔍 Regex Pattern Analysis",
            "",
            f"**Total Patterns:** {len(result.regex_findings)}",
            f"**Manual Review Required:** {result.manual_review_count}",
            f"**Critical Patterns:** {result.critical_patterns}",
            "",
        ])
        
        # Manual Review Items
        if result.needs_manual_review:
            md.extend([
                "## ⚠️ Manual Review Required",
                "",
            ])
            
            manual_items = [f for f in result.regex_findings if f.manual_review_required]
            for i, item in enumerate(manual_items[:10], 1):  # Top 10
                md.extend([
                    f"### {i}. {item.pattern_type.replace('_', ' ').title()} (Line {item.line_number})",
                    f"**Found:** `{item.matched_text}`",
                    f"**Reason:** {item.reason}",
                    f"**Suspicion Level:** {item.suspicion_level.value.upper()}",
                    ""
                ])
                if item.suggestions:
                    md.append(f"**Suggestions:**")
                    for suggestion in item.suggestions:
                        md.append(f"- {suggestion}")
                    md.append("")
        
        return "\n".join(md)
    
    def print_summary(self, result: ComprehensiveResult):
        """Print summary of results"""
        risk_emoji = {
            "CRITICAL": "🔴",
            "HIGH": "🟠", 
            "MEDIUM": "🟡",
            "LOW": "🟢"
        }
        
        print(f"\n{'='*70}")
        print("🚀 COMPREHENSIVE HALLUCINATION DETECTION RESULTS")
        print(f"{'='*70}")
        print(f"File: {result.filename}")
        print(f"Risk Level: {risk_emoji.get(result.risk_level, '⚪')} {result.risk_level}")
        print(f"Overall Confidence: {result.overall_confidence:.1%}")
        print(f"Manual Review Required: {'✅ YES' if result.needs_manual_review else '❌ NO'}")
        print(f"")
        print(f"Detection Results:")
        print(f"  📊 Knowledge Graph: {result.kg_confidence:.1%} confidence")
        print(f"  🔧 Framework: {result.framework_confidence:.1%} confidence")
        print(f"  🔍 Regex: {len(result.regex_findings)} patterns ({result.critical_patterns} critical)")
        
        if result.needs_manual_review:
            print(f"\n⚠️  MANUAL REVIEW REQUIRED!")
            print(f"  • {result.manual_review_count} items need review")
            print(f"  • {result.critical_patterns} critical patterns found")
        
        print(f"{'='*70}")
    
    async def close(self):
        """Close all connections"""
        await self.kg_detector.close()

# CLI interface
async def main():
    import argparse
    from dotenv import load_dotenv
    import os
    
    parser = argparse.ArgumentParser(description="Comprehensive Hallucination Detection")
    parser.add_argument("file", help="Python file to analyze")
    parser.add_argument("--output-dir", help="Output directory for reports")
    parser.add_argument("--neo4j-uri", help="Neo4j URI")
    parser.add_argument("--neo4j-user", help="Neo4j username")
    parser.add_argument("--neo4j-password", help="Neo4j password")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    
    load_dotenv()
    
    neo4j_uri = args.neo4j_uri or os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user = args.neo4j_user or os.getenv('NEO4J_USER', 'neo4j')
    neo4j_password = args.neo4j_password or os.getenv('NEO4J_PASSWORD', 'no_auth')
    
    detector = ComprehensiveHallucinationDetector(neo4j_uri, neo4j_user, neo4j_password)
    
    try:
        await detector.initialize()
        result = await detector.analyze_file(args.file, args.output_dir)
        detector.print_summary(result)
        
    except Exception as e:
        print(f"Error analyzing {args.file}: {e}")
        return 1
    finally:
        await detector.close()
    
    return 0

if __name__ == "__main__":
    exit(asyncio.run(main()))