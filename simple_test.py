#!/usr/bin/env python3
"""Simple configuration test"""

try:
    print("Testing configuration loading...")
    from core.config import settings
    print(f"✅ Config loaded successfully!")
    print(f"   App: {settings.app_name}")
    print(f"   Debug: {settings.debug}")
    print(f"   Port: {settings.port}")
    print(f"   Models path: {settings.llm.local_model_path}")
    print(f"   Base model: {settings.llm.base_model}")
    print("✅ Configuration test passed!")
    
except Exception as e:
    print(f"❌ Configuration test failed: {e}")
    import traceback
    traceback.print_exc() 