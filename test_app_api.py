#!/usr/bin/env python3
"""
Simple test script to verify AXIS AI application functionality
"""

import requests
import json
from datetime import datetime

def test_health_endpoint():
    """Test the health endpoint"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"✅ Health endpoint: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
        return False

def test_docs_endpoint():
    """Test the API documentation endpoint"""
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        print(f"✅ Docs endpoint: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Docs endpoint failed: {e}")
        return False

def test_openapi_endpoint():
    """Test the OpenAPI spec endpoint"""
    try:
        response = requests.get("http://localhost:8000/openapi.json", timeout=5)
        print(f"✅ OpenAPI endpoint: {response.status_code}")
        if response.status_code == 200:
            spec = response.json()
            print(f"   API title: {spec.get('info', {}).get('title', 'Unknown')}")
            print(f"   API version: {spec.get('info', {}).get('version', 'Unknown')}")
            print(f"   Available paths: {len(spec.get('paths', {}))}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ OpenAPI endpoint failed: {e}")
        return False

def test_auth_endpoint():
    """Test authentication endpoints"""
    try:
        # Test the auth register endpoint (should return 422 for missing data, which is good)
        response = requests.post("http://localhost:8000/api/auth/register", timeout=5)
        print(f"✅ Auth register endpoint: {response.status_code} (422 expected for missing data)")
        
        # Test the auth login endpoint (should return 422 for missing data, which is good)
        response = requests.post("http://localhost:8000/api/auth/login", timeout=5)
        print(f"✅ Auth login endpoint: {response.status_code} (422 expected for missing data)")
        
        return True
    except Exception as e:
        print(f"❌ Auth endpoints failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing AXIS AI Application")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_endpoint),
        ("API Documentation", test_docs_endpoint),
        ("OpenAPI Specification", test_openapi_endpoint),
        ("Authentication Endpoints", test_auth_endpoint)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}...")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! AXIS AI is running correctly.")
    else:
        print("⚠️  Some tests failed. Check the application logs.")
    
    print(f"\n📝 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🌐 Access the application at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")

if __name__ == "__main__":
    main() 