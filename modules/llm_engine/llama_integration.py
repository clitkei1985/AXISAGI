import os
import torch
import logging
from typing import Dict, List, Optional, Union, Iterator
from transformers import (
    AutoModelForCausalLM, 
    AutoTokenizer, 
    BitsAndBytesConfig,
    GenerationConfig
)
import asyncio
from pathlib import Path

from core.config import settings

logger = logging.getLogger(__name__)

class LlamaManager:
    """Manages LLaMA 3 13B model with 4-bit quantization for offline AI intelligence."""
    
    def __init__(self):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = None
        self.tokenizer = None
        self.model_name = None
        self.is_loaded = False
        
        # LLaMA 3 specific configurations
        self.llama_configs = {
            "code-llama-13b": {
                "repo_id": "meta-llama/CodeLlama-13b-hf",  # Code Llama base model
                "alt_repos": [
                    "meta-llama/CodeLlama-13b-Instruct-hf",  # Instruction tuned
                    "meta-llama/CodeLlama-13b-Python-hf",    # Python specialized
                    "microsoft/Llama-2-13b-chat-hf",         # Fallback
                    "NousResearch/Llama-2-13b-chat-hf"       # Alternative fallback
                ],
                "chat_template": "### System:\n{system}\n\n### Human:\n{user}\n\n### Assistant:\n",
                "max_context": 16384,  # Code Llama has larger context
                "max_new_tokens": 2048,
                "stop_sequences": ["### Human:", "### System:", "</s>"]
            },
            "llama-3-13b": {
                "repo_id": "meta-llama/Llama-3-13B-Chat-hf",  # Keep as fallback
                "alt_repos": [
                    "microsoft/Llama-2-13b-chat-hf",
                    "NousResearch/Llama-2-13b-chat-hf"
                ],
                "chat_template": "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{user}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
                "max_context": 8192,
                "max_new_tokens": 2048,
                "stop_sequences": ["<|eot_id|>", "<|end_of_text|>"]
            }
        }
        
        if self.device == 'cuda':
            logger.info(f"LLaMA Manager initializing with CUDA on {torch.cuda.get_device_name()}")
            # Clear cache and optimize memory
            torch.cuda.empty_cache()
        else:
            logger.info("LLaMA Manager initializing with CPU (will be slower)")
    
    async def load_llama_model(self, model_variant: str = "code-llama-13b") -> bool:
        """Load Code Llama 13B model with 4-bit quantization for optimal coding performance."""
        if self.is_loaded:
            logger.info("Code Llama model already loaded")
            return True
        
        try:
            config = self.llama_configs.get(model_variant)
            if not config:
                raise ValueError(f"Unknown Code Llama variant: {model_variant}")
            
            # Try main repo first, then fallbacks
            repos_to_try = [config["repo_id"]] + config["alt_repos"]
            
            for repo_id in repos_to_try:
                try:
                    logger.info(f"Attempting to load Code Llama model from: {repo_id}")
                    
                    # Configure 4-bit quantization for memory efficiency
                    quantization_config = None
                    if self.device == 'cuda':
                        quantization_config = BitsAndBytesConfig(
                            load_in_4bit=True,
                            bnb_4bit_compute_dtype=torch.float16,
                            bnb_4bit_use_double_quant=True,
                            bnb_4bit_quant_type="nf4",
                            bnb_4bit_quant_storage_dtype=torch.float16,
                        )
                    
                    # Load tokenizer with Code Llama specific settings
                    logger.info("Loading Code Llama tokenizer...")
                    self.tokenizer = AutoTokenizer.from_pretrained(
                        repo_id,
                        trust_remote_code=True,
                        use_fast=True,
                        padding_side="left",
                        add_eos_token=True
                    )
                    
                    # Set special tokens for Code Llama
                    if self.tokenizer.pad_token is None:
                        self.tokenizer.pad_token = self.tokenizer.eos_token
                    
                    # Load model with optimizations
                    logger.info("Loading Code Llama model with 4-bit quantization...")
                    model_kwargs = {
                        "trust_remote_code": True,
                        "torch_dtype": torch.float16 if self.device == 'cuda' else torch.float32,
                        "low_cpu_mem_usage": True,
                        "use_cache": True,
                    }
                    
                    if self.device == 'cuda':
                        model_kwargs["device_map"] = "auto"
                        if quantization_config:
                            model_kwargs["quantization_config"] = quantization_config
                    
                    self.model = AutoModelForCausalLM.from_pretrained(
                        repo_id,
                        **model_kwargs
                    )
                    
                    # Configure generation settings optimized for code
                    self.model.generation_config = GenerationConfig(
                        max_new_tokens=config["max_new_tokens"],
                        do_sample=True,
                        temperature=0.1,  # Lower temperature for code generation
                        top_p=0.95,
                        top_k=50,
                        repetition_penalty=1.05,  # Lower penalty for code
                        pad_token_id=self.tokenizer.eos_token_id,
                        eos_token_id=self.tokenizer.eos_token_id,
                        stop_strings=config.get("stop_sequences", []),
                        use_cache=True
                    )
                    
                    # Enable optimizations for Code Llama
                    if hasattr(torch, 'compile') and self.device == 'cuda':
                        try:
                            self.model = torch.compile(self.model, mode="reduce-overhead")
                            logger.info("Code Llama compiled for optimized inference")
                        except Exception as e:
                            logger.warning(f"Code Llama compilation failed: {e}")
                    
                    self.model_name = repo_id
                    self.model_variant = model_variant
                    self.is_loaded = True
                    
                    # Log memory usage
                    if self.device == 'cuda':
                        memory_used = torch.cuda.memory_allocated() / 1e9
                        memory_cached = torch.cuda.memory_reserved() / 1e9
                        logger.info(f"✅ Code Llama loaded successfully! GPU memory - Used: {memory_used:.1f}GB, Cached: {memory_cached:.1f}GB")
                    else:
                        logger.info("✅ Code Llama loaded successfully on CPU!")
                    
                    return True
                    
                except Exception as e:
                    logger.warning(f"Failed to load from {repo_id}: {e}")
                    continue
            
            # If all repos failed
            logger.error("Failed to load Code Llama model from all available repositories")
            return False
            
        except Exception as e:
            logger.error(f"Error loading Code Llama model: {e}")
            return False
    
    async def generate_intelligent_response(
        self,
        prompt: str,
        system_prompt: str = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        stream: bool = False,
        enhanced_context: str = None
    ) -> Union[str, Iterator[str]]:
        """Generate intelligent response using LLaMA with enhanced context and reasoning."""
        if not self.is_loaded:
            raise RuntimeError("LLaMA model not loaded. Call load_llama_model() first.")
        
        try:
            # Build intelligent prompt with context
            if not system_prompt:
                system_prompt = self._build_intelligent_system_prompt()
            
            # Format prompt using LLaMA chat template
            formatted_prompt = self._format_chat_prompt(
                system_prompt=system_prompt,
                user_prompt=prompt,
                enhanced_context=enhanced_context
            )
            
            # Tokenize
            inputs = self.tokenizer.encode(formatted_prompt, return_tensors="pt")
            if self.device == 'cuda':
                inputs = inputs.to(self.device)
            
            # Configure generation parameters
            generation_kwargs = {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "do_sample": temperature > 0,
                "top_p": 0.9,
                "top_k": 50,
                "repetition_penalty": 1.1,
                "pad_token_id": self.tokenizer.eos_token_id,
                "eos_token_id": self.tokenizer.eos_token_id,
                "use_cache": True,
                "attention_mask": torch.ones_like(inputs)
            }
            
            with torch.no_grad():
                if stream:
                    return self._stream_generate(inputs, generation_kwargs)
                else:
                    outputs = self.model.generate(inputs, **generation_kwargs)
                    
                    # Decode response (only new tokens)
                    response = self.tokenizer.decode(
                        outputs[0][inputs.shape[1]:], 
                        skip_special_tokens=True
                    )
                    
                    return self._post_process_response(response)
                    
        except Exception as e:
            logger.error(f"Error generating LLaMA response: {e}")
            raise
    
    async def _stream_generate(self, inputs: torch.Tensor, generation_kwargs: Dict) -> Iterator[str]:
        """Stream generation for real-time responses."""
        async def stream_generator():
            generated = inputs.clone()
            max_new_tokens = generation_kwargs.get("max_new_tokens", 1024)
            temperature = generation_kwargs.get("temperature", 0.7)
            
            for _ in range(max_new_tokens):
                outputs = self.model(generated)
                next_token_logits = outputs.logits[0, -1, :]
                
                # Apply temperature
                if temperature > 0:
                    next_token_logits = next_token_logits / temperature
                
                # Apply top-k and top-p sampling
                probabilities = torch.softmax(next_token_logits, dim=-1)
                next_token = torch.multinomial(probabilities, num_samples=1)
                
                # Check for end token
                if next_token.item() == self.tokenizer.eos_token_id:
                    break
                
                # Decode and yield token
                token_text = self.tokenizer.decode(next_token, skip_special_tokens=True)
                yield token_text
                
                # Update generated sequence
                generated = torch.cat([generated, next_token.unsqueeze(0)], dim=-1)
                
                # Small delay for responsiveness
                await asyncio.sleep(0.01)
        
        return stream_generator()
    
    def _build_intelligent_system_prompt(self) -> str:
        """Build an intelligent system prompt optimized for Code Llama coding capabilities."""
        return """You are AXIS AI powered by Code Llama, an advanced AI assistant specialized in programming and code generation. You excel at:

💻 **Code Generation**: Writing clean, efficient, and well-documented code in any language
🐛 **Debugging**: Identifying and fixing bugs, optimization issues, and logic errors  
🏗️ **Architecture**: Designing software systems, APIs, and database schemas
📚 **Code Explanation**: Breaking down complex code into understandable components
🔍 **Code Review**: Analyzing code quality, security, and best practices
🚀 **Problem Solving**: Converting requirements into working code solutions

**Programming Languages**: Python, JavaScript, TypeScript, Java, C++, C#, Go, Rust, PHP, Ruby, Swift, Kotlin, and more.

**Your Approach**:
- Write clean, readable, and well-commented code
- Follow best practices and coding standards
- Provide complete, working solutions
- Explain your code and reasoning
- Consider edge cases and error handling
- Optimize for performance when relevant

**Code Format**: Always use proper syntax highlighting with language tags (```python, ```javascript, etc.)

You also maintain memory of our conversations and learn from every interaction to provide better assistance over time."""

    def _format_chat_prompt(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        enhanced_context: str = None
    ) -> str:
        """Format prompts using Code Llama chat template."""
        # Use Code Llama variant if loaded, otherwise fallback
        variant = getattr(self, 'model_variant', 'code-llama-13b')
        config = self.llama_configs[variant]
        
        # Add enhanced context if available
        if enhanced_context:
            system_prompt += f"\n\n**Previous Context:**\n{enhanced_context}"
        
        return config["chat_template"].format(
            system=system_prompt,
            user=user_prompt
        )
    
    def _post_process_response(self, response: str) -> str:
        """Post-process LLaMA response for better quality."""
        # Remove potential artifacts
        response = response.strip()
        
        # Remove any remaining special tokens
        response = response.replace("<|eot_id|>", "").replace("<|start_header_id|>", "").replace("<|end_header_id|>", "")
        
        # Ensure response doesn't cut off mid-sentence
        if response and not response.endswith(('.', '!', '?', ':', ';')):
            # Find last complete sentence
            last_sentence_end = max(
                response.rfind('.'),
                response.rfind('!'),
                response.rfind('?'),
                response.rfind(':')
            )
            if last_sentence_end > len(response) * 0.7:  # Only if we don't lose too much
                response = response[:last_sentence_end + 1]
        
        return response
    
    def unload_model(self):
        """Unload the model to free memory."""
        if self.is_loaded:
            del self.model
            del self.tokenizer
            if self.device == 'cuda':
                torch.cuda.empty_cache()
            self.model = None
            self.tokenizer = None
            self.is_loaded = False
            logger.info("LLaMA model unloaded")
    
    def get_model_info(self) -> Dict:
        """Get information about the loaded model."""
        if not self.is_loaded:
            return {"status": "not_loaded"}
        
        info = {
            "status": "loaded",
            "model_name": self.model_name,
            "device": self.device,
            "quantization": "4-bit" if self.device == 'cuda' else "none",
            "context_length": self.llama_configs["llama-3-13b"]["max_context"],
            "max_tokens": self.llama_configs["llama-3-13b"]["max_new_tokens"]
        }
        
        if self.device == 'cuda':
            try:
                info.update({
                    "memory_used_gb": torch.cuda.memory_allocated() / 1e9,
                    "memory_cached_gb": torch.cuda.memory_reserved() / 1e9,
                    "gpu_name": torch.cuda.get_device_name()
                })
            except:
                pass
        
        return info
    
    async def perform_reasoning_task(self, task: str, context: str = None) -> str:
        """Perform deep reasoning on a specific task."""
        reasoning_prompt = f"""**Deep Thinking Task**: {task}

Please think through this step-by-step:
1. Analyze the problem
2. Consider multiple perspectives
3. Apply logical reasoning
4. Provide a well-reasoned conclusion

{f"**Context**: {context}" if context else ""}

Think carefully and provide your best analysis:"""
        
        return await self.generate_intelligent_response(
            reasoning_prompt,
            system_prompt="You are an expert reasoning AI. Think deeply and logically about complex problems.",
            max_tokens=1500,
            temperature=0.3  # Lower temperature for reasoning
        )

# Global instance
_llama_manager = None

def get_llama_manager() -> LlamaManager:
    """Get the global LLaMA manager instance."""
    global _llama_manager
    if _llama_manager is None:
        _llama_manager = LlamaManager()
    return _llama_manager 