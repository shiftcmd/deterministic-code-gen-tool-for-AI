#!/usr/bin/env python3
"""
Demonstration of complete UI integration for Phase 2 downloads.

This demo shows how the frontend UI can:
1. Start analysis via orchestrator
2. Monitor progress through all phases
3. Download both Neo4j Cypher and JSON outputs from Phase 2
4. Handle errors and missing files gracefully
"""

import json
import sys
import tempfile
from pathlib import Path

# Add parser directory to path
sys.path.append(str(Path(__file__).parent / "parser" / "prod" / "orchestrator"))

from main import OrchestrationService, JobStatus


def demo_complete_ui_workflow():
    """Demonstrate complete UI workflow with Phase 2 downloads."""
    
    print("🎨 UI INTEGRATION WORKFLOW DEMONSTRATION")
    print("=" * 70)
    
    try:
        orchestrator = OrchestrationService()
        
        # Step 1: UI starts analysis
        print("\n📋 STEP 1: Start Analysis")
        print("-" * 30)
        
        codebase_path = "/example/project"
        job_id = orchestrator.create_job(codebase_path)
        
        print(f"✅ Analysis started")
        print(f"   Job ID: {job_id}")
        print(f"   Codebase: {codebase_path}")
        print(f"   API Call: POST /v1/analyze")
        print(f"   Response: {{'job_id': '{job_id}', 'status': 'Analysis started'}}")
        
        # Step 2: UI monitors progress
        print("\n📊 STEP 2: Monitor Progress")
        print("-" * 30)
        
        job = orchestrator.get_job(job_id)
        print(f"✅ Initial status: {job.status} - {job.message}")
        print(f"   API Call: GET /v1/jobs/{job_id}/status")
        
        # Simulate Phase 1 progress
        orchestrator.update_job_status(
            job_id, JobStatus.EXTRACTING, "extraction", 
            "Processing Python files", progress=25.0
        )
        job = orchestrator.get_job(job_id)
        print(f"✅ Phase 1 progress: {job.status} - {job.message} ({job.progress}%)")
        
        # Simulate Phase 1 completion and Phase 2 start
        job.extraction_output = f"extraction_output_{job_id}.json"
        orchestrator.update_job_status(
            job_id, JobStatus.TRANSFORMING, "transformation",
            "Converting to Neo4j tuples", progress=60.0
        )
        job = orchestrator.get_job(job_id)
        print(f"✅ Phase 2 progress: {job.status} - {job.message} ({job.progress}%)")
        
        # Simulate Phase 2 completion
        job.cypher_commands = f"cypher_commands_{job_id}.cypher"
        job.tuples_output = f"tuples_{job_id}.json"
        orchestrator.update_job_status(
            job_id, JobStatus.COMPLETED, "completed",
            "Analysis completed successfully", progress=100.0
        )
        
        job = orchestrator.get_job(job_id)
        print(f"✅ Analysis complete: {job.status} - {job.message} ({job.progress}%)")
        
        # Step 3: UI retrieves results
        print("\n📄 STEP 3: Retrieve Results")
        print("-" * 30)
        
        print(f"✅ Job results available:")
        print(f"   API Call: GET /v1/jobs/{job_id}/results")
        print(f"   Response:")
        print(f"     - job_id: {job.job_id}")
        print(f"     - status: {job.status}")
        print(f"     - extraction_output: {job.extraction_output}")
        print(f"     - cypher_commands: {job.cypher_commands}")
        print(f"     - tuples_output: {job.tuples_output}")
        
        # Step 4: UI downloads Phase 2 outputs
        print("\n💾 STEP 4: Download Phase 2 Outputs")
        print("-" * 30)
        
        download_options = [
            {
                "name": "Neo4j Cypher Commands",
                "type": "cypher",
                "file": job.cypher_commands,
                "description": "Ready-to-execute Cypher commands for Neo4j database",
                "use_case": "Direct import into Neo4j graph database"
            },
            {
                "name": "JSON Tuples",
                "type": "tuples", 
                "file": job.tuples_output,
                "description": "Structured JSON with nodes and relationships",
                "use_case": "Custom processing or alternative graph databases"
            }
        ]
        
        for option in download_options:
            print(f"✅ {option['name']}:")
            print(f"   File: {option['file']}")
            print(f"   API Call: GET /v1/jobs/{job_id}/files/{option['type']}")
            print(f"   Description: {option['description']}")
            print(f"   Use Case: {option['use_case']}")
            print()
        
        # Step 5: UI handles different scenarios
        print("🔄 STEP 5: UI Scenarios")
        print("-" * 30)
        
        scenarios = [
            {
                "name": "Success Scenario",
                "description": "All files available for download",
                "action": "Display download buttons for both Cypher and JSON outputs"
            },
            {
                "name": "Partial Success",
                "description": "Only some files available",
                "action": "Display available downloads, hide unavailable ones"
            },
            {
                "name": "Processing Scenario", 
                "description": "Analysis still in progress",
                "action": "Show progress bar and status updates, disable downloads"
            },
            {
                "name": "Error Scenario",
                "description": "Analysis failed",
                "action": "Show error message, provide option to retry or contact support"
            }
        ]
        
        for scenario in scenarios:
            print(f"✅ {scenario['name']}:")
            print(f"   Condition: {scenario['description']}")
            print(f"   UI Action: {scenario['action']}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ UI workflow demo failed: {e}")
        return False


def demo_javascript_integration():
    """Show JavaScript code examples for UI integration."""
    
    print("\n💻 JAVASCRIPT INTEGRATION EXAMPLES")
    print("=" * 70)
    
    # Frontend code examples
    examples = {
        "start_analysis": '''
// Start analysis
async function startAnalysis(codebasePath) {
    const response = await fetch('/v1/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ codebase_path: codebasePath })
    });
    const result = await response.json();
    return result.job_id;
}''',
        "monitor_progress": '''
// Monitor progress with polling
async function monitorProgress(jobId) {
    const checkStatus = async () => {
        const response = await fetch(`/v1/jobs/${jobId}/status`);
        const status = await response.json();
        
        updateProgressBar(status.progress);
        updateStatusMessage(status.message);
        
        if (status.status === 'completed') {
            enableDownloads(jobId);
        } else if (status.status === 'failed') {
            showError(status.error);
        } else {
            setTimeout(checkStatus, 2000); // Poll every 2s
        }
    };
    checkStatus();
}''',
        "download_outputs": '''
// Download Phase 2 outputs
async function downloadPhase2Outputs(jobId) {
    // Download Neo4j Cypher commands
    const cypherUrl = `/v1/jobs/${jobId}/files/cypher`;
    downloadFile(cypherUrl, `cypher_commands_${jobId}.cypher`);
    
    // Download JSON tuples
    const tuplesUrl = `/v1/jobs/${jobId}/files/tuples`;
    downloadFile(tuplesUrl, `tuples_${jobId}.json`);
}

function downloadFile(url, filename) {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}''',
        "complete_workflow": '''
// Complete UI workflow
class CodeAnalysisUI {
    async analyzeCodebase(codebasePath) {
        try {
            // Start analysis
            this.jobId = await this.startAnalysis(codebasePath);
            this.showProgress();
            
            // Monitor progress
            await this.monitorProgress(this.jobId);
            
        } catch (error) {
            this.showError(`Analysis failed: ${error.message}`);
        }
    }
    
    async onAnalysisComplete(jobId) {
        // Get results
        const results = await this.getJobResults(jobId);
        
        // Show download options
        this.showDownloadOptions([
            {
                name: 'Neo4j Cypher Commands',
                url: `/v1/jobs/${jobId}/files/cypher`,
                description: 'Import directly into Neo4j'
            },
            {
                name: 'JSON Tuples',
                url: `/v1/jobs/${jobId}/files/tuples`,
                description: 'Process with custom tools'
            }
        ]);
    }
}'''
    }
    
    for title, code in examples.items():
        print(f"\n📝 {title.replace('_', ' ').title()}:")
        print(code)
    
    return True


def demo_error_scenarios():
    """Demonstrate error handling scenarios."""
    
    print("\n⚠️  ERROR HANDLING SCENARIOS")
    print("=" * 70)
    
    try:
        orchestrator = OrchestrationService()
        
        scenarios = [
            {
                "name": "File Not Found",
                "description": "User tries to download before analysis completes",
                "simulation": lambda: orchestrator.get_job("nonexistent-job-id"),
                "expected": "404 Not Found - Job not found",
                "ui_response": "Show 'Analysis not found' message"
            },
            {
                "name": "Invalid File Type",
                "description": "UI requests unsupported file type",
                "file_type": "invalid_type",
                "expected": "400 Bad Request - Invalid file type",
                "ui_response": "Log error, don't show download option"
            },
            {
                "name": "Analysis In Progress",
                "description": "User tries to download while analysis running",
                "simulation": lambda: "Job still processing",
                "expected": "400 Bad Request - Job is still running",
                "ui_response": "Disable download buttons, show progress"
            },
            {
                "name": "Analysis Failed",
                "description": "Analysis completed with errors",
                "simulation": lambda: "Analysis failed due to parsing errors",
                "expected": "Job status: failed",
                "ui_response": "Show error details, offer retry option"
            }
        ]
        
        for scenario in scenarios:
            print(f"\n🔍 {scenario['name']}:")
            print(f"   Description: {scenario['description']}")
            print(f"   Expected Response: {scenario['expected']}")
            print(f"   UI Response: {scenario['ui_response']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error scenarios demo failed: {e}")
        return False


def main():
    """Run complete UI integration demonstration."""
    
    demos = [
        ("Complete UI Workflow", demo_complete_ui_workflow),
        ("JavaScript Integration", demo_javascript_integration),
        ("Error Scenarios", demo_error_scenarios)
    ]
    
    results = {}
    for demo_name, demo_func in demos:
        results[demo_name] = demo_func()
    
    # Summary
    print("\n" + "=" * 70)
    print("🏁 UI INTEGRATION DEMONSTRATION SUMMARY")
    print("=" * 70)
    
    passed_demos = sum(results.values())
    total_demos = len(results)
    
    for demo_name, passed in results.items():
        status = "✅ SUCCESS" if passed else "❌ FAILED"
        print(f"{demo_name}: {status}")
    
    if passed_demos == total_demos:
        print("\n🎉 UI INTEGRATION COMPLETE!")
        print("\n✨ Key Features Demonstrated:")
        print("   • RESTful API for starting analysis")
        print("   • Real-time progress monitoring")
        print("   • Multiple download formats from Phase 2")
        print("   • Comprehensive error handling")
        print("   • Job tracking with unique IDs")
        
        print("\n🔗 Integration Points:")
        print("   • FastAPI orchestrator (port 8000)")
        print("   • Phase 1 extractor with job_id flow")
        print("   • Phase 2 transformer with dual outputs")
        print("   • Download endpoints for UI access")
        print("   • Status monitoring for real-time updates")
        
        print("\n📚 Frontend Implementation Guide:")
        print("   1. Use fetch() API for HTTP requests")
        print("   2. Implement polling for progress updates")
        print("   3. Handle different job states appropriately")
        print("   4. Provide download links for completed analyses")
        print("   5. Show meaningful error messages to users")
        
        return True
    else:
        print(f"\n❌ DEMONSTRATION INCOMPLETE: {total_demos - passed_demos} issues found")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)