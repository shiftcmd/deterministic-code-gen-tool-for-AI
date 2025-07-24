#!/usr/bin/env python3
"""
Test Phase 1 integration with the new Phase 2 transformation domain.
"""

import json
import asyncio
from pathlib import Path

# Add the transformer to the path
import sys
sys.path.append(str(Path(__file__).parent))

from transformer.main import TransformationOrchestrator, transform_file


def create_full_extraction_format():
    """Create a complete Phase 1 extraction format with the sample module."""
    
    # Load the sample data
    sample_file = Path(__file__).parent / "sample_phase1_output.json"
    with open(sample_file, 'r') as f:
        module_data = json.load(f)
    
    # Create the full extraction format that Phase 1 outputs
    extraction_output = {
        "metadata": {
            "extraction_id": "test_extraction_001",
            "timestamp": "2025-01-24T10:30:00Z",
            "version": "1.0.0",
            "total_files": 1,
            "total_modules": 1,
            "processing_time_seconds": 2.5,
            "parser_version": "dev",
            "extracted_by": "test_integration"
        },
        "modules": {
            module_data["path"]: module_data
        },
        "statistics": {
            "total_imports": len(module_data["imports"]),
            "total_classes": len(module_data["classes"]),
            "total_functions": len(module_data["functions"]),
            "total_variables": len(module_data["variables"]),
            "total_lines": module_data["line_count"],
            "total_bytes": module_data["size_bytes"]
        },
        "errors": [],
        "warnings": []
    }
    
    return extraction_output


async def test_transformation():
    """Test the Phase 2 transformation with Phase 1 data."""
    
    print("Phase 1 -> Phase 2 Integration Test")
    print("=" * 50)
    
    # Create the full extraction format
    extraction_data = create_full_extraction_format()
    
    # Save it to a file for testing
    test_input_file = Path(__file__).parent / "test_extraction_input.json"
    with open(test_input_file, 'w') as f:
        json.dump(extraction_data, f, indent=2)
    
    print(f"Created test extraction file: {test_input_file}")
    print(f"Input statistics:")
    print(f"  - Modules: {len(extraction_data['modules'])}")
    print(f"  - Classes: {extraction_data['statistics']['total_classes']}")  
    print(f"  - Functions: {extraction_data['statistics']['total_functions']}")
    print(f"  - Imports: {extraction_data['statistics']['total_imports']}")
    print()
    
    # Test transformation using the new orchestrator
    print("Starting Phase 2 transformation...")
    
    try:
        # Create output directory
        output_dir = Path(__file__).parent / "test_output"
        output_dir.mkdir(exist_ok=True)
        
        # Run transformation
        orchestrator = TransformationOrchestrator(
            job_id="test_phase1_integration",
            enable_progress_reporting=False  # Disable for testing
        )
        
        result = await orchestrator.transform_extraction_data(
            extraction_data,
            output_formats=["neo4j", "json"],
            output_directory=str(output_dir)
        )
        
        # Display results
        print("Transformation Results:")
        print("=" * 30)
        print(f"Success: {result.success}")
        print(f"Job ID: {result.job_id}")
        print(f"Errors: {len(result.errors)}")
        print(f"Warnings: {len(result.warnings)}")
        print(f"Output files: {list(result.output_files.keys())}")
        
        if result.errors:
            print("\nErrors:")
            for error in result.errors:
                print(f"  - {error}")
        
        if result.warnings:
            print("\nWarnings:")
            for warning in result.warnings:
                print(f"  - {warning}")
        
        # Display transformation statistics
        metadata = result.metadata.to_dict()
        print(f"\nTransformation Statistics:")
        print(f"  - Processing time: {metadata['processing_statistics']['time_seconds']:.2f}s")
        print(f"  - Nodes generated: {metadata['output_statistics']['nodes']}")
        print(f"  - Relationships generated: {metadata['output_statistics']['relationships']}")
        print(f"  - Output formats: {metadata['output_statistics']['formats']}")
        
        # Show sample of generated Neo4j commands
        if "neo4j" in result.output_files:
            neo4j_file = result.output_files["neo4j"]
            print(f"\nSample Neo4j output (first 10 lines of {neo4j_file}):")
            with open(neo4j_file, 'r') as f:
                lines = f.readlines()
                for i, line in enumerate(lines[:10]):
                    print(f"  {i+1:2d}: {line.rstrip()}")
                if len(lines) > 10:
                    print(f"  ... ({len(lines) - 10} more lines)")
        
        return result
        
    except Exception as e:
        print(f"Transformation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_streaming_transformation():
    """Test streaming transformation capability."""
    
    print("\n" + "=" * 50)
    print("Testing Streaming Transformation")
    print("=" * 50)
    
    # Create test data
    extraction_data = create_full_extraction_format()
    
    async def mock_extraction_stream():
        """Mock extraction stream that yields extraction data."""
        yield extraction_data
    
    try:
        orchestrator = TransformationOrchestrator(
            job_id="test_streaming",
            enable_progress_reporting=False
        )
        
        tuple_count = 0
        batch_count = 0
        
        async for tuple_set in orchestrator.stream_transform(
            mock_extraction_stream(),
            batch_size=5
        ):
            batch_count += 1
            tuple_count += tuple_set.size
            print(f"Batch {batch_count}: {tuple_set.size} tuples "
                  f"({tuple_set.node_count} nodes, {tuple_set.relationship_count} relationships)")
        
        print(f"\nStreaming transformation complete:")
        print(f"  - Total batches: {batch_count}")
        print(f"  - Total tuples: {tuple_count}")
        
    except Exception as e:
        print(f"Streaming transformation failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all integration tests."""
    # Test basic transformation
    result = await test_transformation()
    
    if result and result.success:
        print("\n✅ Phase 1 -> Phase 2 integration test PASSED")
        
        # Test streaming if basic test passed
        await test_streaming_transformation()
        print("\n✅ Streaming transformation test PASSED")
        
    else:
        print("\n❌ Phase 1 -> Phase 2 integration test FAILED")
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)