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
