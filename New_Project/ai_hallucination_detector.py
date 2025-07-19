# FILE: ai_hallucination_detector.py
# TAGS: [orchestrator, main-detector, hallucination-analysis, neo4j-integration]
# PURPOSE: Main orchestrator for detecting AI coding assistant hallucinations in Python scripts
# INTEGRATES: AST analysis, knowledge graph validation, and comprehensive reporting

"""
AI Hallucination Detector

Main orchestrator for detecting AI coding assistant hallucinations in Python scripts.
Combines AST analysis, knowledge graph validation, and comprehensive reporting.
"""

import argparse  # Command-line argument parsing

# DEPENDENCY IMPORTS
# TAGS: [imports, dependencies, core-modules]
# PURPOSE: Import core Python modules and external dependencies
import asyncio  # Async runtime for concurrent operations
import logging  # Logging infrastructure
import os  # Operating system interface
import sys  # System-specific parameters and functions
from pathlib import Path  # Object-oriented filesystem paths
from typing import List, Optional  # Type hints for better code clarity

# EXTERNAL DEPENDENCIES
# TAGS: [external-deps, config-management]
from dotenv import load_dotenv  # Environment variable management

# INTERNAL MODULE IMPORTS
# TAGS: [internal-modules, component-integration]
# PURPOSE: Import custom modules for analysis pipeline
from .ai_script_analyzer import (  # AST analysis components
    AIScriptAnalyzer,
    analyze_ai_script,
)
from .hallucination_reporter import HallucinationReporter  # Report generation
from .knowledge_graph_validator import KnowledgeGraphValidator  # Neo4j validation logic

# LOGGING CONFIGURATION
# TAGS: [logging, configuration, observability]
# PURPOSE: Set up structured logging for debugging and monitoring
logging.basicConfig(
    level=logging.INFO,  # Set default log level to INFO
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Structured log format
    datefmt="%Y-%m-%d %H:%M:%S",  # ISO timestamp format
)

# REGEX INTEGRATION PATCH
sys.path.append(str(Path(__file__).parent.parent))
from regex_hallucination_detector import RegexHallucinationDetector

logger = logging.getLogger(__name__)  # Create module-specific logger


# MAIN DETECTOR CLASS
# TAGS: [main-class, orchestrator, dependency-injection]
# PURPOSE: Central orchestrator that coordinates all hallucination detection components
class AIHallucinationDetector:
    """Main detector class that orchestrates the entire process"""

    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        # COMPONENT INITIALIZATION
        # TAGS: [dependency-injection, component-setup]
        # PURPOSE: Initialize all required components for detection pipeline
        self.validator = KnowledgeGraphValidator(
            neo4j_uri, neo4j_user, neo4j_password
        )  # Neo4j validation component
        self.reporter = HallucinationReporter()  # Report generation component
        self.analyzer = AIScriptAnalyzer()  # AST analysis component
        # REGEX INTEGRATION PATCH
        self.regex_detector = RegexHallucinationDetector()

    # ASYNC INITIALIZATION METHOD
    # TAGS: [async-init, connection-setup, lifecycle]
    # PURPOSE: Initialize async components and database connections
    async def initialize(self):
        """Initialize connections and components"""
        await self.validator.initialize()  # Initialize Neo4j database connection
        logger.info(
            "AI Hallucination Detector initialized successfully"
        )  # Log successful initialization

    # CLEANUP METHOD
    # TAGS: [cleanup, connection-close, lifecycle]
    # PURPOSE: Properly close database connections and cleanup resources
    async def close(self):
        """Close connections"""
        await self.validator.close()  # Close Neo4j database connection

    # MAIN DETECTION METHOD
    # TAGS: [main-detection, pipeline, async-processing]
    # PURPOSE: Orchestrate the complete hallucination detection pipeline
    async def detect_hallucinations(
        self,
        script_path: str,
        output_dir: Optional[str] = None,
        save_json: bool = True,
        save_markdown: bool = True,
        print_summary: bool = True,
    ) -> dict:
        """
        Main detection function that analyzes a script and generates reports

        Args:
            script_path: Path to the AI-generated Python script
            output_dir: Directory to save reports (defaults to script directory)
            save_json: Whether to save JSON report
            save_markdown: Whether to save Markdown report
            print_summary: Whether to print summary to console

        Returns:
            Complete validation report as dictionary
        """
        # DETECTION PIPELINE INITIALIZATION
        # TAGS: [pipeline-start, input-validation, logging]
        logger.info(f"Starting hallucination detection for: {script_path}")

        # INPUT VALIDATION
        # TAGS: [validation, error-handling, file-system]
        # PURPOSE: Validate input file exists and is a Python script
        if not os.path.exists(script_path):
            raise FileNotFoundError(
                f"Script not found: {script_path}"
            )  # File existence check

        if not script_path.endswith(".py"):
            raise ValueError(
                "Only Python (.py) files are supported"
            )  # Python file validation

        # OUTPUT DIRECTORY SETUP
        # TAGS: [output-setup, directory-creation, file-system]
        # PURPOSE: Ensure output directory exists for saving reports
        if output_dir is None:
            output_dir = str(Path(script_path).parent)  # Default to script directory

        os.makedirs(output_dir, exist_ok=True)  # Create output directory if needed

        try:
            # STEP 1: AST ANALYSIS
            # TAGS: [ast-analysis, step-1, script-parsing]
            # PURPOSE: Parse Python script using AST to extract code elements
            logger.info("Step 1: Analyzing script structure...")
            analysis_result = self.analyzer.analyze_script(
                script_path
            )  # Run AST analysis

            # ERROR HANDLING FOR ANALYSIS
            # TAGS: [error-handling, analysis-warnings]
            if analysis_result.errors:
                logger.warning(
                    f"Analysis warnings: {analysis_result.errors}"
                )  # Log any analysis issues

            # ANALYSIS RESULTS LOGGING
            # TAGS: [logging, metrics, analysis-summary]
            # PURPOSE: Log summary of extracted code elements
            logger.info(
                f"Found: {len(analysis_result.imports)} imports, "
                f"{len(analysis_result.class_instantiations)} class instantiations, "
                f"{len(analysis_result.method_calls)} method calls, "
                f"{len(analysis_result.function_calls)} function calls, "
                f"{len(analysis_result.attribute_accesses)} attribute accesses"
            )

            # STEP 2: KNOWLEDGE GRAPH VALIDATION
            # TAGS: [validation, step-2, neo4j-query, knowledge-graph]
            # PURPOSE: Validate extracted code elements against Neo4j knowledge graph

            # REGEX INTEGRATION PATCH - Add pattern detection
            logger.info("Step 2.5: Running regex pattern analysis...")
            with open(script_path, "r") as f:
                script_code = f.read()
            regex_findings = self.regex_detector.analyze_code(script_code, script_path)
            logger.info(f"Found {len(regex_findings)} suspicious patterns")

            logger.info("Step 2: Validating against knowledge graph...")
            validation_result = await self.validator.validate_script(
                analysis_result
            )  # Run async validation

            # VALIDATION RESULTS LOGGING
            # TAGS: [logging, validation-metrics, confidence-scoring]
            logger.info(
                f"Validation complete. Overall confidence: {validation_result.overall_confidence:.1%}"
            )

            # STEP 3: REPORT GENERATION
            # TAGS: [reporting, step-3, comprehensive-analysis]
            # PURPOSE: Generate detailed report from validation results
            logger.info("Step 3: Generating reports...")
            report = self.reporter.generate_comprehensive_report(
                validation_result
            )  # Generate comprehensive report

            # REGEX INTEGRATION PATCH - Add regex findings to report
            report["regex_analysis"] = {
                "total_patterns": len(regex_findings),
                "manual_review_required": sum(
                    1 for f in regex_findings if f.manual_review_required
                ),
                "critical_patterns": sum(
                    1 for f in regex_findings if f.suspicion_level.value == "critical"
                ),
                "findings": [
                    {
                        "pattern_type": f.pattern_type,
                        "line_number": f.line_number,
                        "matched_text": f.matched_text,
                        "suspicion_level": f.suspicion_level.value,
                        "reason": f.reason,
                        "manual_review_required": f.manual_review_required,
                        "suggestions": f.suggestions,
                    }
                    for f in regex_findings
                ],
            }

            # STEP 4: REPORT PERSISTENCE
            # TAGS: [file-output, step-4, report-saving]
            # PURPOSE: Save generated reports to filesystem in multiple formats
            script_name = Path(script_path).stem  # Extract filename without extension

            # JSON REPORT SAVING
            # TAGS: [json-output, structured-data]
            if save_json:
                json_path = os.path.join(
                    output_dir, f"{script_name}_hallucination_report.json"
                )
                self.reporter.save_json_report(
                    report, json_path
                )  # Save structured JSON report

            # MARKDOWN REPORT SAVING
            # TAGS: [markdown-output, human-readable]
            if save_markdown:
                md_path = os.path.join(
                    output_dir, f"{script_name}_hallucination_report.md"
                )
                self.reporter.save_markdown_report(
                    report, md_path
                )  # Save human-readable markdown report

            # STEP 5: CONSOLE OUTPUT
            # TAGS: [console-output, step-5, summary-display]
            # PURPOSE: Display summary results to console if requested
            if print_summary:
                self.reporter.print_summary(report)  # Print summary to console

            # COMPLETION LOGGING
            # TAGS: [completion, success-logging]
            logger.info("Hallucination detection completed successfully")
            return report  # Return complete report dictionary

        # EXCEPTION HANDLING
        # TAGS: [error-handling, exception-management, logging]
        # PURPOSE: Handle and log any errors during the detection process
        except Exception as e:
            logger.error(
                f"Error during hallucination detection: {str(e)}"
            )  # Log error details
            raise  # Re-raise exception for caller handling

    # BATCH PROCESSING METHOD
    # TAGS: [batch-processing, multiple-scripts, async-processing]
    # PURPOSE: Process multiple Python scripts in batch for hallucination detection
    async def batch_detect(
        self, script_paths: List[str], output_dir: Optional[str] = None
    ) -> List[dict]:
        """
        Detect hallucinations in multiple scripts

        Args:
            script_paths: List of paths to Python scripts
            output_dir: Directory to save all reports

        Returns:
            List of validation reports
        """
        # BATCH PROCESSING INITIALIZATION
        # TAGS: [batch-init, logging, metrics]
        logger.info(f"Starting batch detection for {len(script_paths)} scripts")

        # BATCH PROCESSING LOOP
        # TAGS: [batch-loop, iteration, error-resilience]
        # PURPOSE: Process each script individually with error resilience
        results = []  # Collect results from all scripts
        for i, script_path in enumerate(script_paths, 1):
            logger.info(
                f"Processing script {i}/{len(script_paths)}: {script_path}"
            )  # Progress logging

            # INDIVIDUAL SCRIPT PROCESSING
            # TAGS: [script-processing, error-handling, resilience]
            try:
                result = await self.detect_hallucinations(
                    script_path=script_path,
                    output_dir=output_dir,
                    print_summary=False,  # Don't print individual summaries in batch mode
                )
                results.append(result)  # Add successful result to collection

            except Exception as e:
                logger.error(
                    f"Failed to process {script_path}: {str(e)}"
                )  # Log individual failures
                # Continue with other scripts
                continue  # Skip failed script and continue with others

        # BATCH COMPLETION
        # TAGS: [batch-completion, summary-display]
        # PURPOSE: Display aggregate results from all processed scripts
        self._print_batch_summary(results)  # Print consolidated batch summary

        return results  # Return all collected results

    # BATCH SUMMARY DISPLAY METHOD
    # TAGS: [batch-summary, console-output, metrics-aggregation]
    # PURPOSE: Display aggregated metrics from batch processing results
    def _print_batch_summary(self, results: List[dict]):
        """Print summary of batch processing results"""
        # EMPTY RESULTS HANDLING
        # TAGS: [error-handling, empty-results]
        if not results:
            print(
                "No scripts were successfully processed."
            )  # Handle case of no successful processing
            return

        # SUMMARY HEADER DISPLAY
        # TAGS: [console-formatting, header-display]
        print("\n" + "=" * 80)
        print("🚀 BATCH HALLUCINATION DETECTION SUMMARY")
        print("=" * 80)

        # METRICS AGGREGATION
        # TAGS: [metrics-calculation, aggregation, statistics]
        # PURPOSE: Calculate aggregate statistics from all batch results
        total_scripts = len(results)  # Count of successfully processed scripts
        total_validations = sum(
            r["validation_summary"]["total_validations"] for r in results
        )  # Sum all validations
        total_valid = sum(
            r["validation_summary"]["valid_count"] for r in results
        )  # Sum valid elements
        total_invalid = sum(
            r["validation_summary"]["invalid_count"] for r in results
        )  # Sum invalid elements
        total_not_found = sum(
            r["validation_summary"]["not_found_count"] for r in results
        )  # Sum not found elements
        total_hallucinations = sum(
            len(r["hallucinations_detected"]) for r in results
        )  # Sum detected hallucinations

        # CONFIDENCE AVERAGE CALCULATION
        # TAGS: [confidence-calculation, average-metrics]
        avg_confidence = (
            sum(r["validation_summary"]["overall_confidence"] for r in results)
            / total_scripts
        )

        # BASIC METRICS DISPLAY
        # TAGS: [metrics-display, console-output]
        print(f"Scripts Processed: {total_scripts}")  # Display script count
        print(
            f"Total Validations: {total_validations}"
        )  # Display total validation count
        print(
            f"Average Confidence: {avg_confidence:.1%}"
        )  # Display average confidence percentage
        print(
            f"Total Hallucinations: {total_hallucinations}"
        )  # Display total hallucination count

        # AGGREGATED RESULTS DISPLAY
        # TAGS: [results-display, percentage-calculations]
        print(f"\nAggregated Results:")
        if total_validations > 0:
            print(
                f"  ✅ Valid: {total_valid} ({total_valid/total_validations:.1%})"
            )  # Valid elements with percentage
            print(
                f"  ❌ Invalid: {total_invalid} ({total_invalid/total_validations:.1%})"
            )  # Invalid elements with percentage
            print(
                f"  🔍 Not Found: {total_not_found} ({total_not_found/total_validations:.1%})"
            )  # Not found elements with percentage
        else:
            print(f"  ✅ Valid: {total_valid} (0.0%)")
            print(f"  ❌ Invalid: {total_invalid} (0.0%)")
            print(f"  🔍 Not Found: {total_not_found} (0.0%)")

        # WORST PERFORMING SCRIPTS DISPLAY
        # TAGS: [worst-performers, ranking, issue-identification]
        # PURPOSE: Highlight scripts with the most hallucinations for priority attention
        print(f"\n🚨 Scripts with Most Hallucinations:")
        sorted_results = sorted(
            results, key=lambda x: len(x["hallucinations_detected"]), reverse=True
        )  # Sort by hallucination count
        for result in sorted_results[:5]:  # Show top 5 worst performers
            script_name = Path(
                result["analysis_metadata"]["script_path"]
            ).name  # Extract script filename
            hall_count = len(result["hallucinations_detected"])  # Count hallucinations
            confidence = result["validation_summary"][
                "overall_confidence"
            ]  # Get confidence score
            print(
                f"  - {script_name}: {hall_count} hallucinations ({confidence:.1%} confidence)"
            )

        # SUMMARY FOOTER
        # TAGS: [console-formatting, footer-display]
        print("=" * 80)


# MAIN CLI FUNCTION
# TAGS: [cli-interface, main-function, command-line]
# PURPOSE: Provide command-line interface for the hallucination detector
async def main():
    """Command-line interface for the AI Hallucination Detector"""
    # ARGUMENT PARSER SETUP
    # TAGS: [argument-parsing, cli-setup, help-text]
    # PURPOSE: Define command-line arguments and help documentation
    parser = argparse.ArgumentParser(
        description="Detect AI coding assistant hallucinations in Python scripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,  # Preserve example formatting
        epilog="""
Examples:
  # Analyze single script
  python ai_hallucination_detector.py script.py

  # Analyze multiple scripts
  python ai_hallucination_detector.py script1.py script2.py script3.py

  # Specify output directory
  python ai_hallucination_detector.py script.py --output-dir reports/

  # Skip markdown report
  python ai_hallucination_detector.py script.py --no-markdown
        """,
    )

    # POSITIONAL ARGUMENTS
    # TAGS: [positional-args, script-input]
    parser.add_argument(
        "scripts",
        nargs="+",  # Accept one or more scripts
        help="Python script(s) to analyze for hallucinations",
    )

    # OUTPUT OPTIONS
    # TAGS: [output-options, file-system]
    parser.add_argument(
        "--output-dir", help="Directory to save reports (defaults to script directory)"
    )

    # REPORT FORMAT OPTIONS
    # TAGS: [report-options, output-format]
    parser.add_argument(
        "--no-json",
        action="store_true",  # Boolean flag
        help="Skip JSON report generation",
    )

    parser.add_argument(
        "--no-markdown",
        action="store_true",  # Boolean flag
        help="Skip Markdown report generation",
    )

    parser.add_argument(
        "--no-summary",
        action="store_true",  # Boolean flag
        help="Skip printing summary to console",
    )

    # NEO4J CONNECTION OPTIONS
    # TAGS: [neo4j-options, database-connection]
    parser.add_argument(
        "--neo4j-uri",
        default=None,  # Use environment variable if not provided
        help="Neo4j URI (default: from environment NEO4J_URI)",
    )

    parser.add_argument(
        "--neo4j-user",
        default=None,  # Use environment variable if not provided
        help="Neo4j username (default: from environment NEO4J_USER)",
    )

    parser.add_argument(
        "--neo4j-password",
        default=None,  # Use environment variable if not provided
        help="Neo4j password (default: from environment NEO4J_PASSWORD)",
    )

    # LOGGING OPTIONS
    # TAGS: [logging-options, verbosity]
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging"  # Boolean flag
    )

    # ARGUMENT PARSING
    # TAGS: [argument-parsing, cli-processing]
    args = parser.parse_args()  # Parse command-line arguments

    # VERBOSE LOGGING SETUP
    # TAGS: [logging-configuration, verbosity-control]
    # PURPOSE: Configure logging levels based on verbosity flag
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)  # Enable verbose logging
        # Only enable debug for our modules, not neo4j
        logging.getLogger("neo4j").setLevel(
            logging.WARNING
        )  # Suppress Neo4j debug logs
        logging.getLogger("neo4j.pool").setLevel(
            logging.WARNING
        )  # Suppress Neo4j pool logs
        logging.getLogger("neo4j.io").setLevel(
            logging.WARNING
        )  # Suppress Neo4j I/O logs

    # ENVIRONMENT VARIABLE LOADING
    # TAGS: [environment-setup, configuration]
    # PURPOSE: Load configuration from .env file
    load_dotenv()  # Load environment variables from .env file

    # NEO4J CREDENTIAL RESOLUTION
    # TAGS: [credential-resolution, configuration, neo4j-setup]
    # PURPOSE: Resolve Neo4j connection credentials from args or environment
    neo4j_uri = args.neo4j_uri or os.environ.get(
        "NEO4J_URI", "bolt://localhost:7687"
    )  # URI with fallback
    neo4j_user = args.neo4j_user or os.environ.get(
        "NEO4J_USER", "neo4j"
    )  # Username with fallback
    neo4j_password = args.neo4j_password or os.environ.get(
        "NEO4J_PASSWORD", "password"
    )  # Password with fallback

    # PASSWORD VALIDATION
    # TAGS: [security-validation, credential-check]
    # PURPOSE: Ensure secure password is provided
    if not neo4j_password or neo4j_password == "password":
        logger.error(
            "Please set NEO4J_PASSWORD environment variable or use --neo4j-password"
        )
        sys.exit(1)  # Exit if insecure password

    # DETECTOR INITIALIZATION
    # TAGS: [detector-init, component-setup]
    # PURPOSE: Create and initialize the main detector with Neo4j credentials
    detector = AIHallucinationDetector(
        neo4j_uri, neo4j_user, neo4j_password
    )  # Create detector instance

    # MAIN EXECUTION BLOCK
    # TAGS: [main-execution, error-handling]
    try:
        await detector.initialize()  # Initialize async components

        # PROCESSING MODE SELECTION
        # TAGS: [mode-selection, single-vs-batch]
        # PURPOSE: Choose between single script and batch processing modes
        if len(args.scripts) == 1:
            # SINGLE SCRIPT MODE
            # TAGS: [single-script, individual-processing]
            await detector.detect_hallucinations(
                script_path=args.scripts[0],  # Single script path
                output_dir=args.output_dir,  # Output directory
                save_json=not args.no_json,  # JSON report flag (inverted)
                save_markdown=not args.no_markdown,  # Markdown report flag (inverted)
                print_summary=not args.no_summary,  # Summary flag (inverted)
            )
        else:
            # BATCH PROCESSING MODE
            # TAGS: [batch-processing, multiple-scripts]
            await detector.batch_detect(
                script_paths=args.scripts,  # Multiple script paths
                output_dir=args.output_dir,  # Shared output directory
            )

    # KEYBOARD INTERRUPT HANDLING
    # TAGS: [interrupt-handling, graceful-shutdown]
    except KeyboardInterrupt:
        logger.info("Detection interrupted by user")  # Log user interruption
        sys.exit(1)  # Exit with error code

    # GENERAL EXCEPTION HANDLING
    # TAGS: [error-handling, failure-logging]
    except Exception as e:
        logger.error(f"Detection failed: {str(e)}")  # Log failure details
        sys.exit(1)  # Exit with error code

    # CLEANUP BLOCK
    # TAGS: [cleanup, resource-management]
    # PURPOSE: Always close detector resources, even on error
    finally:
        await detector.close()  # Close database connections and cleanup


# SCRIPT ENTRY POINT
# TAGS: [entry-point, main-execution, async-runner]
# PURPOSE: Run the CLI interface when script is executed directly
if __name__ == "__main__":
    asyncio.run(main())  # Run async main function
