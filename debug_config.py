#!/usr/bin/env python3
"""Debug script to check configuration"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Check environment variables before loading config
print("=== Environment Variables Before Config ===")
for key, value in os.environ.items():
    if 'LLM' in key or 'OPENAI' in key:
        print(f"{key}: {value[:30]}...")

from core.config import settings

print("\n=== Environment Variables After Config ===")
for key, value in os.environ.items():
    if 'LLM' in key or 'OPENAI' in key:
        print(f"{key}: {value[:30]}...")

print("\n=== Configuration Debug ===")
print(f"OpenAI API Key configured: {bool(settings.llm.openai_api_key)}")
if settings.llm.openai_api_key:
    print(f"API Key starts with: {settings.llm.openai_api_key[:20]}...")
else:
    print("No API key found")

print(f"Model name: {settings.llm.model_name}")
print(f"Use OpenAI fallback: {settings.llm.use_openai_fallback}")
print(f"Local model path: {settings.llm.local_model_path}")

# Test the LLM engine directly
try:
    from modules.llm_engine.engine import get_llm_engine
    from core.database import SessionLocal
    
    db = SessionLocal()
    llm_engine = get_llm_engine(db)
    print(f"LLM Engine OpenAI client: {bool(llm_engine.openai_client)}")
    print(f"Local models loaded: {list(llm_engine.local_models.keys())}")
    db.close()
except Exception as e:
    print(f"Error testing LLM engine: {e}") 