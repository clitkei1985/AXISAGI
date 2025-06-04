#!/bin/bash
# AXIS AI Startup Script

echo "🚀 Starting AXIS AI System..."

# Check if we need to run setup first
if [ ! -d "models/CodeLlama-13b-hf" ]; then
    echo "⚙️  Models not found. Running setup first..."
    python setup_codellama.py
fi

# Check for environment file
if [ ! -f ".env" ]; then
    echo "📝 Creating environment file..."
    python setup_codellama.py configure_environment
fi

# Activate virtual environment if it exists
if [ -d "axis_env" ]; then
    echo "🔧 Activating virtual environment..."
    source axis_env/bin/activate
fi

# Start the main application
echo "🚀 Starting AXIS AI..."
python main.py 