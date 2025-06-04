#!/usr/bin/env python3
import requests
import json

def test_chat():
    base_url = "http://localhost:8000"
    
    with open("test_results.txt", "w") as f:
        f.write("Testing chat functionality...\n")
        
        # Test 1: Login
        f.write("1. Testing login...\n")
        try:
            login_response = requests.post(
                f"{base_url}/api/auth/login",
                data={"username": "admin", "password": "1609"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )
            
            if login_response.status_code == 200:
                token = login_response.json()["access_token"]
                f.write("✓ Login successful\n")
                
                # Test 2: Send message
                f.write("2. Testing chat send...\n")
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                
                chat_response = requests.post(
                    f"{base_url}/api/chat/send",
                    json={"content": "hello", "role": "user"},
                    headers=headers,
                    timeout=10
                )
                
                f.write(f"Chat response status: {chat_response.status_code}\n")
                if chat_response.status_code == 200:
                    f.write("✓ Chat send successful\n")
                    f.write(f"Response: {chat_response.json()}\n")
                else:
                    f.write(f"✗ Chat send failed: {chat_response.text}\n")
                    
            else:
                f.write(f"✗ Login failed: {login_response.text}\n")
        except Exception as e:
            f.write(f"Error: {str(e)}\n")

if __name__ == "__main__":
    test_chat()
    print("Test completed. Check test_results.txt")