#!/bin/bash

echo "🚀 Quick Install: Code Llama 13B for AXIS AI"
echo "============================================="

# Basic Python version check
python3 -c "
import sys
print(f'📍 Python version: {sys.version_info.major}.{sys.version_info.minor}')
if sys.version_info < (3, 9):
    print('❌ Python 3.9+ required')
    exit(1)
print('✅ Python version OK')
"
if [ $? -ne 0 ]; then
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "axis_env" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv axis_env
fi

echo "🔧 Activating virtual environment..."
source axis_env/bin/activate

# Check for NVIDIA GPU
echo "🔍 Checking for GPU..."
if command -v nvidia-smi &> /dev/null; then
    echo "✅ NVIDIA GPU detected"
    CUDA_AVAILABLE=true
else
    echo "⚠️  No NVIDIA GPU - will use CPU mode"
    CUDA_AVAILABLE=false
fi

# Install PyTorch
echo "📦 Installing PyTorch..."
if [ "$CUDA_AVAILABLE" = true ]; then
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    echo "📦 Installing GPU acceleration (bitsandbytes)..."
    pip install bitsandbytes
else
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

# Install Transformers and dependencies
echo "📦 Installing Transformers..."
pip install transformers accelerate
pip install sentencepiece protobuf safetensors huggingface-hub

# Install AXIS AI requirements
echo "📦 Installing AXIS AI dependencies..."
pip install -r requirements.txt

# Test installation
echo "🧪 Testing installation..."
python3 -c "
import torch
from transformers import AutoTokenizer
print('✅ PyTorch:', torch.__version__)
print('✅ CUDA available:', torch.cuda.is_available())
if torch.cuda.is_available():
    try:
        print('✅ GPU:', torch.cuda.get_device_name())
        print('✅ GPU Memory:', f'{torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB')
    except:
        print('⚠️  GPU detected but properties unavailable')
print('✅ Transformers ready')
print('📝 Code Llama model (~25GB) will download on first use')
"

# Create optimized startup script
echo "📝 Creating startup script..."
cat > start_with_code_llama.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting AXIS AI with Code Llama 13B"
echo "======================================"

# Activate virtual environment
source axis_env/bin/activate

# Set environment variables
export PYTORCH_CUDA_ALLOC_CONF="max_split_size_mb:512"
export TRANSFORMERS_CACHE="./models/cache"
export HF_HOME="./models/cache"

# Create cache directory
mkdir -p ./models/cache

echo "🎯 Code Llama Features:"
echo "  ✅ Specialized for programming tasks"
echo "  ✅ Python, JavaScript, C++, and 20+ languages"
echo "  ✅ Code generation, debugging, optimization"
echo "  ✅ Memory learning from interactions"
echo "  ✅ Works completely offline"
echo ""
echo "🌐 Visit: http://localhost:8000"
echo "💻 Try: 'Write a Python function to sort a list'"
echo ""

python main.py
EOF

chmod +x start_with_code_llama.sh

echo ""
echo "🎉 Installation Complete!"
echo ""
echo "🚀 Next Steps:"
echo "1. Accept the license: https://huggingface.co/meta-llama/CodeLlama-13b-hf"
echo "2. Start AXIS AI: ./start_with_code_llama.sh"
echo "3. First run will download Code Llama (~25GB, takes 2-5 min)"
echo ""
echo "💡 Perfect for:"
echo "  - Writing and debugging code"
echo "  - Code explanations and reviews"
echo "  - Algorithm implementations"
echo "  - Refactoring and optimization" 