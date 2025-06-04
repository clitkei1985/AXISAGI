#!/bin/bash

echo "🚀 Installing Code Llama 13B for AXIS AI"
echo "========================================"

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "📍 Python version: $python_version"

# Check if Python version is >= 3.9
python3 -c "
import sys
if sys.version_info < (3, 9):
    print('❌ Python 3.9+ required. Current version: {}.{}'.format(sys.version_info.major, sys.version_info.minor))
    exit(1)
else:
    print('✅ Python version check passed')
"

# Check if virtual environment exists
if [ ! -d "axis_env" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv axis_env
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source axis_env/bin/activate

# Check for CUDA
echo "🔍 Checking for CUDA support..."
cuda_available=false

# Try to detect CUDA first
if command -v nvidia-smi &> /dev/null; then
    echo "✅ NVIDIA driver detected"
    # Try to check PyTorch CUDA support if available
    if python3 -c "import torch; print('CUDA available:', torch.cuda.is_available())" 2>/dev/null | grep -q "True"; then
        cuda_available=true
        gpu_name=$(python3 -c "import torch; print(torch.cuda.get_device_name())" 2>/dev/null || echo "Unknown GPU")
        gpu_memory=$(python3 -c "import torch; print(f'{torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB')" 2>/dev/null || echo "Unknown")
        echo "✅ CUDA detected: $gpu_name ($gpu_memory)"
        
        # Check if we have enough GPU memory for Code Llama 13B
        gpu_memory_gb=$(python3 -c "import torch; print(torch.cuda.get_device_properties(0).total_memory / 1e9)" 2>/dev/null || echo "0")
        if python3 -c "exit(0 if float('$gpu_memory_gb') >= 6 else 1)" 2>/dev/null; then
            echo "✅ GPU memory sufficient for Code Llama 13B"
        else
            echo "⚠️  Warning: Code Llama 13B with 4-bit quantization needs ~6GB VRAM. You have ${gpu_memory_gb}GB"
            echo "   Consider using CPU mode or a smaller model variant"
        fi
    else
        echo "🔧 NVIDIA driver found but PyTorch not installed yet - will install CUDA version"
        cuda_available=true
    fi
else
    echo "⚠️  No NVIDIA driver detected - Code Llama will run on CPU (much slower)"
fi

# Install PyTorch with CUDA if available
echo "📦 Installing PyTorch..."
if [ "$cuda_available" = true ]; then
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
else
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

# Install transformers and related packages
echo "📦 Installing Transformers and model dependencies..."
pip install transformers>=4.41.0
pip install accelerate>=0.20.0
pip install sentencepiece>=0.1.99
pip install protobuf>=3.20.0
pip install safetensors>=0.4.0
pip install huggingface-hub>=0.20.0

# Install quantization support if CUDA available
if [ "$cuda_available" = true ]; then
    echo "📦 Installing 4-bit quantization support..."
    pip install bitsandbytes>=0.39.0
fi

# Install other required packages
echo "📦 Installing additional dependencies..."
pip install -r requirements.txt

# Test Code Llama installation
echo "🧪 Testing Code Llama installation..."
python3 -c "
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
print('✅ PyTorch version:', torch.__version__)
print('✅ CUDA available:', torch.cuda.is_available())
if torch.cuda.is_available():
    print('✅ GPU:', torch.cuda.get_device_name())
    print('✅ GPU Memory:', f'{torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB')
print('✅ Transformers ready for Code Llama')
print('📝 Note: Code Llama model will be downloaded on first use (~25GB)')
"

# Setup Hugging Face authentication (optional but recommended)
echo ""
echo "🔐 Hugging Face Authentication (Optional)"
echo "To automatically download Code Llama, you can:"
echo "1. Visit: https://huggingface.co/meta-llama/CodeLlama-13b-hf"
echo "2. Accept the license agreement"
echo "3. Get your access token from: https://huggingface.co/settings/tokens"
echo "4. Run: huggingface-cli login"
echo ""

# Check if user wants to set up HF token now
read -p "Do you want to set up Hugging Face authentication now? [y/N]: " setup_hf
if [[ $setup_hf =~ ^[Yy]$ ]]; then
    echo "Installing Hugging Face CLI..."
    pip install huggingface_hub[cli]
    echo "Please run 'huggingface-cli login' and paste your token"
    huggingface-cli login
fi

# Create startup script specifically for Code Llama
echo "📝 Creating Code Llama startup script..."
cat > start_code_llama.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting AXIS AI with Code Llama 13B"
echo "======================================"

# Activate virtual environment
source axis_env/bin/activate

# Set environment variables for optimal Code Llama performance
export TRANSFORMERS_CACHE="./models/transformers_cache"
export HF_HOME="./models/huggingface_cache" 
export PYTORCH_CUDA_ALLOC_CONF="max_split_size_mb:512"
export OFFLINE_MODE=true
export PREFER_LOCAL=true

# Create cache directories
mkdir -p ./models/transformers_cache
mkdir -p ./models/huggingface_cache

echo "🎯 AXIS AI with Code Llama Features:"
echo "  ✅ Code Llama 13B (specialized for coding)"
echo "  ✅ 4-bit quantization (~6GB VRAM)"
echo "  ✅ Enhanced code generation & debugging" 
echo "  ✅ Memory system with learning"
echo "  ✅ Complete offline operation"
echo ""
echo "📊 Code Llama will auto-load on first coding request"
echo "🌐 Visit: http://localhost:8000"
echo "💻 Perfect for programming tasks!"
echo ""

# Start the server
python main.py
EOF

chmod +x start_code_llama.sh

echo ""
echo "🎉 Code Llama 13B installation complete!"
echo ""
echo "📋 What happens next:"
echo "1. The Code Llama model (~25GB) will download on first use"
echo "2. With 4-bit quantization, it uses ~6GB GPU memory"
echo "3. First model load takes 2-5 minutes depending on internet speed"
echo "4. Subsequent loads are much faster (30-60 seconds)"
echo ""
echo "🚀 To start AXIS AI with Code Llama:"
echo "   ./start_code_llama.sh"
echo ""
echo "💡 Tips:"
echo "  - Code Llama excels at Python, JavaScript, C++, and 20+ languages"
echo "  - It's optimized for code generation, debugging, and explanation"
echo "  - Ask it to 'write a function to...' or 'debug this code:...'"
echo "  - All conversations are saved to memory for continuous learning"
echo ""
echo "🔗 License: Make sure you've accepted the license at:"
echo "   https://huggingface.co/meta-llama/CodeLlama-13b-hf" 