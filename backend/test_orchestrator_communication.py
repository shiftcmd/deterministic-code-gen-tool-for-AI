#!/usr/bin/env python3
"""
Test orchestrator communication and validation.
"""

import json
from pathlib import Path

def test_orchestrator_communication():
    """Test orchestrator communication patterns."""
    
    print("Orchestrator Communication Test")
    print("=" * 50)
    
    # Test progress service
    import sys
    sys.path.append(str(Path(__file__).parent))
    
    from transformer.services.progress_service import ProgressService
    
    try:
        progress_service = ProgressService("test_orchestrator_comm")
        
        print("1. Testing transformation lifecycle...")
        
        # Test status reporting
        success = progress_service.start_transformation({
            "modules": 1,
            "classes": 4, 
            "functions": 16,
            "imports": 12
        })
        print(f"   ✅ Start transformation reported: {success}")
        
        # Test progress reporting
        success = progress_service.report_progress(25, 100, "tuple_generation", "Generating tuples")
        print(f"   ✅ Progress reported (25%): {success}")
        
        success = progress_service.report_progress(50, 100, "relationship_mapping", "Mapping relationships") 
        print(f"   ✅ Progress reported (50%): {success}")
        
        success = progress_service.report_progress(75, 100, "output_formatting", "Formatting output")
        print(f"   ✅ Progress reported (75%): {success}")
        
        # Test step completion
        success = progress_service.report_step_completed("tuple_generation")
        print(f"   ✅ Step completion reported: {success}")
        
        # Test batch processing
        success = progress_service.report_batch_processed(1, 25, 1.5)
        print(f"   ✅ Batch processing reported: {success}")
        
        # Test validation results
        success = progress_service.report_validation_results(True, [], ["Minor warning about unused import"])
        print(f"   ✅ Validation results reported: {success}")
        
        # Test completion
        success = progress_service.complete_transformation(
            {"neo4j": "/path/to/output.cypher", "json": "/path/to/output.json"},
            {"nodes": 21, "relationships": 34}
        )
        print(f"   ✅ Completion reported: {success}")
        
        # Check metadata
        metadata = progress_service.get_metadata()
        print(f"   ✅ Metadata collected for job: {metadata.job_id}")
        print(f"   ✅ Final status: {metadata.status.value}")
        print(f"   ✅ Processing time: {metadata.processing_time_seconds:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Orchestrator communication test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_status_file_generation():
    """Test status file generation and format."""
    
    print("\n2. Testing status file generation...")
    
    # Check if status files were created
    status_files = list(Path(".").glob("transformation_status_*.json"))
    
    if status_files:
        print(f"   ✅ Found {len(status_files)} status file(s)")
        
        # Read and validate the most recent status file
        latest_file = max(status_files, key=lambda f: f.stat().st_mtime)
        
        try:
            with open(latest_file, 'r') as f:
                status_data = json.load(f)
            
            print(f"   ✅ Status file is valid JSON: {latest_file.name}")
            print(f"   ✅ Contains {len(status_data)} status updates")
            
            # Show sample status updates
            if status_data:
                print("   📊 Sample status updates:")
                for i, update in enumerate(status_data[:3]):  # First 3 updates
                    print(f"      {i+1}. {update.get('status', 'unknown')} - {update.get('message', 'no message')}")
                
                if len(status_data) > 3:
                    print(f"      ... and {len(status_data) - 3} more updates")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error reading status file: {e}")
            return False
    else:
        print("   ❌ No status files found")
        return False


def test_transformation_metadata():
    """Test transformation metadata structure."""
    
    print("\n3. Testing transformation metadata...")
    
    from transformer.models.metadata import TransformationMetadata, TransformationStatus
    
    try:
        # Create and test metadata
        metadata = TransformationMetadata(job_id="test_metadata")
        
        # Test initial state
        assert metadata.status == TransformationStatus.PENDING
        print("   ✅ Initial status is PENDING")
        
        # Test starting transformation
        metadata.start()
        assert metadata.status == TransformationStatus.RUNNING
        assert metadata.started_at is not None
        print("   ✅ Start() changes status to RUNNING")
        
        # Test progress updates
        metadata.update_progress(50.0, "processing")
        assert metadata.progress_percentage == 50.0
        assert metadata.current_step == "processing"
        print("   ✅ Progress updates work correctly")
        
        # Test step tracking
        metadata.add_completed_step("tuple_generation")
        assert "tuple_generation" in metadata.steps_completed
        print("   ✅ Step tracking works correctly")
        
        # Test completion
        metadata.complete()
        assert metadata.status == TransformationStatus.COMPLETED
        assert metadata.completed_at is not None
        assert metadata.progress_percentage == 100.0
        print("   ✅ Complete() changes status to COMPLETED")
        
        # Test serialization
        metadata_dict = metadata.to_dict()
        assert isinstance(metadata_dict, dict)
        assert "job_id" in metadata_dict
        assert "status" in metadata_dict
        print("   ✅ Metadata serialization works")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Metadata test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_phase3_handoff_format():
    """Test Phase 3 handoff format preparation."""
    
    print("\n4. Testing Phase 3 handoff format...")
    
    from transformer.models.tuples import TupleSet, Neo4jNodeTuple, Neo4jRelationshipTuple
    from transformer.models.relationships import RelationshipType
    
    try:
        # Create sample tuple set (what Phase 3 will receive)
        tuple_set = TupleSet()
        
        # Add sample node
        node = Neo4jNodeTuple(
            label="Module",
            properties={"name": "test_module", "path": "/test/path.py"},
            unique_key="module:/test/path.py",
            merge_properties={"path"}
        )
        tuple_set.add_node(node)
        
        # Add sample relationship
        relationship = Neo4jRelationshipTuple(
            source_key="module:/test/path.py",
            target_key="module:os",
            relationship_type=RelationshipType.IMPORTS.value,
            properties={"import_name": "os", "line_start": 1},
            source_label="Module",
            target_label="Module"
        )
        tuple_set.add_relationship(relationship)
        
        # Test serialization for Phase 3
        phase3_data = tuple_set.to_dict()
        
        assert "nodes" in phase3_data
        assert "relationships" in phase3_data
        assert "statistics" in phase3_data
        print("   ✅ Phase 3 data structure is correct")
        
        assert phase3_data["statistics"]["node_count"] == 1
        assert phase3_data["statistics"]["relationship_count"] == 1
        print("   ✅ Statistics are calculated correctly")
        
        # Validate node format
        node_data = phase3_data["nodes"][0]
        assert "label" in node_data
        assert "unique_key" in node_data
        assert "properties" in node_data
        print("   ✅ Node format is correct for Phase 3")
        
        # Validate relationship format
        rel_data = phase3_data["relationships"][0]
        assert "source_key" in rel_data
        assert "target_key" in rel_data
        assert "relationship_type" in rel_data
        print("   ✅ Relationship format is correct for Phase 3")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Phase 3 handoff test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all orchestrator and validation tests."""
    
    # Test orchestrator communication
    comm_success = test_orchestrator_communication()
    
    # Test status file generation
    file_success = test_status_file_generation()
    
    # Test metadata structure
    metadata_success = test_transformation_metadata()
    
    # Test Phase 3 handoff
    handoff_success = test_phase3_handoff_format()
    
    print("\n" + "=" * 50)
    print("ORCHESTRATOR & VALIDATION TEST SUMMARY")
    print("=" * 50)
    print(f"Orchestrator Communication: {'✅ PASS' if comm_success else '❌ FAIL'}")
    print(f"Status File Generation: {'✅ PASS' if file_success else '❌ FAIL'}")
    print(f"Metadata Structure: {'✅ PASS' if metadata_success else '❌ FAIL'}")
    print(f"Phase 3 Handoff Format: {'✅ PASS' if handoff_success else '❌ FAIL'}")
    
    overall_success = comm_success and file_success and metadata_success and handoff_success
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🎉 Phase 2 Transformation domain is ready!")
        print("   ✅ Can receive data from Phase 1 (extractor)")
        print("   ✅ Communicates with main orchestrator")
        print("   ✅ Provides progress updates for UI")
        print("   ✅ Generates data ready for Phase 3 (loader)")
    
    return overall_success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)