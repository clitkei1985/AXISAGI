#!/usr/bin/env python3
"""Test script to check if all required imports work"""

print("🔍 Testing imports...")

try:
    import pydantic
    print(f"✅ pydantic version: {pydantic.__version__}")
except ImportError as e:
    print(f"❌ pydantic import failed: {e}")

try:
    from pydantic_settings import BaseSettings
    print("✅ pydantic_settings.BaseSettings imported successfully")
except ImportError as e:
    print(f"❌ pydantic_settings import failed: {e}")
    print("   Run: pip install pydantic-settings")

try:
    from pydantic import Field
    print("✅ pydantic.Field imported successfully")
except ImportError as e:
    print(f"❌ pydantic.Field import failed: {e}")

try:
    from core.config import settings
    print("✅ config.py imports work correctly")
    print(f"   App name: {settings.app_name}")
except Exception as e:
    print(f"❌ config.py import failed: {e}")

print("\n🎯 Run this script with: python3 test_imports.py") 