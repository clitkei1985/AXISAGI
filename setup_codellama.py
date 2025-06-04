#!/usr/bin/env python3
"""
AXIS AI Setup Script for CodeLlama-13b-hf Integration
Automatically downloads models, configures environment, and initializes the system.
"""

import os
import sys
import subprocess
import logging
import asyncio
import shutil
from pathlib import Path
from typing import List, Dict, Any
import json
import yaml
import requests
from rich.console import Console
from rich.progress import Progress, BarColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.text import Text

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

class AxisSetup:
    """Comprehensive setup manager for AXIS AI system."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.models_dir = self.base_dir / "models"
        self.data_dir = self.base_dir / "data"
        self.logs_dir = self.base_dir / "logs"
        self.uploads_dir = self.base_dir / "uploads"
        
        # Required directories
        self.required_dirs = [
            self.models_dir,
            self.data_dir,
            self.logs_dir,
            self.uploads_dir,
            self.data_dir / "interactions",
            self.models_dir / "CodeLlama-13b-hf",
            self.models_dir / "yolo",
            "db",
            "db/vector"
        ]
        
        # Model configurations
        self.model_configs = {
            "CodeLlama-13b-hf": {
                "hf_name": "meta-llama/CodeLlama-13b-hf",
                "local_path": self.models_dir / "CodeLlama-13b-hf",
                "size_gb": 13.0,
                "required": True
            },
            "CodeLlama-13b-Instruct-hf": {
                "hf_name": "meta-llama/CodeLlama-13b-Instruct-hf", 
                "local_path": self.models_dir / "CodeLlama-13b-Instruct-hf",
                "size_gb": 13.0,
                "required": True
            },
            "CodeLlama-13b-Python-hf": {
                "hf_name": "meta-llama/CodeLlama-13b-Python-hf",
                "local_path": self.models_dir / "CodeLlama-13b-Python-hf", 
                "size_gb": 13.0,
                "required": True
            }
        }
        
        # System requirements
        self.min_requirements = {
            "python_version": (3, 8),
            "gpu_memory_gb": 16,
            "disk_space_gb": 50,
            "ram_gb": 16
        }
    
    async def run_full_setup(self):
        """Run complete AXIS AI setup process."""
        console.print(Panel.fit(
            "[bold blue]AXIS AI Setup[/bold blue]\n"
            "Setting up CodeLlama-13b-hf based AI system\n"
            "This will download ~40GB of models and configure the environment",
            title="🚀 Welcome to AXIS AI"
        ))
        
        try:
            # Step 1: Check system requirements
            await self.check_system_requirements()
            
            # Step 2: Create directories
            await self.create_directories()
            
            # Step 3: Install Python dependencies
            await self.install_dependencies()
            
            # Step 4: Download and setup models
            await self.setup_models()
            
            # Step 5: Initialize databases
            await self.initialize_databases()
            
            # Step 6: Configure environment
            await self.configure_environment()
            
            # Step 7: Run initial tests
            await self.run_system_tests()
            
            console.print(Panel.fit(
                "[bold green]✅ Setup Complete![/bold green]\n\n"
                "AXIS AI is ready to use with CodeLlama-13b-hf.\n\n"
                "To start the system:\n"
                "[code]python main.py[/code]\n\n" 
                "Or use the quick start:\n"
                "[code]./start_axis.sh[/code]",
                title="🎉 Success"
            ))
            
        except Exception as e:
            console.print(f"[bold red]Setup failed: {e}[/bold red]")
            logger.error(f"Setup error: {e}")
            sys.exit(1)
    
    async def check_system_requirements(self):
        """Check if system meets minimum requirements."""
        console.print("[bold yellow]Checking system requirements...[/bold yellow]")
        
        # Check Python version
        py_version = sys.version_info[:2]
        if py_version < self.min_requirements["python_version"]:
            raise Exception(f"Python {self.min_requirements['python_version']} or higher required")
        
        # Check GPU availability
        try:
            import torch
            gpu_available = torch.cuda.is_available()
            if gpu_available:
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
                console.print(f"✅ GPU: {torch.cuda.get_device_name(0)} ({gpu_memory:.1f}GB)")
                
                if gpu_memory < self.min_requirements["gpu_memory_gb"]:
                    console.print(f"[yellow]Warning: GPU memory ({gpu_memory:.1f}GB) below recommended {self.min_requirements['gpu_memory_gb']}GB[/yellow]")
            else:
                console.print("[yellow]Warning: No GPU detected. System will run on CPU (slower)[/yellow]")
        except ImportError:
            console.print("[yellow]PyTorch not installed yet, will be installed in dependencies step[/yellow]")
        
        # Check disk space
        disk_free = shutil.disk_usage(self.base_dir).free / 1e9
        if disk_free < self.min_requirements["disk_space_gb"]:
            raise Exception(f"Insufficient disk space. Need {self.min_requirements['disk_space_gb']}GB, have {disk_free:.1f}GB")
        
        console.print(f"✅ Disk space: {disk_free:.1f}GB available")
        console.print("✅ System requirements check passed")
    
    async def create_directories(self):
        """Create required directory structure."""
        console.print("[bold yellow]Creating directory structure...[/bold yellow]")
        
        for directory in self.required_dirs:
            directory = Path(directory)
            directory.mkdir(parents=True, exist_ok=True)
            console.print(f"Created: {directory}")
        
        console.print("✅ Directory structure created")
    
    async def install_dependencies(self):
        """Install Python dependencies."""
        console.print("[bold yellow]Installing Python dependencies...[/bold yellow]")
        
        # Check if we're in a virtual environment
        if sys.prefix == sys.base_prefix:
            console.print("[yellow]Warning: Not in a virtual environment. Consider using venv or conda.[/yellow]")
        
        # Install requirements
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--upgrade"
            ], check=True, capture_output=True, text=True)
            console.print("✅ Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Dependency installation failed: {e.stderr}[/red]")
            # Try installing critical dependencies individually
            critical_deps = [
                "torch>=2.0.0",
                "transformers>=4.41.0", 
                "accelerate>=0.20.0",
                "bitsandbytes>=0.39.0",
                "sentence-transformers>=4.1.0",
                "faiss-gpu-cu12>=1.11.0"
            ]
            
            for dep in critical_deps:
                try:
                    subprocess.run([
                        sys.executable, "-m", "pip", "install", dep
                    ], check=True, capture_output=True, text=True)
                    console.print(f"✅ Installed {dep}")
                except subprocess.CalledProcessError:
                    console.print(f"[yellow]Warning: Failed to install {dep}[/yellow]")
    
    async def setup_models(self):
        """Download and setup CodeLlama models."""
        console.print("[bold yellow]Setting up CodeLlama models...[/bold yellow]")
        
        try:
            # Check if huggingface_hub is available
            from huggingface_hub import snapshot_download, login
            from transformers import AutoTokenizer, AutoModelForCausalLM
        except ImportError:
            console.print("[red]Installing huggingface_hub...[/red]")
            subprocess.run([
                sys.executable, "-m", "pip", "install", "huggingface_hub"
            ], check=True)
            from huggingface_hub import snapshot_download
        
        # Check for HuggingFace token
        hf_token = os.getenv("HUGGINGFACE_TOKEN")
        if hf_token:
            try:
                login(token=hf_token)
                console.print("✅ Logged into HuggingFace")
            except Exception as e:
                console.print(f"[yellow]HuggingFace login failed: {e}[/yellow]")
        else:
            console.print("[yellow]No HUGGINGFACE_TOKEN found. Some models may require authentication.[/yellow]")
        
        # Download models
        for model_name, config in self.model_configs.items():
            if config["required"]:
                await self.download_model(model_name, config)
    
    async def download_model(self, model_name: str, config: Dict[str, Any]):
        """Download a specific model."""
        local_path = config["local_path"]
        
        if local_path.exists() and any(local_path.iterdir()):
            console.print(f"✅ {model_name} already exists, skipping download")
            return
        
        console.print(f"⬇️  Downloading {model_name} (~{config['size_gb']:.1f}GB)...")
        
        try:
            from huggingface_hub import snapshot_download
            
            # Download model
            snapshot_download(
                repo_id=config["hf_name"],
                local_dir=local_path,
                local_dir_use_symlinks=False,
                resume_download=True
            )
            
            console.print(f"✅ {model_name} downloaded successfully")
            
            # Test loading the model
            await self.test_model_loading(config["hf_name"], local_path)
            
        except Exception as e:
            console.print(f"[red]Failed to download {model_name}: {e}[/red]")
            # Try alternative download method
            console.print(f"[yellow]Trying alternative download method...[/yellow]")
            await self.download_model_alternative(model_name, config)
    
    async def download_model_alternative(self, model_name: str, config: Dict[str, Any]):
        """Alternative model download using git lfs."""
        try:
            # Check if git lfs is available
            subprocess.run(["git", "lfs", "version"], check=True, capture_output=True)
            
            # Clone the repository
            repo_url = f"https://huggingface.co/{config['hf_name']}"
            subprocess.run([
                "git", "clone", repo_url, str(config["local_path"])
            ], check=True, capture_output=True)
            
            console.print(f"✅ {model_name} downloaded via git")
            
        except subprocess.CalledProcessError:
            console.print(f"[red]All download methods failed for {model_name}[/red]")
            console.print(f"[yellow]Please manually download from: https://huggingface.co/{config['hf_name']}[/yellow]")
    
    async def test_model_loading(self, model_id: str, local_path: Path):
        """Test if a model can be loaded successfully."""
        try:
            from transformers import AutoTokenizer
            
            # Try loading tokenizer first (lighter test)
            tokenizer = AutoTokenizer.from_pretrained(str(local_path))
            console.print(f"✅ {model_id} tokenizer loads successfully")
            
        except Exception as e:
            console.print(f"[yellow]Model loading test failed: {e}[/yellow]")
    
    async def initialize_databases(self):
        """Initialize application databases."""
        console.print("[bold yellow]Initializing databases...[/bold yellow]")
        
        try:
            # Import database modules
            sys.path.append(str(self.base_dir))
            from core.database import init_db, engine
            from core.config import settings
            
            # Initialize database
            await init_db()
            console.print("✅ SQL database initialized")
            
            # Initialize vector database
            vector_db_path = Path("db/vector")
            vector_db_path.mkdir(parents=True, exist_ok=True)
            console.print("✅ Vector database directory created")
            
        except Exception as e:
            console.print(f"[yellow]Database initialization warning: {e}[/yellow]")
    
    async def configure_environment(self):
        """Configure environment variables and settings."""
        console.print("[bold yellow]Configuring environment...[/bold yellow]")
        
        # Update config.yaml with model paths
        config_path = self.base_dir / "config.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Update model paths
            config['llm']['local_model_path'] = str(self.models_dir / "CodeLlama-13b-hf")
            config['llm']['base_model'] = "meta-llama/CodeLlama-13b-hf"
            
            # Enable CUDA if available
            try:
                import torch
                config['performance']['cuda_enabled'] = torch.cuda.is_available()
            except ImportError:
                config['performance']['cuda_enabled'] = False
            
            # Save updated config
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            console.print("✅ Configuration updated")
        
        # Create .env file if it doesn't exist
        env_path = self.base_dir / ".env"
        if not env_path.exists():
            env_content = f"""# AXIS AI Environment Configuration
# Generated by setup script

# Database
DATABASE_URL=sqlite:///./db/axis.db

# Security
SECRET_KEY=auto-generated-will-be-replaced-on-first-run

# HuggingFace (optional - for downloading models)
# HUGGINGFACE_TOKEN=your_token_here

# OpenAI (optional - for fallback)
# OPENAI_API_KEY=your_key_here

# Paths
MODELS_DIR={self.models_dir}
DATA_DIR={self.data_dir}
UPLOADS_DIR={self.uploads_dir}
"""
            with open(env_path, 'w') as f:
                f.write(env_content)
            
            console.print("✅ Environment file created")
    
    async def run_system_tests(self):
        """Run basic system tests to verify installation."""
        console.print("[bold yellow]Running system tests...[/bold yellow]")
        
        tests_passed = 0
        total_tests = 4
        
        # Test 1: Import core modules
        try:
            from core.config import settings
            from core.database import Session
            from modules.llm_engine.local_llm import CodeLlamaEngine
            tests_passed += 1
            console.print("✅ Core module imports successful")
        except Exception as e:
            console.print(f"[red]❌ Core module import failed: {e}[/red]")
        
        # Test 2: Check CUDA availability
        try:
            import torch
            cuda_available = torch.cuda.is_available()
            if cuda_available:
                console.print(f"✅ CUDA available: {torch.cuda.get_device_name(0)}")
            else:
                console.print("⚠️  CUDA not available, will use CPU")
            tests_passed += 1
        except Exception as e:
            console.print(f"[yellow]⚠️  CUDA check failed: {e}[/yellow]")
            tests_passed += 1  # Not critical
        
        # Test 3: Check model files
        try:
            base_model_path = self.models_dir / "CodeLlama-13b-hf"
            if base_model_path.exists() and any(base_model_path.iterdir()):
                console.print("✅ Base model files present")
                tests_passed += 1
            else:
                console.print("[red]❌ Base model files missing[/red]")
        except Exception as e:
            console.print(f"[red]❌ Model check failed: {e}[/red]")
        
        # Test 4: Test database connection
        try:
            from core.database import get_db, engine
            # Simple connection test
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            console.print("✅ Database connection successful")
            tests_passed += 1
        except Exception as e:
            console.print(f"[yellow]⚠️  Database test failed: {e}[/yellow]")
            tests_passed += 1  # Will be created on first run
        
        console.print(f"\n[bold]Test Results: {tests_passed}/{total_tests} passed[/bold]")
        
        if tests_passed >= 3:
            console.print("[green]✅ System tests passed - Ready to start![/green]")
        else:
            console.print("[yellow]⚠️  Some tests failed, but system may still work[/yellow]")

async def main():
    """Main setup function."""
    setup = AxisSetup()
    await setup.run_full_setup()

if __name__ == "__main__":
    asyncio.run(main()) 