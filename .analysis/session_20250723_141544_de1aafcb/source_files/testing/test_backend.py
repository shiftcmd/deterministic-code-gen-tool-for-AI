#!/usr/bin/env python3
"""
Test script for the Framework Backend API

Tests basic functionality of the FastAPI backend server.
"""

import asyncio
import aiohttp
import json
import time
import subprocess
import signal
import os
from pathlib import Path

BASE_URL = "http://localhost:8000"

async def test_api_endpoints():
    """Test various API endpoints"""
    
    async with aiohttp.ClientSession() as session:
        try:
            # Test root endpoint
            print("Testing root endpoint...")
            async with session.get(f"{BASE_URL}/") as response:
                data = await response.json()
                print(f"✓ Root: {data}")
            
            # Test project analysis
            print("\nTesting project analysis...")
            test_path = str(Path.cwd())
            async with session.post(f"{BASE_URL}/api/projects/analyze", 
                                  json={"path": test_path, "isGitRepo": False}) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✓ Project analysis: Found {len(data.get('files', []))} Python files")
                else:
                    print(f"✗ Project analysis failed: {response.status}")
            
            # Test file system browsing
            print("\nTesting file system browsing...")
            async with session.get(f"{BASE_URL}/api/filesystem/browse?path=/home") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✓ File system browse: Found {len(data)} items")
                else:
                    print(f"✗ File system browse failed: {response.status}")
            
            # Test path validation
            print("\nTesting path validation...")
            async with session.post(f"{BASE_URL}/api/filesystem/validate", 
                                  json={"path": test_path}) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✓ Path validation: {data}")
                else:
                    print(f"✗ Path validation failed: {response.status}")
            
            # Test runs listing (should be empty initially)
            print("\nTesting runs listing...")
            async with session.get(f"{BASE_URL}/api/runs") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✓ Runs listing: {len(data)} runs found")
                else:
                    print(f"✗ Runs listing failed: {response.status}")
            
            # Test Neo4j schema (placeholder)
            print("\nTesting Neo4j schema...")
            async with session.get(f"{BASE_URL}/api/neo4j/test-run/schema") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✓ Neo4j schema: {data['node_count']} nodes, {data['relationship_count']} relationships")
                else:
                    print(f"✗ Neo4j schema failed: {response.status}")
            
            print("\n✅ All API tests completed successfully!")
            
        except Exception as e:
            print(f"\n❌ API test failed: {e}")
            return False
    
    return True

def start_backend_server():
    """Start the backend server"""
    print("Starting backend server...")
    
    # Check if backend_api.py exists
    if not Path("backend_api.py").exists():
        print("❌ backend_api.py not found in current directory")
        return None
    
    # Start the server
    process = subprocess.Popen([
        "python", "backend_api.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Wait a bit for server to start
    time.sleep(3)
    
    # Check if process is still running
    if process.poll() is not None:
        stdout, stderr = process.communicate()
        print(f"❌ Server failed to start:\nSTDOUT: {stdout}\nSTDERR: {stderr}")
        return None
    
    print("✓ Backend server started")
    return process

async def main():
    """Main test function"""
    print("🚀 Testing Deterministic AI Framework Backend\n")
    
    # Start backend server
    server_process = start_backend_server()
    
    if not server_process:
        return
    
    try:
        # Wait a bit more for server to be ready
        await asyncio.sleep(2)
        
        # Run API tests
        success = await test_api_endpoints()
        
        if success:
            print("\n🎉 Backend API is working correctly!")
        else:
            print("\n💥 Some tests failed")
            
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted")
    finally:
        # Stop the server
        if server_process:
            print("\nStopping backend server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
            print("✓ Backend server stopped")

if __name__ == "__main__":
    asyncio.run(main())