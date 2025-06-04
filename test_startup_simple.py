#!/usr/bin/env python3
"""Simple startup test for AXIS AI"""

import sys
import os
import traceback

def test_config():
    """Test configuration loading"""
    print("1. Testing configuration...")
    try:
        from core.config import settings
        print(f"   ✅ Config loaded: {settings.app_name}")
        print(f"   ✅ Port: {settings.port}")
        print(f"   ✅ Debug: {settings.debug}")
        return True
    except Exception as e:
        print(f"   ❌ Config failed: {e}")
        return False

def test_app_creation():
    """Test FastAPI app creation"""
    print("2. Testing app creation...")
    try:
        from core.app_config import create_app
        app = create_app()
        print(f"   ✅ FastAPI app created successfully")
        return True
    except Exception as e:
        print(f"   ❌ App creation failed: {e}")
        return False

def test_database():
    """Test database connection"""
    print("3. Testing database...")
    try:
        from core.database import get_db, engine
        # Simple connection test
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        print(f"   ✅ Database connection successful")
        return True
    except Exception as e:
        print(f"   ❌ Database test failed: {e}")
        return False

def test_routes():
    """Test route imports"""
    print("4. Testing route imports...")
    try:
        from core.app_routes import include_routers
        print(f"   ✅ Route imports successful")
        return True
    except Exception as e:
        print(f"   ❌ Route imports failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("AXIS AI STARTUP TEST")
    print("=" * 50)
    
    tests = [
        test_config,
        test_app_creation, 
        test_database,
        test_routes
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"   ❌ Test error: {e}")
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! AXIS AI is ready to start!")
        print("\nTo start the server:")
        print("   python main.py")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    print("=" * 50)

if __name__ == "__main__":
    main() 