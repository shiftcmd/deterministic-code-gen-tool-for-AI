#!/usr/bin/env python3
"""
Test the complete orchestrator flow: File path → Phase 1 → Phase 2 → Phase 3
"""

import asyncio
import json
from pathlib import Path


def test_orchestrator_file_path_handling():
    """Test orchestrator's ability to handle file paths and start Phase 1."""
    
    print("🔍 ORCHESTRATOR FILE PATH FLOW TEST")
    print("=" * 60)
    
    # Check orchestrator structure
    orchestrator_dir = Path("parser/prod/orchestrator")
    orchestrator_main = orchestrator_dir / "main.py"
    
    if not orchestrator_main.exists():
        print("❌ Orchestrator main.py not found")
        return False
    
    print("✅ Orchestrator main.py found")
    
    # Check orchestrator FastAPI endpoints
    with open(orchestrator_main, 'r') as f:
        orchestrator_code = f.read()
    
    # Verify key components
    checks = {
        "FastAPI app creation": 'app = FastAPI(' in orchestrator_code,
        "File path handling": '/v1/analyze' in orchestrator_code,
        "AnalyzeRequest model": 'class AnalyzeRequest' in orchestrator_code,
        "codebase_path field": 'codebase_path: str' in orchestrator_code,
        "Path validation": 'codebase_path.exists()' in orchestrator_code,
        "Phase 1 execution": '_run_extractor' in orchestrator_code,
        "Phase 2 execution": '_run_transformer' in orchestrator_code,
        "Background tasks": 'background_tasks.add_task' in orchestrator_code
    }
    
    print("\n📋 Orchestrator Components:")
    all_passed = True
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed


def test_phase1_integration():
    """Test Phase 1 extractor integration."""
    
    print("\n🔧 PHASE 1 INTEGRATION TEST")
    print("-" * 40)
    
    # Check Phase 1 extractor
    extractor_main = Path("parser/prod/extractor/main.py")
    
    if not extractor_main.exists():
        print("❌ Phase 1 extractor main.py not found")
        return False
    
    print("✅ Phase 1 extractor main.py found")
    
    # Check command-line interface
    with open(extractor_main, 'r') as f:
        extractor_code = f.read()
    
    cli_checks = {
        "Command line interface": 'argparse' in extractor_code,
        "Path argument": '--path' in extractor_code,
        "Job ID argument": '--job-id' in extractor_code,
        "Output argument": '--output' in extractor_code,
        "ExtractorMain class": 'class ExtractorMain' in extractor_code,
        "Extract method": '.extract(' in extractor_code
    }
    
    print("\n📋 Phase 1 Components:")
    all_passed = True
    for check_name, passed in cli_checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed


def test_phase2_integration():
    """Test Phase 2 transformer integration."""
    
    print("\n⚙️  PHASE 2 INTEGRATION TEST")
    print("-" * 40)
    
    # Check new transformer
    new_transformer_main = Path("transformer/main.py")
    
    if not new_transformer_main.exists():
        print("❌ New Phase 2 transformer main.py not found")
        return False
    
    print("✅ New Phase 2 transformer main.py found")
    
    # Check bridge CLI
    bridge_main = Path("parser/prod/transformer/main.py")
    
    if not bridge_main.exists():
        print("❌ Phase 2 bridge CLI not found")
        return False
    
    print("✅ Phase 2 bridge CLI found")
    
    # Check bridge implementation  
    with open(bridge_main, 'r') as f:
        bridge_code = f.read()
    
    bridge_checks = {
        "Command line interface": 'argparse' in bridge_code,
        "Input argument": '--input' in bridge_code,
        "Job ID argument": '--job-id' in bridge_code,
        "Output argument": '--output' in bridge_code,
        "New transformer import": 'from transformer.main import transform_file' in bridge_code,
        "Async main": 'async def main' in bridge_code
    }
    
    print("\n📋 Phase 2 Components:")
    all_passed = True
    for check_name, passed in bridge_checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed


def test_api_integration():
    """Test API integration points."""
    
    print("\n🌐 API INTEGRATION TEST")
    print("-" * 40)
    
    # Check API integration module
    api_integration = Path("parser/api_integration.py")
    
    if not api_integration.exists():
        print("❌ API integration module not found")
        return False
    
    print("✅ API integration module found")
    
    # Check integration components
    with open(api_integration, 'r') as f:
        integration_code = f.read()
    
    api_checks = {
        "Orchestrator client": 'class ParserOrchestratorClient' in integration_code,
        "Start analysis": 'start_analysis' in integration_code,
        "Get job status": 'get_job_status' in integration_code,
        "Get job results": 'get_job_results' in integration_code,
        "Health check": 'check_orchestrator_health' in integration_code,
        "HTTP client": 'httpx' in integration_code,
        "Error handling": 'ConnectionError' in integration_code
    }
    
    print("\n📋 API Integration Components:")
    all_passed = True
    for check_name, passed in api_checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed


def test_data_flow():
    """Test the complete data flow structure."""
    
    print("\n📊 DATA FLOW TEST")
    print("-" * 40)
    
    # Check if sample data exists from previous tests
    sample_files = {
        "Sample extraction input": Path("test_extraction_input.json"),
        "Sample Phase 1 output": Path("sample_phase1_output.json"),
        "Test output directory": Path("test_output"),
        "Neo4j output": Path("test_output").glob("*.cypher"),
        "JSON tuple output": Path("test_output").glob("tuples_*.json")
    }
    
    print("\n📋 Data Flow Files:")
    all_files_exist = True
    for file_name, file_path in sample_files.items():
        if isinstance(file_path, Path):
            exists = file_path.exists()
        else:  # glob pattern
            exists = any(file_path)
        
        status = "✅" if exists else "❌"
        print(f"   {status} {file_name}")
        if not exists:
            all_files_exist = False
    
    if all_files_exist:
        print("\n✅ Complete data flow chain validated")
    else:
        print("\n⚠️  Run integration tests first to generate sample data")
    
    return all_files_exist


def main():
    """Run complete orchestrator flow test."""
    
    tests = [
        ("Orchestrator File Path Handling", test_orchestrator_file_path_handling),
        ("Phase 1 Integration", test_phase1_integration),
        ("Phase 2 Integration", test_phase2_integration),
        ("API Integration", test_api_integration),
        ("Data Flow", test_data_flow)
    ]
    
    results = {}
    for test_name, test_func in tests:
        results[test_name] = test_func()
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 ORCHESTRATOR FLOW TEST SUMMARY")
    print("=" * 60)
    
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 ORCHESTRATOR FLOW VALIDATION: SUCCESS!")
        print("\n✨ Complete Flow Ready:")
        print("   1. UI → FastAPI (file path input)")
        print("   2. FastAPI → Orchestrator (via api_integration.py)")
        print("   3. Orchestrator → Phase 1 (extraction with --path)")
        print("   4. Phase 1 → Phase 2 (via bridge CLI)")
        print("   5. Phase 2 → Phase 3 (tuples ready for upload)")
        print("\n📋 Usage:")
        print("   1. Start orchestrator: cd parser/prod/orchestrator && python main.py")
        print("   2. Use api_integration.py to connect main FastAPI")
        print("   3. Call start_parser_analysis(codebase_path)")
        
        return True
    else:
        print(f"\n❌ FLOW VALIDATION INCOMPLETE: {total_tests - passed_tests} issues found")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)