from typing import Dict, Optional
import os
from pathlib import Path
import logging
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from core.config import settings

logger = logging.getLogger(__name__)

class ModelManager:
    """Manages loading, switching, and optimization of local LLM models."""
    
    def __init__(self, device: str = None):
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.local_models: Dict = {}
        self.tokenizers: Dict = {}
        self.gpu_memory_fraction = 0.8  # Use 80% of GPU memory
        
        if self.device == 'cuda':
            logger.info(f"Model Manager initializing with CUDA on {torch.cuda.get_device_name()}")
            logger.info(f"Available GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
            
            # Configure memory management for RTX 5080
            torch.cuda.empty_cache()
            if hasattr(torch.cuda, 'set_per_process_memory_fraction'):
                torch.cuda.set_per_process_memory_fraction(self.gpu_memory_fraction)
        else:
            logger.info("Model Manager initializing with CPU")
        
        # Load default model if specified
        if settings.llm.local_model_path:
            self.load_model(settings.llm.local_model_path)

    def load_model(self, model_path: str, model_name: Optional[str] = None):
        """Load a local model with GPU optimization and fallback handling."""
        if not model_name:
            model_name = model_path.split('/')[-1]
        
        try:
            logger.info(f"Loading local model: {model_path}")
            
            # Check if model files exist
            model_path_obj = Path(model_path)
            if not model_path_obj.exists():
                logger.error(f"Model path does not exist: {model_path}")
                return self._load_fallback_model(model_name)
            
            # Check for required model weight files
            index_file = model_path_obj / "model.safetensors.index.json"
            if index_file.exists():
                import json
                with open(index_file) as f:
                    index_data = json.load(f)
                
                # Check if all safetensors files exist
                weight_files = set(index_data.get("weight_map", {}).values())
                missing_files = []
                for weight_file in weight_files:
                    if not (model_path_obj / weight_file).exists():
                        missing_files.append(weight_file)
                
                if missing_files:
                    logger.error(f"Missing model weight files: {missing_files}")
                    logger.info("Attempting to download missing files...")
                    if self._download_missing_files(model_path, missing_files):
                        logger.info("Successfully downloaded missing files")
                    else:
                        logger.warning("Could not download missing files, using fallback")
                        return self._load_fallback_model(model_name)
            
            # Configure quantization for memory efficiency on RTX 5080
            quantization_config = None
            if self.device == 'cuda':
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
            
            # Load tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True,
                padding_side="left"
            )
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # Load model with GPU optimizations
            model_kwargs = {
                "trust_remote_code": True,
                "torch_dtype": torch.float16 if self.device == 'cuda' else torch.float32,
                "device_map": "auto" if self.device == 'cuda' else None,
            }
            
            if quantization_config:
                model_kwargs["quantization_config"] = quantization_config
            
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                **model_kwargs
            )
            
            # Move to GPU if not using device_map
            if self.device == 'cuda' and "device_map" not in model_kwargs:
                model = model.to(self.device)
            
            # Enable optimizations
            if hasattr(model, 'half') and self.device == 'cuda':
                model = model.half()
            
            # Compile model for better performance (PyTorch 2.0+)
            if hasattr(torch, 'compile') and self.device == 'cuda':
                try:
                    model = torch.compile(model, mode="reduce-overhead")
                    logger.info("Model compiled for optimized performance")
                except Exception as e:
                    logger.warning(f"Model compilation failed: {e}")
            
            self.local_models[model_name] = model
            self.tokenizers[model_name] = tokenizer
            
            logger.info(f"Successfully loaded model {model_name} on {self.device}")
            
            # Log GPU memory usage
            if self.device == 'cuda':
                memory_used = torch.cuda.memory_allocated() / 1e9
                memory_cached = torch.cuda.memory_reserved() / 1e9
                logger.info(f"GPU memory - Used: {memory_used:.1f}GB, Cached: {memory_cached:.1f}GB")
                
        except Exception as e:
            logger.error(f"Failed to load model {model_path}: {e}")
            logger.info("Attempting to load fallback model...")
            return self._load_fallback_model(model_name)
    
    def _download_missing_files(self, model_path: str, missing_files: list) -> bool:
        """Attempt to download missing model files from HuggingFace."""
        try:
            from huggingface_hub import hf_hub_download
            
            # Extract repo ID from path (assuming it follows our structure)
            if "CodeLlama-13b-hf" in model_path:
                repo_id = "codellama/CodeLlama-13b-hf"
            elif "CodeLlama-13b-Instruct-hf" in model_path:
                repo_id = "codellama/CodeLlama-13b-Instruct-hf"
            elif "CodeLlama-13b-Python-hf" in model_path:
                repo_id = "codellama/CodeLlama-13b-Python-hf"
            else:
                logger.error("Could not determine HuggingFace repo ID from path")
                return False
            
            logger.info(f"Downloading {len(missing_files)} missing files from {repo_id}")
            
            for file in missing_files:
                logger.info(f"Downloading {file}...")
                try:
                    hf_hub_download(
                        repo_id=repo_id,
                        filename=file,
                        local_dir=model_path,
                        local_dir_use_symlinks=False
                    )
                    logger.info(f"Successfully downloaded {file}")
                except Exception as e:
                    logger.error(f"Failed to download {file}: {e}")
                    return False
            
            return True
            
        except ImportError:
            logger.error("huggingface_hub not available for downloading missing files")
            return False
        except Exception as e:
            logger.error(f"Error downloading missing files: {e}")
            return False
    
    def _load_fallback_model(self, model_name: str) -> bool:
        """Load a fallback model (GPT-2 or similar) when primary model fails."""
        try:
            logger.info("Loading fallback model (GPT-2) for basic functionality...")
            
            from transformers import GPT2LMHeadModel, GPT2Tokenizer
            
            # Load GPT-2 as fallback
            tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
            tokenizer.pad_token = tokenizer.eos_token
            
            model = GPT2LMHeadModel.from_pretrained("gpt2")
            
            if self.device == 'cuda':
                model = model.to(self.device)
            
            self.local_models[f"{model_name}_fallback"] = model
            self.tokenizers[f"{model_name}_fallback"] = tokenizer
            
            # Also register with original name for compatibility
            self.local_models[model_name] = model
            self.tokenizers[model_name] = tokenizer
            
            logger.info(f"Successfully loaded fallback model for {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load fallback model: {e}")
            # Create a dummy model that returns helpful error messages
            self._create_dummy_model(model_name)
            return False
    
    def _create_dummy_model(self, model_name: str):
        """Create a dummy model that returns helpful error messages."""
        class DummyModel:
            def generate(self, *args, **kwargs):
                return torch.tensor([[1, 2, 3]])  # Dummy output
        
        class DummyTokenizer:
            def __init__(self):
                self.pad_token = "<pad>"
                self.eos_token = "<eos>"
                self.vocab_size = 1000
                
            def encode(self, text, *args, **kwargs):
                return [1, 2, 3]
                
            def decode(self, tokens, *args, **kwargs):
                return "I apologize, but the AI model is currently unavailable. Please ensure the CodeLlama model files are properly downloaded."
        
        self.local_models[model_name] = DummyModel()
        self.tokenizers[model_name] = DummyTokenizer()
        logger.warning(f"Created dummy model for {model_name} - responses will be limited")

    def unload_model(self, model_name: str) -> bool:
        """Unload a model to free memory."""
        try:
            if model_name in self.local_models:
                # Clear from GPU memory
                if self.device == 'cuda':
                    del self.local_models[model_name]
                    del self.tokenizers[model_name]
                    torch.cuda.empty_cache()
                else:
                    del self.local_models[model_name]
                    del self.tokenizers[model_name]
                
                logger.info(f"Unloaded model: {model_name}")
                return True
            else:
                logger.warning(f"Model {model_name} not found")
                return False
                
        except Exception as e:
            logger.error(f"Error unloading model {model_name}: {e}")
            return False

    def switch_model(self, model_name: str) -> bool:
        """Switch to a different loaded model."""
        if model_name in self.local_models:
            logger.info(f"Switched to model: {model_name}")
            return True
        else:
            logger.error(f"Model {model_name} not loaded")
            return False

    def get_model(self, model_name: str):
        """Get a loaded model instance."""
        return self.local_models.get(model_name)

    def get_tokenizer(self, model_name: str):
        """Get a tokenizer instance."""
        return self.tokenizers.get(model_name)

    def list_loaded_models(self) -> list:
        """Get list of currently loaded models."""
        return list(self.local_models.keys())

    def get_model_info(self, model_name: str) -> dict:
        """Get information about a loaded model."""
        if model_name not in self.local_models:
            return {}
        
        model = self.local_models[model_name]
        tokenizer = self.tokenizers[model_name]
        
        info = {
            "name": model_name,
            "device": str(next(model.parameters()).device),
            "dtype": str(next(model.parameters()).dtype),
            "vocab_size": tokenizer.vocab_size,
            "model_max_length": getattr(tokenizer, 'model_max_length', 'unknown')
        }
        
        # Get memory usage if on CUDA
        if self.device == 'cuda':
            try:
                memory_used = torch.cuda.memory_allocated() / 1e9
                memory_cached = torch.cuda.memory_reserved() / 1e9
                info["memory_used_gb"] = memory_used
                info["memory_cached_gb"] = memory_cached
            except:
                pass
        
        return info

    def optimize_memory(self):
        """Optimize GPU memory usage."""
        if self.device == 'cuda':
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            logger.info("GPU memory optimized")

    def get_memory_usage(self) -> dict:
        """Get current memory usage statistics."""
        if self.device == 'cuda':
            try:
                return {
                    "device": "cuda",
                    "allocated_gb": torch.cuda.memory_allocated() / 1e9,
                    "cached_gb": torch.cuda.memory_reserved() / 1e9,
                    "max_allocated_gb": torch.cuda.max_memory_allocated() / 1e9,
                    "total_memory_gb": torch.cuda.get_device_properties(0).total_memory / 1e9
                }
            except:
                return {"device": "cuda", "error": "Could not get memory stats"}
        else:
            import psutil
            memory = psutil.virtual_memory()
            return {
                "device": "cpu", 
                "used_gb": memory.used / 1e9,
                "total_gb": memory.total / 1e9,
                "percent": memory.percent
            }

    def check_model_compatibility(self, model_path: str) -> dict:
        """Check if a model can be loaded with current hardware."""
        try:
            # Try to load model config without loading weights
            from transformers import AutoConfig
            config = AutoConfig.from_pretrained(model_path, trust_remote_code=True)
            
            estimated_size_gb = getattr(config, 'num_parameters', 0) * 4 / 1e9  # Rough estimate
            
            result = {
                "compatible": True,
                "estimated_size_gb": estimated_size_gb,
                "warnings": []
            }
            
            if self.device == 'cuda':
                available_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
                if estimated_size_gb > available_memory * 0.8:
                    result["warnings"].append(f"Model may not fit in GPU memory ({estimated_size_gb:.1f}GB > {available_memory*0.8:.1f}GB)")
            
            return result
            
        except Exception as e:
            return {
                "compatible": False,
                "error": str(e)
            } 