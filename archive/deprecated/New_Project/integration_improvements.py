#!/usr/bin/env python3
"""
Integration Improvements for Existing Hallucination Detection System

This script adds several enhancements to the existing knowledge_graphs/ hallucination detection:
1. Real-time validation during code generation
2. Confidence threshold tuning
3. Custom validation rules
4. Performance optimizations
5. Enhanced reporting with visualizations
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import matplotlib.pyplot as plt
import seaborn as sns

# Import existing components
from .ai_hallucination_detector import AIHallucinationDetector
from .hallucination_reporter import HallucinationReporter
from .knowledge_graph_validator import ScriptValidationResult, ValidationStatus

logger = logging.getLogger(__name__)


@dataclass
class ValidationRule:
    """Custom validation rule"""

    name: str
    description: str
    validator: Callable[[str, Dict[str, Any]], Dict[str, Any]]
    severity: str = "medium"
    enabled: bool = True


class RealTimeValidator:
    """Real-time validation during code generation"""

    def __init__(self, detector: AIHallucinationDetector):
        self.detector = detector
        self.validation_cache = {}
        self.performance_metrics = {
            "validation_count": 0,
            "cache_hits": 0,
            "avg_validation_time": 0.0,
        }

    async def validate_code_snippet(
        self, code: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate a code snippet in real-time"""
        import hashlib
        import time

        start_time = time.time()

        # Create cache key
        cache_key = hashlib.md5(code.encode()).hexdigest()

        # Check cache
        if cache_key in self.validation_cache:
            self.performance_metrics["cache_hits"] += 1
            return self.validation_cache[cache_key]

        # Create temporary file for validation
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            # Run validation
            result = await self.detector.detect_hallucinations(
                temp_path, save_json=False, save_markdown=False, print_summary=False
            )

            # Cache result
            self.validation_cache[cache_key] = result

            # Update metrics
            self.performance_metrics["validation_count"] += 1
            validation_time = time.time() - start_time
            self.performance_metrics["avg_validation_time"] = (
                self.performance_metrics["avg_validation_time"]
                * (self.performance_metrics["validation_count"] - 1)
                + validation_time
            ) / self.performance_metrics["validation_count"]

            return result

        finally:
            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)


class ConfidenceThresholdTuner:
    """Automatically tune confidence thresholds based on validation history"""

    def __init__(self):
        self.validation_history = []
        self.threshold_config = {
            "high_confidence": 0.9,
            "medium_confidence": 0.7,
            "low_confidence": 0.5,
        }

    def add_validation_result(self, result: Dict[str, Any], ground_truth: bool):
        """Add validation result with ground truth for learning"""
        self.validation_history.append(
            {
                "confidence": result.get("validation_summary", {}).get(
                    "overall_confidence", 0.0
                ),
                "predicted_hallucination": len(
                    result.get("hallucinations_detected", [])
                )
                > 0,
                "actual_hallucination": ground_truth,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def optimize_thresholds(self) -> Dict[str, float]:
        """Optimize confidence thresholds based on validation history"""
        if len(self.validation_history) < 10:
            return self.threshold_config

        # Simple optimization: find threshold that maximizes F1 score
        best_threshold = 0.7
        best_f1 = 0.0

        for threshold in [0.5, 0.6, 0.7, 0.8, 0.9]:
            tp = fp = tn = fn = 0

            for record in self.validation_history:
                predicted = (
                    record["confidence"] < threshold
                )  # Lower confidence = predicted hallucination
                actual = record["actual_hallucination"]

                if predicted and actual:
                    tp += 1
                elif predicted and not actual:
                    fp += 1
                elif not predicted and not actual:
                    tn += 1
                else:
                    fn += 1

            if tp + fp > 0 and tp + fn > 0:
                precision = tp / (tp + fp)
                recall = tp / (tp + fn)
                f1 = (
                    2 * precision * recall / (precision + recall)
                    if (precision + recall) > 0
                    else 0
                )

                if f1 > best_f1:
                    best_f1 = f1
                    best_threshold = threshold

        self.threshold_config["medium_confidence"] = best_threshold
        return self.threshold_config


class CustomValidationRules:
    """Custom validation rules for domain-specific checks"""

    def __init__(self):
        self.rules = [
            ValidationRule(
                name="security_check",
                description="Check for potential security issues",
                validator=self._validate_security,
                severity="high",
            ),
            ValidationRule(
                name="performance_check",
                description="Check for performance anti-patterns",
                validator=self._validate_performance,
                severity="medium",
            ),
            ValidationRule(
                name="style_check",
                description="Check for style violations",
                validator=self._validate_style,
                severity="low",
            ),
            ValidationRule(
                name="ai_specific_check",
                description="Check for AI-specific hallucination patterns",
                validator=self._validate_ai_patterns,
                severity="high",
            ),
        ]

    def _validate_security(self, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate security concerns"""
        issues = []

        security_patterns = [
            ("eval(", "Use of eval() is dangerous"),
            ("exec(", "Use of exec() is dangerous"),
            ("__import__", "Dynamic imports can be risky"),
            ("os.system(", "Direct system calls are dangerous"),
            ("subprocess.call(", "Subprocess calls need validation"),
        ]

        for pattern, message in security_patterns:
            if pattern in code:
                issues.append(
                    {
                        "type": "security_issue",
                        "message": message,
                        "pattern": pattern,
                        "severity": "high",
                    }
                )

        return {"valid": len(issues) == 0, "issues": issues}

    def _validate_performance(
        self, code: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate performance concerns"""
        issues = []

        # Check for common performance issues
        if "for" in code and "append(" in code and "list" in code:
            issues.append(
                {
                    "type": "performance_issue",
                    "message": "Consider using list comprehension instead of append in loop",
                    "severity": "medium",
                }
            )

        if code.count("import ") > 10:
            issues.append(
                {
                    "type": "performance_issue",
                    "message": "Too many imports may affect startup time",
                    "severity": "low",
                }
            )

        return {"valid": len(issues) == 0, "issues": issues}

    def _validate_style(self, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate style concerns"""
        issues = []

        # Check for style issues
        if (
            "lambda" in code
            and len([line for line in code.split("\n") if "lambda" in line]) > 3
        ):
            issues.append(
                {
                    "type": "style_issue",
                    "message": "Consider using regular functions instead of multiple lambdas",
                    "severity": "low",
                }
            )

        return {"valid": len(issues) == 0, "issues": issues}

    def _validate_ai_patterns(
        self, code: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate AI-specific hallucination patterns"""
        issues = []

        # Common AI hallucination patterns
        ai_patterns = [
            # Fake methods that AIs often generate
            (".auto_", 'AI-generated "auto_" methods are often hallucinated'),
            (".smart_", 'AI-generated "smart_" methods are often hallucinated'),
            (".enhanced_", 'AI-generated "enhanced_" methods are often hallucinated'),
            (".super_", 'AI-generated "super_" methods are often hallucinated'),
            (".magic_", 'AI-generated "magic_" methods are often hallucinated'),
            # Fake parameters
            ("auto_retry=", "auto_retry parameter is often hallucinated"),
            ("smart_mode=", "smart_mode parameter is often hallucinated"),
            ("enhanced_features=", "enhanced_features parameter is often hallucinated"),
        ]

        for pattern, message in ai_patterns:
            if pattern in code:
                issues.append(
                    {
                        "type": "ai_hallucination_pattern",
                        "message": message,
                        "pattern": pattern,
                        "severity": "high",
                    }
                )

        return {"valid": len(issues) == 0, "issues": issues}

    async def validate_all_rules(
        self, code: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run all enabled validation rules"""
        all_issues = []
        rule_results = {}

        for rule in self.rules:
            if rule.enabled:
                try:
                    result = rule.validator(code, context)
                    rule_results[rule.name] = result

                    # Add rule info to issues
                    for issue in result.get("issues", []):
                        issue["rule"] = rule.name
                        issue["rule_description"] = rule.description
                        all_issues.append(issue)

                except Exception as e:
                    logger.error(f"Rule {rule.name} failed: {e}")
                    rule_results[rule.name] = {
                        "valid": False,
                        "issues": [{"type": "rule_error", "message": str(e)}],
                    }

        return {
            "valid": len(all_issues) == 0,
            "issues": all_issues,
            "rule_results": rule_results,
        }


class EnhancedReporter(HallucinationReporter):
    """Enhanced reporter with visualizations and advanced analysis"""

    def generate_visual_report(self, result: Dict[str, Any], output_dir: str):
        """Generate visual report with charts and graphs"""

        # Create visualization directory
        viz_dir = Path(output_dir) / "visualizations"
        viz_dir.mkdir(exist_ok=True)

        # Generate confidence distribution chart
        self._generate_confidence_chart(result, viz_dir)

        # Generate issue breakdown chart
        self._generate_issue_breakdown(result, viz_dir)

        # Generate validation timeline
        self._generate_validation_timeline(result, viz_dir)

        logger.info(f"Visual reports generated in {viz_dir}")

    def _generate_confidence_chart(self, result: Dict[str, Any], viz_dir: Path):
        """Generate confidence distribution chart"""
        plt.figure(figsize=(10, 6))

        # Extract confidence data
        validation_details = result.get("validation_details", {})

        confidences = []
        statuses = []

        for category in [
            "valid_items",
            "invalid_items",
            "uncertain_items",
            "not_found_items",
        ]:
            items = validation_details.get(category, [])
            for item in items:
                confidences.append(item.get("confidence", 0.0))
                statuses.append(category.replace("_items", ""))

        if confidences:
            # Create confidence distribution
            plt.hist(confidences, bins=20, alpha=0.7, edgecolor="black")
            plt.xlabel("Confidence Score")
            plt.ylabel("Frequency")
            plt.title("Confidence Score Distribution")
            plt.grid(True, alpha=0.3)

            # Add overall confidence line
            overall_conf = result.get("validation_summary", {}).get(
                "overall_confidence", 0.0
            )
            plt.axvline(
                overall_conf,
                color="red",
                linestyle="--",
                label=f"Overall Confidence: {overall_conf:.1%}",
            )
            plt.legend()

            plt.tight_layout()
            plt.savefig(
                viz_dir / "confidence_distribution.png", dpi=300, bbox_inches="tight"
            )
            plt.close()

    def _generate_issue_breakdown(self, result: Dict[str, Any], viz_dir: Path):
        """Generate issue breakdown chart"""
        plt.figure(figsize=(12, 8))

        # Count issues by type
        issue_counts = {}
        validation_details = result.get("validation_details", {})

        for category in ["invalid_items", "uncertain_items", "not_found_items"]:
            items = validation_details.get(category, [])
            for item in items:
                issue_type = item.get("type", "unknown")
                issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1

        if issue_counts:
            # Create bar chart
            types = list(issue_counts.keys())
            counts = list(issue_counts.values())

            bars = plt.bar(
                types,
                counts,
                color=["red", "orange", "yellow", "lightcoral", "darkred"][
                    : len(types)
                ],
            )
            plt.xlabel("Issue Type")
            plt.ylabel("Count")
            plt.title("Issue Breakdown by Type")
            plt.xticks(rotation=45, ha="right")

            # Add value labels on bars
            for bar, count in zip(bars, counts):
                plt.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.1,
                    str(count),
                    ha="center",
                    va="bottom",
                )

            plt.tight_layout()
            plt.savefig(viz_dir / "issue_breakdown.png", dpi=300, bbox_inches="tight")
            plt.close()

    def _generate_validation_timeline(self, result: Dict[str, Any], viz_dir: Path):
        """Generate validation timeline (placeholder for multiple validations)"""
        plt.figure(figsize=(12, 6))

        # For now, just show overall confidence over time
        # In a real implementation, this would show confidence trends
        times = ["Analysis Start", "AST Parsing", "KG Validation", "Report Generation"]
        confidence_trend = [
            0.0,
            0.3,
            0.8,
            result.get("validation_summary", {}).get("overall_confidence", 0.0),
        ]

        plt.plot(times, confidence_trend, marker="o", linewidth=2, markersize=8)
        plt.xlabel("Validation Stage")
        plt.ylabel("Confidence Score")
        plt.title("Validation Confidence Timeline")
        plt.ylim(0, 1)
        plt.grid(True, alpha=0.3)

        # Add confidence threshold lines
        plt.axhline(
            0.7, color="green", linestyle="--", alpha=0.5, label="High Confidence"
        )
        plt.axhline(
            0.5, color="orange", linestyle="--", alpha=0.5, label="Medium Confidence"
        )
        plt.axhline(0.3, color="red", linestyle="--", alpha=0.5, label="Low Confidence")
        plt.legend()

        plt.tight_layout()
        plt.savefig(viz_dir / "validation_timeline.png", dpi=300, bbox_inches="tight")
        plt.close()


class IntegratedHallucinationDetector:
    """Integrated detector with all improvements"""

    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        self.base_detector = AIHallucinationDetector(
            neo4j_uri, neo4j_user, neo4j_password
        )
        self.realtime_validator = RealTimeValidator(self.base_detector)
        self.threshold_tuner = ConfidenceThresholdTuner()
        self.custom_rules = CustomValidationRules()
        self.enhanced_reporter = EnhancedReporter()

    async def initialize(self):
        """Initialize all components"""
        await self.base_detector.initialize()
        logger.info("Integrated hallucination detector initialized")

    async def detect_with_all_improvements(
        self,
        script_path: str,
        output_dir: Optional[str] = None,
        include_visuals: bool = True,
    ) -> Dict[str, Any]:
        """Run detection with all improvements"""

        # Step 1: Base detection
        base_result = await self.base_detector.detect_hallucinations(
            script_path,
            output_dir,
            save_json=False,
            save_markdown=False,
            print_summary=False,
        )

        # Step 2: Custom rules validation
        with open(script_path, "r") as f:
            code = f.read()

        context = {"script_path": script_path}
        custom_rules_result = await self.custom_rules.validate_all_rules(code, context)

        # Step 3: Combine results
        combined_result = {
            "base_analysis": base_result,
            "custom_rules": custom_rules_result,
            "performance_metrics": self.realtime_validator.performance_metrics,
            "threshold_config": self.threshold_tuner.threshold_config,
        }

        # Step 4: Enhanced reporting
        if output_dir:
            # Save enhanced JSON report
            script_name = Path(script_path).stem
            json_path = Path(output_dir) / f"{script_name}_integrated_report.json"
            with open(json_path, "w") as f:
                json.dump(combined_result, f, indent=2, default=str)

            # Generate visual reports
            if include_visuals:
                self.enhanced_reporter.generate_visual_report(base_result, output_dir)

        return combined_result

    async def close(self):
        """Close all connections"""
        await self.base_detector.close()


# Example usage and CLI
async def main():
    """Example usage of integrated detector"""
    import argparse
    import os

    from dotenv import load_dotenv

    parser = argparse.ArgumentParser(description="Integrated Hallucination Detector")
    parser.add_argument("script", help="Python script to analyze")
    parser.add_argument("--output-dir", help="Output directory for reports")
    parser.add_argument(
        "--no-visuals", action="store_true", help="Skip visual report generation"
    )
    args = parser.parse_args()

    load_dotenv()

    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "no_auth")

    detector = IntegratedHallucinationDetector(neo4j_uri, neo4j_user, neo4j_password)

    try:
        await detector.initialize()
        result = await detector.detect_with_all_improvements(
            args.script, args.output_dir, include_visuals=not args.no_visuals
        )

        # Print summary
        print(f"\n{'='*60}")
        print("🚀 INTEGRATED HALLUCINATION DETECTION RESULTS")
        print(f"{'='*60}")
        print(f"Script: {args.script}")

        base_confidence = result["base_analysis"]["validation_summary"][
            "overall_confidence"
        ]
        custom_issues = len(result["custom_rules"]["issues"])

        print(f"Base Confidence: {base_confidence:.1%}")
        print(f"Custom Rule Issues: {custom_issues}")
        print(
            f"Cache Hit Rate: {result['performance_metrics']['cache_hits']}/{result['performance_metrics']['validation_count']}"
        )
        print(f"{'='*60}")

    finally:
        await detector.close()


if __name__ == "__main__":
    asyncio.run(main())
