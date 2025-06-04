#!/usr/bin/env python3
"""Simple test script for chat functionality"""

import requests
import json

# Test login first
print("1. Testing login...")
login_data = {
    "username": "admin",
    "password": "1609"
}

response = requests.post(
    "http://localhost:8000/api/auth/login", 
    data=login_data,
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)

if response.status_code != 200:
    print(f"Login failed: {response.text}")
    exit(1)

token_data = response.json()
access_token = token_data["access_token"]
print("✅ Login successful")

# Test chat
print("2. Testing chat...")
chat_data = {
    "content": "Hello, can you tell me a joke?"
}

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

response = requests.post(
    "http://localhost:8000/api/chat/send",
    json=chat_data,
    headers=headers
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"Chat Response: {result.get('response', 'No response field')}")
    print("✅ Chat working!")
else:
    print(f"Chat failed: {response.text}") 