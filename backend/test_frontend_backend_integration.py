#!/usr/bin/env python3
"""
Frontend-Backend Integration Test

Tests the integration between the frontend API service and backend endpoints
to ensure proper communication and data flow.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add current directory to Python path  
sys.path.insert(0, str(Path(__file__).parent))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_api_health_endpoints():
    """Test that all health check endpoints work."""
    logger.info("=== Testing API Health Endpoints ===")
    
    try:
        import httpx
        
        # Test main API health
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8080/api/health")
            if response.status_code == 200:
                logger.info("✓ Main API health check passed")
            else:
                logger.error(f"✗ Main API health check failed: {response.status_code}")
                return False
        
        # Test orchestrator health check via main API
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8080/api/orchestrator/health")
            if response.status_code == 200:
                data = response.json()
                if data.get("orchestrator_available"):
                    logger.info("✓ Orchestrator is available via main API")
                else:
                    logger.warning(f"⚠ Orchestrator not available: {data.get('message')}")
            else:
                logger.error(f"✗ Orchestrator health check failed: {response.status_code}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ API health test failed: {e}")
        return False


async def test_orchestrator_integration():
    """Test orchestrator integration."""
    logger.info("=== Testing Orchestrator Integration ===")
    
    try:
        from api.orchestrator_client import orchestrator_client
        
        # Test direct orchestrator health check
        health = await orchestrator_client.health_check()
        if health:
            logger.info("✓ Direct orchestrator health check passed")
        else:
            logger.warning("⚠ Orchestrator service not running on port 8000")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Orchestrator integration test failed: {e}")
        return False


async def test_phase3_endpoints():
    """Test Phase 3 endpoints."""
    logger.info("=== Testing Phase 3 Endpoints ===")
    
    try:
        import httpx
        
        # Test backup endpoints
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8080/v1/backups/")
            if response.status_code == 200:
                logger.info("✓ Backup list endpoint accessible")
            else:
                logger.error(f"✗ Backup list endpoint failed: {response.status_code}")
                return False
        
        # Test upload health endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8080/v1/upload/health") 
            if response.status_code == 200:
                logger.info("✓ Upload health endpoint accessible")
            else:
                logger.error(f"✗ Upload health endpoint failed: {response.status_code}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Phase 3 endpoints test failed: {e}")
        return False


async def test_analysis_endpoints():
    """Test analysis endpoints."""
    logger.info("=== Testing Analysis Endpoints ===")
    
    try:
        import httpx
        
        # Test file system validation
        async with httpx.AsyncClient() as client:
            response = await client.post("http://localhost:8080/api/filesystem/validate", 
                                       json={"path": ".", "include_hidden": False, "python_only": False})
            if response.status_code == 200:
                logger.info("✓ File system validation endpoint accessible")
            else:
                logger.error(f"✗ File system validation failed: {response.status_code}")
                return False
        
        # Test runs endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8080/api/runs")
            if response.status_code == 200:
                logger.info("✓ Runs list endpoint accessible")
            else:
                logger.error(f"✗ Runs list endpoint failed: {response.status_code}")
                return False
                
        return True
        
    except Exception as e:
        logger.error(f"✗ Analysis endpoints test failed: {e}")
        return False


async def main():
    """Run all frontend-backend integration tests."""
    logger.info("Starting Frontend-Backend Integration Tests")
    logger.info("=" * 50)
    
    tests = [
        ("API Health Endpoints", test_api_health_endpoints),
        ("Orchestrator Integration", test_orchestrator_integration),
        ("Phase 3 Endpoints", test_phase3_endpoints),
        ("Analysis Endpoints", test_analysis_endpoints),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))
        
        logger.info("")  # Empty line between tests
    
    # Summary
    logger.info("=" * 50)
    logger.info("Frontend-Backend Integration Test Results:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        logger.info(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All frontend-backend integration tests passed!")
        logger.info("\nIntegration is complete and functional:")
        logger.info("• Main API (port 8080) is accessible")
        logger.info("• Orchestrator integration is working") 
        logger.info("• Phase 3 endpoints are available")
        logger.info("• Analysis pipeline is connected")
        logger.info("\nFrontend can now communicate with the full backend stack!")
    else:
        logger.info("❌ Some integration tests failed")
        logger.info("\nNext steps:")
        logger.info("1. Ensure main API is running: python -m uvicorn api.main:app --host 0.0.0.0 --port 8080")
        logger.info("2. Ensure orchestrator is running: python parser/prod/orchestrator/main.py")
        logger.info("3. Check for any missing dependencies or configuration issues")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(main())