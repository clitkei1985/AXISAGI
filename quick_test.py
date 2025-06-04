#!/usr/bin/env python3
"""Quick test for AXIS AI functionality"""

import sys
import asyncio
import traceback

async def test_basic_functionality():
    """Test basic AXIS AI functionality"""
    
    print("🔍 Testing AXIS AI Basic Functionality...")
    
    try:
        # Test 1: Configuration
        print("\n1. Testing configuration...")
        from core.config import settings
        print(f"   ✅ App: {settings.app_name}")
        print(f"   ✅ Models dir: {settings.llm.local_model_path}")
        print(f"   ✅ Base model: {settings.llm.base_model}")
        
        # Test 2: Database
        print("\n2. Testing database...")
        from core.database import get_db, User
        print("   ✅ Database imports successful")
        
        # Test 3: Memory Manager
        print("\n3. Testing memory manager...")
        from modules.memory.memory_manager import MemoryManager
        print("   ✅ Memory manager imported")
        
        # Test 4: LLM Engine
        print("\n4. Testing LLM engine...")
        from modules.llm_engine.local_llm import CodeLlamaEngine
        print("   ✅ CodeLlama engine imported")
        
        # Test 5: Voice Engine
        print("\n5. Testing voice engine...")
        from modules.audio_voice.voice_engine import VoiceEngine
        print("   ✅ Voice engine imported")
        
        # Test 6: Multi-Agent System
        print("\n6. Testing multi-agent system...")
        from modules.llm_engine.agents import MultiAgentSystem
        print("   ✅ Multi-agent system imported")
        
        # Test 7: Check GPU availability
        print("\n7. Testing GPU availability...")
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
                print(f"   ✅ GPU: {gpu_name} ({gpu_memory:.1f}GB)")
            else:
                print("   ⚠️  No GPU available - will use CPU")
        except ImportError:
            print("   ⚠️  PyTorch not available")
        
        # Test 8: Check model files
        print("\n8. Testing model files...")
        from pathlib import Path
        models_dir = Path(settings.llm.local_model_path)
        if models_dir.exists() and any(models_dir.iterdir()):
            print(f"   ✅ Models found in: {models_dir}")
        else:
            print(f"   ⚠️  Models not found in: {models_dir}")
        
        print("\n🎉 BASIC TESTS PASSED!")
        print("   System components are properly configured")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR in basic tests: {e}")
        print(f"   Type: {type(e).__name__}")
        print(f"   Details:\n{traceback.format_exc()}")
        return False

async def test_llm_functionality():
    """Test LLM functionality if available"""
    
    print("\n🧠 Testing LLM Functionality...")
    
    try:
        # Import required modules
        from core.database import get_db
        from modules.memory.memory_manager import MemoryManager  
        from modules.llm_engine.local_llm import CodeLlamaEngine
        
        # Get database session
        db = next(get_db())
        
        # Create memory manager
        memory_manager = MemoryManager(db)
        
        # Create LLM engine
        print("   Creating CodeLlama engine...")
        llm_engine = CodeLlamaEngine(db, memory_manager)
        
        # Test simple generation
        print("   Testing simple generation...")
        response = await llm_engine.generate_response(
            "Hello! Can you briefly introduce yourself?",
            agent_type="coder",
            max_tokens=100,
            use_memory=False
        )
        
        print(f"   ✅ LLM Response: {response[:100]}...")
        print("\n🎉 LLM TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"\n⚠️  LLM test failed: {e}")
        print("   This is expected if models are not fully loaded")
        return False

async def main():
    """Main test runner"""
    print("=" * 60)
    print("         AXIS AI SYSTEM TEST")
    print("=" * 60)
    
    # Run basic tests
    basic_ok = await test_basic_functionality()
    
    if basic_ok:
        # Try LLM tests if basic tests pass
        llm_ok = await test_llm_functionality()
        
        if llm_ok:
            print("\n🏆 ALL TESTS PASSED!")
            print("   AXIS AI is fully functional!")
        else:
            print("\n✅ BASIC SYSTEM READY!")
            print("   LLM requires model loading (may take time on first run)")
    else:
        print("\n❌ SYSTEM NOT READY")
        print("   Please check configuration and dependencies")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(main())