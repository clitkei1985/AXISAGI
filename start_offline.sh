#!/bin/bash

echo "🚀 Starting AXIS AI with LLaMA 3 13B Offline Intelligence"
echo "=========================================================="

# Check if virtual environment exists
if [ ! -d "axis_env" ]; then
    echo "⚠️  Virtual environment not found. Creating one..."
    python3 -m venv axis_env
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source axis_env/bin/activate

# Install/update requirements
echo "📦 Installing requirements..."
pip install -q -r requirements.txt
pip install -q requests beautifulsoup4 bitsandbytes accelerate

# Check for CUDA
if python -c "import torch; print(torch.cuda.is_available())" 2>/dev/null | grep -q "True"; then
    echo "🚀 CUDA detected - LLaMA 3 13B will use GPU acceleration"
else
    echo "⚠️  No CUDA detected - LLaMA 3 13B will run on CPU (slower)"
fi

# Set environment variables for offline mode
export OFFLINE_MODE=true
export PREFER_LOCAL=true

echo ""
echo "🎯 AXIS AI Features Ready:"
echo "  ✅ LLaMA 3 13B (4-bit quantized)"  
echo "  ✅ Memory system with auto-learning"
echo "  ✅ Intelligent web search & research"
echo "  ✅ Complete offline operation"
echo "  ✅ Continuous learning from interactions"
echo ""
echo "📊 System will auto-load LLaMA 3 13B on first request"
echo "🌐 Visit: http://localhost:8000"
echo "📝 Memory tab will show stored conversations"
echo ""
echo "Starting server..."

# Start the server
python main.py 