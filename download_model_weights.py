#!/usr/bin/env python3
"""
Download missing CodeLlama model weight files
"""

import os
from pathlib import Path
from huggingface_hub import hf_hub_download

def download_model_weights():
    """Download the missing safetensors files for CodeLlama-13b-hf"""
    
    model_path = Path("models/CodeLlama-13b-hf")
    model_path.mkdir(parents=True, exist_ok=True)
    
    # Files we need to download
    weight_files = [
        "model-00001-of-00003.safetensors",
        "model-00002-of-00003.safetensors", 
        "model-00003-of-00003.safetensors"
    ]
    
    print("🚀 Downloading missing CodeLlama-13b-hf model weight files...")
    print("⚠️  This will download ~26GB of data. Please be patient.")
    
    for file in weight_files:
        file_path = model_path / file
        if file_path.exists():
            print(f"✅ {file} already exists")
            continue
            
        print(f"📥 Downloading {file}...")
        try:
            downloaded_path = hf_hub_download(
                repo_id="codellama/CodeLlama-13b-hf",
                filename=file,
                local_dir=str(model_path),
                local_dir_use_symlinks=False
            )
            print(f"✅ Downloaded {file}")
        except Exception as e:
            print(f"❌ Failed to download {file}: {e}")
            return False
    
    print("🎉 All model weight files downloaded successfully!")
    print("🔄 You can now restart the AXIS AI application.")
    return True

if __name__ == "__main__":
    success = download_model_weights()
    if success:
        print("\n✅ Model download complete! Run 'python main.py' to start the application.")
    else:
        print("\n❌ Model download failed. Please check your internet connection and try again.") 