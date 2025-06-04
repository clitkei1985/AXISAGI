#!/usr/bin/env python3
"""Test script to check if the application starts correctly"""

import sys

print("🔍 Testing Axis AI startup...")

try:
    print("1. Testing config import...")
    from core.config import settings
    print(f"   ✅ Config loaded: {settings.app_name}")
    
    print("2. Testing database import...")
    from core.database import get_db, User
    print("   ✅ Database models loaded")
    
    print("3. Testing security import...")
    from core.security import create_access_token
    print("   ✅ Security functions loaded")
    
    print("4. Testing app creation...")
    from core.app_config import create_app
    app = create_app()
    print("   ✅ FastAPI app created")
    
    print("5. Testing router imports...")
    from core.app_routes import include_routers
    print("   ✅ Router imports successful")
    
    print("6. Testing complete app setup...")
    include_routers(app)
    print("   ✅ All routers included successfully")
    
    print("\n🎉 SUCCESS! Application is ready to start!")
    print("   Run: /home/chris-litkei/venvs/axis/bin/python main.py")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print(f"   Type: {type(e).__name__}")
    import traceback
    print(f"   Details:\n{traceback.format_exc()}")
    sys.exit(1) 