# 🚀 Manual Installation Guide: Code Llama 13B for AXIS AI

This guide will help you manually install Code Llama 13B when the automated scripts don't work.

## 🔧 Step-by-Step Installation

### **Step 1: Install Python Dependencies**
```bash
# Install Python development tools (required for virtual environments)
sudo apt update
sudo apt install python3-full python3-pip python3-venv python3-dev

# Install build essentials (needed for some Python packages)
sudo apt install build-essential
```

### **Step 2: Create and Activate Virtual Environment**
```bash
# Create virtual environment
python3 -m venv axis_env

# Activate it (Linux/Mac)
source axis_env/bin/activate

# Verify activation (should show axis_env in prompt)
which python
which pip
```

### **Step 3: Upgrade pip and Install Basic Tools**
```bash
# Upgrade pip to latest version
pip install --upgrade pip setuptools wheel

# Install basic tools
pip install packaging
```

### **Step 4: Install PyTorch (GPU or CPU)**

**For GPU (NVIDIA with CUDA):**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**For CPU only:**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### **Step 5: Install Transformers and Dependencies**
```bash
# Install transformers and core dependencies
pip install transformers>=4.41.0
pip install accelerate>=0.20.0
pip install safetensors>=0.4.0
pip install huggingface-hub>=0.20.0

# Install Code Llama specific dependencies
pip install sentencepiece>=0.1.99
pip install protobuf>=3.20.0
pip install tokenizers>=0.15.0

# Install quantization support (GPU only)
pip install bitsandbytes>=0.39.0
```

### **Step 6: Install AXIS AI Requirements**
```bash
# Install remaining requirements
pip install fastapi uvicorn
pip install sqlalchemy alembic
pip install sentence-transformers
pip install faiss-cpu  # or faiss-gpu if you have CUDA
pip install numpy pandas
pip install requests beautifulsoup4
pip install python-multipart
pip install python-jose[cryptography]
pip install passlib[bcrypt]
pip install pydantic pydantic-settings
```

### **Step 7: Test Installation**
```bash
python3 -c "
import torch
from transformers import AutoTokenizer
print('✅ PyTorch version:', torch.__version__)
print('✅ CUDA available:', torch.cuda.is_available())
if torch.cuda.is_available():
    print('✅ GPU:', torch.cuda.get_device_name())
    print('✅ GPU Memory:', f'{torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB')
print('✅ Transformers ready for Code Llama')
print('✅ Installation successful!')
"
```

## 🔐 Hugging Face Setup (Required)

### **Step 1: Accept License Agreement**
1. Visit: https://huggingface.co/meta-llama/CodeLlama-13b-hf
2. Click "Accept" on the license agreement
3. Create account if needed

### **Step 2: Get Access Token (Optional but Recommended)**
1. Go to: https://huggingface.co/settings/tokens
2. Create a new token with "Read" permissions
3. Copy the token

### **Step 3: Login (Optional)**
```bash
pip install huggingface_hub[cli]
huggingface-cli login
# Paste your token when prompted
```

## 🚀 Start AXIS AI with Code Llama

### **Create Startup Script**
```bash
cat > start_code_llama.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting AXIS AI with Code Llama 13B"
echo "======================================"

# Activate virtual environment
source axis_env/bin/activate

# Set environment variables
export PYTORCH_CUDA_ALLOC_CONF="max_split_size_mb:512"
export TRANSFORMERS_CACHE="./models/cache"
export HF_HOME="./models/cache"
export OFFLINE_MODE=true
export PREFER_LOCAL=true

# Create cache directory
mkdir -p ./models/cache

echo "🎯 Code Llama Features Ready:"
echo "  ✅ Code generation & debugging"
echo "  ✅ 20+ programming languages"
echo "  ✅ Memory learning system"
echo "  ✅ Complete offline operation"
echo ""
echo "🌐 Visit: http://localhost:8000"
echo "💻 Try: 'Write a Python function to...'"
echo ""

# Start the server
python main.py
EOF

chmod +x start_code_llama.sh
```

### **Start the System**
```bash
./start_code_llama.sh
```

## 🐛 Troubleshooting

### **Virtual Environment Issues**
```bash
# If activation fails, try:
deactivate  # if in a venv
rm -rf axis_env
python3 -m venv axis_env --clear
source axis_env/bin/activate
```

### **Permission Issues**
```bash
# If you get permission errors:
sudo chown -R $USER:$USER axis_env/
chmod +x axis_env/bin/activate
```

### **CUDA Issues**
```bash
# Check NVIDIA driver
nvidia-smi

# If no CUDA, install CPU version:
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### **Memory Issues**
```bash
# For systems with limited memory:
export PYTORCH_CUDA_ALLOC_CONF="max_split_size_mb:256"
```

### **Download Issues**
```bash
# If model download fails, try:
export HF_HUB_DISABLE_TELEMETRY=1
export HF_HUB_OFFLINE=0
```

## 💡 Quick Commands

**Check if everything is working:**
```bash
source axis_env/bin/activate
python -c "import torch, transformers; print('Ready!')"
```

**Start AXIS AI:**
```bash
source axis_env/bin/activate
python main.py
```

**Check GPU status:**
```bash
nvidia-smi
```

**View logs:**
```bash
tail -f logs/axis.log
```

## 📋 What Happens Next

1. **First startup**: Code Llama model (~25GB) downloads automatically
2. **Download time**: 2-5 minutes depending on internet speed  
3. **GPU memory**: Uses ~6GB VRAM with 4-bit quantization
4. **CPU mode**: Works but much slower (16GB+ RAM recommended)
5. **Subsequent starts**: Much faster (~30-60 seconds)

## 🎯 Testing Code Llama

Once running, try these prompts:

```
"Write a Python function to sort a dictionary by values"
"Debug this JavaScript code: [paste code]"
"Explain how binary search works with code example"
"Create a REST API endpoint using FastAPI"
"Optimize this SQL query for performance"
```

The AI will generate code, explain algorithms, debug issues, and learn from your interactions! 🚀 