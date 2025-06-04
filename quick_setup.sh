#!/bin/bash
echo "🚀 Setting up Axis AI..."

VENV_PATH="/home/chris-litkei/venvs/axis"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_PATH" ]; then
    echo "📦 Creating virtual environment at $VENV_PATH..."
    mkdir -p "$(dirname "$VENV_PATH")"
    python3 -m venv "$VENV_PATH"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source "$VENV_PATH/bin/activate"

# Upgrade pip
echo "📈 Upgrading pip..."
python -m pip install --upgrade pip

# Install requirements
echo "📋 Installing requirements..."
pip install -r requirements.txt

# Test imports
echo "🔍 Testing imports..."
python test_imports.py

echo "✅ Setup complete! Run: ./start_axis.sh" 