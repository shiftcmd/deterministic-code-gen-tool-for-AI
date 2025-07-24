#!/usr/bin/env python3
"""
Command-line interface for the new Phase 2 Transformer domain.

This is a bridge that allows the existing orchestrator to call
the new transformer implementation.
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add parent directories to path to access new transformer
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from transformer.main import transform_file


async def main():
    """Command-line entry point for transformer."""
    parser = argparse.ArgumentParser(
        description="Transform code extraction output to Neo4j Cypher commands"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the extraction_output.json file"
    )
    parser.add_argument(
        "--job-id",
        required=True,
        help="Job identifier (must match extraction job)"
    )
    parser.add_argument(
        "--output",
        help="Custom output file path (default: cypher_commands_<job_id>.txt)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Use the new transformer implementation
        result = await transform_file(
            input_file=args.input,
            output_directory=Path(args.output).parent if args.output else ".",
            output_formats=["neo4j"],
            job_id=args.job_id
        )
        
        if result.success:
            # Rename output file to match orchestrator expectations
            if args.output and "neo4j" in result.output_files:
                source_file = Path(result.output_files["neo4j"])
                target_file = Path(args.output)
                if source_file.exists():
                    source_file.rename(target_file)
            
            print(f"Transformation successful. Job ID: {result.job_id}")
            sys.exit(0)
        else:
            print(f"Transformation failed: {', '.join(result.errors)}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Transformation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())