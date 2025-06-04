#!/bin/bash
# Simple test runner for AXIS AI

echo "🔍 Testing AXIS AI System..."

# Activate virtual environment if it exists
if [ -d "axis_env" ]; then
    echo "🔧 Activating virtual environment..."
    source axis_env/bin/activate
fi

# Run the test
echo "🧪 Running quick test..."
python3 quick_test.py

echo "✅ Test completed!" 