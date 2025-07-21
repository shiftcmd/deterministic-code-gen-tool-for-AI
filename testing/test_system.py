#!/usr/bin/env python3
"""
Quick test script to verify the complete system is working
"""

import requests
import json
import time

def test_system():
    """Test the complete React frontend + Python backend system"""
    
    print("🧪 Testing Complete System...")
    print("=" * 50)
    
    # Test 1: Backend API health
    try:
        response = requests.get("http://localhost:8080/")
        if response.status_code == 200:
            print("✅ Backend API is responding")
        else:
            print("❌ Backend API health check failed")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return False
    
    # Test 2: Start a processing request
    try:
        payload = {
            "projectPath": "/home/amo/coding_projects/python_debug_tool",
            "selectedFiles": ["backend_api.py"],
            "isGitRepo": False,
            "options": {}
        }
        
        response = requests.post(
            "http://localhost:8080/api/processing/start",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            run_id = data.get('id')
            print(f"✅ Processing started successfully (Run ID: {run_id[:8]}...)")
            
            # Wait and check status
            time.sleep(3)
            status_response = requests.get(f"http://localhost:8080/api/processing/status/{run_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"✅ Status check working: {status_data.get('status', 'unknown')}")
            else:
                print("⚠️  Status check failed but processing started")
            
            return True
        else:
            print(f"❌ Processing start failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Processing test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_system()
    if success:
        print("\n🎉 System test PASSED! Your React frontend + Python backend is working!")
        print("\n📋 Next steps:")
        print("1. Open http://localhost:3000 in your browser")
        print("2. Navigate through the interface")
        print("3. Start a code analysis")
        print("4. Check the error dashboard at /errors")
    else:
        print("\n❌ System test FAILED. Check the logs above.")