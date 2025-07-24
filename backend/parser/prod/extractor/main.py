#!/usr/bin/env python
"""
Main entry point for the Extractor Domain.

This module orchestrates the entire extraction phase, parsing a codebase
and producing a structured JSON output file containing all code elements
and their relationships.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Optional
import uuid

from codebase_parser import CodebaseParser
from serialization import Serializer
from models import ParsedModule
from communication import StatusReporter


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExtractorMain:
    """Main orchestrator for the extraction phase."""
    
    def __init__(self, job_id: Optional[str] = None):
        """Initialize the extractor with optional job ID."""
        self.job_id = job_id or str(uuid.uuid4())
        self.status_reporter = StatusReporter(job_id=self.job_id)
        self.codebase_parser = CodebaseParser()
        self.serializer = Serializer()
        
    def extract(self, codebase_path: str, output_path: Optional[str] = None) -> str:
        """
        Extract code structure from the given codebase.
        
        Args:
            codebase_path: Path to the codebase to analyze
            output_path: Optional custom output path
            
        Returns:
            Path to the generated output file
        """
        try:
            # Report extraction started
            self.status_reporter.report_status(
                phase="extraction",
                status="started",
                message=f"Starting extraction for codebase: {codebase_path}"
            )
            
            # Validate input path
            path = Path(codebase_path)
            if not path.exists():
                raise ValueError(f"Codebase path does not exist: {codebase_path}")
            if not path.is_dir():
                raise ValueError(f"Codebase path is not a directory: {codebase_path}")
            
            # Parse the codebase
            logger.info(f"Parsing codebase at: {codebase_path}")
            self.status_reporter.report_status(
                phase="extraction",
                status="parsing",
                message="Discovering and parsing Python files"
            )
            
            parsed_modules: Dict[str, ParsedModule] = self.codebase_parser.parse_codebase(
                str(path),
                status_reporter=self.status_reporter
            )
            
            # Generate output filename
            if output_path is None:
                output_path = f"extraction_output_{self.job_id}.json"
            
            # Serialize the results
            logger.info(f"Serializing {len(parsed_modules)} modules to {output_path}")
            self.status_reporter.report_status(
                phase="extraction",
                status="serializing",
                message=f"Serializing {len(parsed_modules)} parsed modules"
            )
            
            serialized_data = self.serializer.serialize_modules(parsed_modules)
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(serialized_data, f, indent=2)
            
            # Report completion
            self.status_reporter.report_status(
                phase="extraction",
                status="completed",
                message=f"Extraction completed. Output saved to: {output_path}",
                metadata={
                    "modules_parsed": len(parsed_modules),
                    "output_file": output_path
                }
            )
            
            logger.info(f"Extraction completed. Output saved to: {output_path}")
            return output_path
            
        except Exception as e:
            # Report error
            self.status_reporter.report_status(
                phase="extraction",
                status="error",
                message=str(e)
            )
            logger.error(f"Extraction failed: {e}")
            raise


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(
        description="Extract code structure from a Python codebase"
    )
    parser.add_argument(
        "--path",
        required=True,
        help="Path to the codebase to analyze"
    )
    parser.add_argument(
        "--job-id",
        help="Unique job identifier (generated if not provided)"
    )
    parser.add_argument(
        "--output",
        help="Custom output file path (default: extraction_output_<job_id>.json)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        extractor = ExtractorMain(job_id=args.job_id)
        output_file = extractor.extract(
            codebase_path=args.path,
            output_path=args.output
        )
        print(f"Extraction successful. Output: {output_file}")
        sys.exit(0)
    except Exception as e:
        print(f"Extraction failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()