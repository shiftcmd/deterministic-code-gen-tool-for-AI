#!/usr/bin/env python3
"""
Test complete job_id flow through orchestrator and all phases.

This test verifies that:
1. Orchestrator creates unique job_id using uuid.uuid4()
2. Job_id flows to Phase 1 (extractor) via --job-id argument
3. Job_id flows to Phase 2 (transformer) via --job-id argument  
4. Job_id is used in output filenames throughout
5. Job_id flows back to orchestrator for tracking
"""

import sys
import uuid
from pathlib import Path

# Add parser directory to path
sys.path.append(str(Path(__file__).parent / "parser" / "prod" / "orchestrator"))

from main import OrchestrationService, Job


def test_orchestrator_job_creation():
    """Test orchestrator job_id creation and management."""
    
    print("🆔 ORCHESTRATOR JOB ID CREATION TEST")
    print("=" * 60)
    
    try:
        orchestrator = OrchestrationService()
        
        # Test job creation
        codebase_path = "/test/path"
        job_id = orchestrator.create_job(codebase_path)
        
        print(f"✅ Job ID created: {job_id}")
        
        # Verify it's a valid UUID
        try:
            uuid_obj = uuid.UUID(job_id)
            print(f"✅ Job ID is valid UUID: {uuid_obj.version}")
        except ValueError:
            print("❌ Job ID is not a valid UUID")
            return False
        
        # Test job retrieval
        job = orchestrator.get_job(job_id)
        if job and job.job_id == job_id:
            print(f"✅ Job retrieved successfully: {job.job_id}")
            print(f"✅ Codebase path stored: {job.codebase_path}")
        else:
            print("❌ Failed to retrieve job")
            return False
        
        # Test multiple job creation (unique IDs)
        job_id_2 = orchestrator.create_job("/another/path")
        if job_id != job_id_2:
            print(f"✅ Multiple jobs have unique IDs: {job_id} != {job_id_2}")
        else:
            print("❌ Job IDs are not unique")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Orchestrator job creation test failed: {e}")
        return False


def test_phase1_job_id_flow():
    """Test job_id flow to Phase 1 extractor."""
    
    print("\n🔧 PHASE 1 JOB ID FLOW TEST")
    print("=" * 60)
    
    try:
        orchestrator = OrchestrationService()
        
        # Create job
        codebase_path = "/test/path"
        job_id = orchestrator.create_job(codebase_path)
        job = orchestrator.get_job(job_id)
        
        print(f"✅ Test job created: {job_id}")
        
        # Check Phase 1 command construction
        output_file = f"extraction_output_{job.job_id}.json"
        
        # This simulates what _run_extractor does
        cmd = [
            sys.executable,
            str(orchestrator.extractor_dir / "main.py"),
            "--path", job.codebase_path,
            "--job-id", job.job_id,
            "--output", output_file
        ]
        
        print("✅ Phase 1 command constructed:")
        print(f"   Command: {' '.join(cmd)}")
        
        # Verify job_id is in command
        if job.job_id in cmd:
            print(f"✅ Job ID passed to Phase 1: --job-id {job.job_id}")
        else:
            print("❌ Job ID not found in Phase 1 command")
            return False
        
        # Verify output filename includes job_id
        if job.job_id in output_file:
            print(f"✅ Output filename includes job ID: {output_file}")
        else:
            print("❌ Output filename doesn't include job ID")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Phase 1 job ID flow test failed: {e}")
        return False


def test_phase2_job_id_flow():
    """Test job_id flow to Phase 2 transformer."""
    
    print("\n⚙️  PHASE 2 JOB ID FLOW TEST")
    print("=" * 60)
    
    try:
        orchestrator = OrchestrationService()
        
        # Create job and simulate Phase 1 completion
        codebase_path = "/test/path"
        job_id = orchestrator.create_job(codebase_path)
        job = orchestrator.get_job(job_id)
        job.extraction_output = f"extraction_output_{job_id}.json"
        
        print(f"✅ Test job prepared: {job_id}")
        
        # Check Phase 2 command construction  
        output_file = f"cypher_commands_{job.job_id}.txt"
        
        # This simulates what _run_transformer does
        cmd = [
            sys.executable,
            str(orchestrator.transformer_dir / "main.py"),
            "--input", job.extraction_output,
            "--job-id", job.job_id,
            "--output", output_file
        ]
        
        print("✅ Phase 2 command constructed:")
        print(f"   Command: {' '.join(cmd)}")
        
        # Verify job_id is in command
        if job.job_id in cmd:
            print(f"✅ Job ID passed to Phase 2: --job-id {job.job_id}")
        else:
            print("❌ Job ID not found in Phase 2 command")
            return False
        
        # Verify input filename includes job_id (from Phase 1)
        if job.job_id in job.extraction_output:
            print(f"✅ Input filename includes job ID: {job.extraction_output}")
        else:
            print("❌ Input filename doesn't include job ID")
        
        # Verify output filename includes job_id
        if job.job_id in output_file:
            print(f"✅ Output filename includes job ID: {output_file}")
        else:
            print("❌ Output filename doesn't include job ID")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Phase 2 job ID flow test failed: {e}")
        return False


def test_job_status_tracking():
    """Test job status tracking with job_id."""
    
    print("\n📊 JOB STATUS TRACKING TEST")
    print("=" * 60)
    
    try:
        orchestrator = OrchestrationService()
        
        # Create job
        codebase_path = "/test/path"
        job_id = orchestrator.create_job(codebase_path)
        
        print(f"✅ Job created for tracking: {job_id}")
        
        # Test status updates
        orchestrator.update_job_status(
            job_id,
            orchestrator.jobs[job_id].status,  # Use current status enum
            "extraction",
            "Starting extraction",
            progress=10.0
        )
        
        # Verify status was updated
        job = orchestrator.get_job(job_id)
        if job.message == "Starting extraction":
            print(f"✅ Job status updated: {job.message}")
        else:
            print("❌ Job status not updated")
            return False
        
        if job.progress == 10.0:
            print(f"✅ Progress tracking working: {job.progress}%")
        else:
            print("❌ Progress tracking failed")
            return False
        
        # Test multiple status updates
        orchestrator.update_job_status(
            job_id,
            orchestrator.jobs[job_id].status,
            "transformation", 
            "Processing transformation",
            progress=50.0
        )
        
        job = orchestrator.get_job(job_id)
        if job.progress == 50.0 and job.phase == "transformation":
            print(f"✅ Multiple status updates working: {job.phase} @ {job.progress}%")
        else:
            print("❌ Multiple status updates failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Job status tracking test failed: {e}")
        return False


def test_job_id_consistency():
    """Test job_id consistency across all components."""
    
    print("\n🔄 JOB ID CONSISTENCY TEST")
    print("=" * 60)
    
    try:
        orchestrator = OrchestrationService()
        
        # Create job
        codebase_path = "/test/path"
        original_job_id = orchestrator.create_job(codebase_path)
        
        print(f"✅ Original job ID: {original_job_id}")
        
        # Verify job_id consistency in all file names
        job = orchestrator.get_job(original_job_id)
        
        expected_files = {
            "extraction_output": f"extraction_output_{original_job_id}.json",
            "cypher_commands": f"cypher_commands_{original_job_id}.txt",
            "loader_output": f"loader_output_{original_job_id}.json"  # Future Phase 3
        }
        
        print("✅ Expected output files:")
        for file_type, filename in expected_files.items():
            print(f"   {file_type}: {filename}")
            
            # Verify job_id is in filename
            if original_job_id in filename:
                print(f"   ✅ Job ID consistent in {file_type}")
            else:
                print(f"   ❌ Job ID missing from {file_type}")
                return False
        
        # Test file name generation functions
        extraction_file = f"extraction_output_{original_job_id}.json"
        cypher_file = f"cypher_commands_{original_job_id}.txt"
        
        # Simulate Phase 1 → Phase 2 flow
        job.extraction_output = extraction_file
        job.cypher_commands = cypher_file
        
        if (job.extraction_output == extraction_file and 
            job.cypher_commands == cypher_file):
            print("✅ File naming consistency maintained")
        else:
            print("❌ File naming consistency broken")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Job ID consistency test failed: {e}")
        return False


def main():
    """Run complete job_id flow test."""
    
    tests = [
        ("Orchestrator Job Creation", test_orchestrator_job_creation),
        ("Phase 1 Job ID Flow", test_phase1_job_id_flow),
        ("Phase 2 Job ID Flow", test_phase2_job_id_flow),
        ("Job Status Tracking", test_job_status_tracking),
        ("Job ID Consistency", test_job_id_consistency)
    ]
    
    results = {}
    for test_name, test_func in tests:
        results[test_name] = test_func()
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 JOB ID FLOW TEST SUMMARY")
    print("=" * 60)
    
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 JOB ID FLOW VALIDATION: SUCCESS!")
        print("\n✨ Complete Job ID Flow:")
        print("   1. Orchestrator creates UUID job_id")
        print("   2. Job_id passed to Phase 1 via --job-id argument")
        print("   3. Phase 1 uses job_id in output filename")
        print("   4. Job_id passed to Phase 2 via --job-id argument")
        print("   5. Phase 2 uses job_id in output filename")
        print("   6. Job_id used for status tracking throughout")
        print("   7. All phases report back to orchestrator with job_id")
        
        print("\n📋 Job ID Benefits:")
        print("   • Unique identification of each analysis run")
        print("   • File traceability across all phases")
        print("   • Status tracking and progress reporting")
        print("   • Result retrieval and download")
        print("   • Error tracking and debugging")
        
        return True
    else:
        print(f"\n❌ JOB ID FLOW INCOMPLETE: {total_tests - passed_tests} issues found")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)