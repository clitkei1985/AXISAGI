#!/bin/bash

echo "Testing chat functionality..."

# Get token
echo "1. Getting auth token..."
TOKEN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=1609")

TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')

if [ "$TOKEN" = "null" ]; then
    echo "❌ Login failed"
    exit 1
fi

echo "✅ Login successful"

# Test chat
echo "2. Testing chat..."
CHAT_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/chat/send" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"content": "Hello, tell me a joke!"}')

echo "Chat response:"
echo $CHAT_RESPONSE | jq '.'

if echo $CHAT_RESPONSE | jq -e '.response' > /dev/null; then
    echo "✅ Chat working!"
else
    echo "❌ Chat failed"
fi 