#!/usr/bin/env python3
"""
Phase 3 Upload Orchestrator - CLI Interface

Uploads Phase 2 transformation results to Neo4j graph database.
Integrates with existing orchestrator pipeline via CLI interface.
"""

import argparse
import asyncio
import sys
import json
from pathlib import Path

from .core.neo4j_client import Neo4jClient
from .core.batch_uploader import BatchUploader
from .services.validation_service import ValidationService
from .models.upload_result import UploadResult

async def main():
    """Command-line entry point for uploader."""
    parser = argparse.ArgumentParser(
        description="Upload Phase 2 transformation results to Neo4j"
    )
    parser.add_argument("--input", required=True, help="Path to cypher_commands file")
    parser.add_argument("--job-id", required=True, help="Job identifier")
    parser.add_argument("--output", help="Path to save upload results JSON")
    parser.add_argument("--neo4j-uri", help="Neo4j connection URI")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for uploads")
    parser.add_argument("--validate-only", action="store_true", help="Only validate, don't upload")
    parser.add_argument("--clear-database", help="Clear database before upload (true/false)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Initialize services
    neo4j_client = Neo4jClient(uri=args.neo4j_uri)
    validator = ValidationService()
    uploader = BatchUploader(neo4j_client, batch_size=args.batch_size)
    
    try:
        # Validate input file
        validation_result = await validator.validate_cypher_file(args.input)
        if not validation_result.is_valid:
            print(f"Validation failed: {', '.join(validation_result.errors)}")
            if args.output:
                _save_error_result(args.output, args.job_id, validation_result.errors)
            sys.exit(1)
        
        if args.validate_only:
            print("Validation successful")
            if args.output:
                _save_validation_result(args.output, validation_result)
            sys.exit(0)
        
        # Clear database if requested
        if args.clear_database and args.clear_database.lower() == "true":
            print("Clearing database before upload...")
            await _clear_database(neo4j_client)
        
        # Perform upload
        upload_result = await uploader.upload_from_file(
            args.input, 
            job_id=args.job_id
        )
        
        # Save results if output path provided
        if args.output:
            _save_upload_result(args.output, upload_result)
        
        if upload_result.success:
            print(f"Upload successful. Job ID: {upload_result.job_id}")
            print(f"Uploaded: {upload_result.nodes_created} nodes, {upload_result.relationships_created} relationships")
            if upload_result.upload_duration_seconds:
                print(f"Duration: {upload_result.upload_duration_seconds:.2f} seconds")
            sys.exit(0)
        else:
            print(f"Upload failed: {', '.join(upload_result.errors)}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Upload failed: {e}")
        if args.output:
            _save_error_result(args.output, args.job_id, [str(e)])
        sys.exit(1)


async def _clear_database(neo4j_client: Neo4jClient) -> None:
    """Clear the Neo4j database before upload."""
    try:
        # Connect to Neo4j
        await neo4j_client.connect()
        
        # Clear all nodes and relationships
        clear_commands = [
            "MATCH (n) DETACH DELETE n;",
            "CALL apoc.schema.assert({},{},true) YIELD label, key RETURN *;"  # Clear constraints/indexes if APOC available
        ]
        
        for command in clear_commands:
            try:
                result = await neo4j_client.execute_cypher_batch([command], batch_size=1)
                if not result.success:
                    print(f"Warning: Clear command failed: {command}")
            except Exception as e:
                # APOC may not be available, ignore errors for the second command
                if "apoc" not in command.lower():
                    raise e
        
        print("Database cleared successfully")
        
    except Exception as e:
        print(f"Failed to clear database: {e}")
        raise


def _save_upload_result(output_path: str, result: UploadResult) -> None:
    """Save upload result to JSON file."""
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        
        print(f"Upload results saved to: {output_path}")
        
    except Exception as e:
        print(f"Failed to save upload results: {e}")


def _save_validation_result(output_path: str, result) -> None:
    """Save validation result to JSON file."""
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        validation_data = {
            "operation": "validation",
            "result": result.to_dict(),
            "timestamp": result.to_dict().get("validated_at", "unknown")
        }
        
        with open(output_file, 'w') as f:
            json.dump(validation_data, f, indent=2)
        
        print(f"Validation results saved to: {output_path}")
        
    except Exception as e:
        print(f"Failed to save validation results: {e}")


def _save_error_result(output_path: str, job_id: str, errors: list) -> None:
    """Save error result to JSON file."""
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        error_data = {
            "job_id": job_id,
            "success": False,
            "errors": errors,
            "timestamp": Path().stat().st_mtime if Path().exists() else None
        }
        
        with open(output_file, 'w') as f:
            json.dump(error_data, f, indent=2)
        
        print(f"Error results saved to: {output_path}")
        
    except Exception as e:
        print(f"Failed to save error results: {e}")


if __name__ == "__main__":
    asyncio.run(main())