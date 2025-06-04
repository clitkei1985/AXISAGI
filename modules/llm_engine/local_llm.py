"""
Local LLM Engine for CodeLlama-13b-hf with Learning Capabilities
Features: 72-98, 184-191, 195
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Union, Any, Iterator, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import torch
import torch.nn.functional as F
from transformers import (
    AutoModelForCausalLM, 
    AutoTokenizer, 
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from datasets import Dataset
from peft import LoraConfig, get_peft_model, TaskType, prepare_model_for_kbit_training
import numpy as np
import pickle
from tenacity import retry, stop_after_attempt, wait_exponential
from circuit_breaker import CircuitBreaker

from core.config import settings
from core.database import Session
from modules.memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

class CodeLlamaEngine:
    """
    Local CodeLlama-13b-hf engine with continuous learning capabilities.
    Features: 72-98, 184-191, 195
    """
    
    def __init__(self, db: Session, memory_manager: MemoryManager):
        self.db = db
        self.memory_manager = memory_manager
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # Model registry for multi-agent support (Feature 186)
        self.models = {}
        self.tokenizers = {}
        self.agent_models = {
            'coder': settings.llm.agents.coder,
            'researcher': settings.llm.agents.researcher,
            'analyst': settings.llm.agents.analyst,
            'creative': settings.llm.agents.creative
        }
        
        # Learning and fine-tuning setup (Features 90-98)
        self.learning_enabled = settings.llm.learning_enabled
        self.interaction_buffer = []
        self.fine_tune_buffer = []
        self.last_fine_tune = datetime.now()
        
        # Circuit breaker for reliability (Feature 195)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=30,
            expected_exception=Exception
        )
        
        # Performance tracking
        self.stats = {
            'interactions': 0,
            'learning_cycles': 0,
            'model_improvements': 0,
            'error_corrections': 0
        }
        
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize CodeLlama models with GPU optimization."""
        logger.info("Initializing CodeLlama models...")
        
        # Configure quantization for memory efficiency
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        ) if self.device == 'cuda' else None
        
        # Load primary models
        primary_models = [
            settings.llm.base_model,
            settings.llm.fallback_models[0],  # Instruct variant
            settings.llm.fallback_models[1]   # Python variant
        ]
        
        for model_name in primary_models:
            try:
                self._load_model(model_name, quantization_config)
            except Exception as e:
                logger.error(f"Failed to load {model_name}: {e}")
                continue
    
    def _load_model(self, model_name: str, quantization_config=None):
        """Load a specific CodeLlama model variant."""
        logger.info(f"Loading {model_name}...")
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True,
            padding_side="left"
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Model loading configuration
        model_kwargs = {
            "trust_remote_code": True,
            "torch_dtype": torch.float16 if self.device == 'cuda' else torch.float32,
            "device_map": "auto" if self.device == 'cuda' else None,
        }
        
        if quantization_config:
            model_kwargs["quantization_config"] = quantization_config
        
        # Load model
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            **model_kwargs
        )
        
        # Prepare for fine-tuning if learning enabled
        if self.learning_enabled and quantization_config:
            model = prepare_model_for_kbit_training(model)
            
            # Add LoRA adapters for efficient fine-tuning
            lora_config = LoraConfig(
                task_type=TaskType.CAUSAL_LM,
                r=16,
                lora_alpha=32,
                lora_dropout=0.1,
                target_modules=["q_proj", "v_proj", "k_proj", "o_proj"]
            )
            model = get_peft_model(model, lora_config)
        
        # Store model and tokenizer
        self.models[model_name] = model
        self.tokenizers[model_name] = tokenizer
        
        logger.info(f"Successfully loaded {model_name}")
        
        # Log GPU memory usage
        if self.device == 'cuda':
            memory_used = torch.cuda.memory_allocated() / 1e9
            logger.info(f"GPU memory used: {memory_used:.1f}GB")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_response(
        self,
        prompt: str,
        agent_type: str = "coder",
        max_tokens: int = None,
        temperature: float = None,
        use_memory: bool = True,
        user_id: Optional[int] = None,
        session_id: Optional[int] = None
    ) -> str:
        """
        Generate response using appropriate CodeLlama model.
        Features: 72-75, 186 (multi-agent)
        """
        try:
            return await self.circuit_breaker.call_async(
                self._generate_response_internal,
                prompt, agent_type, max_tokens, temperature, 
                use_memory, user_id, session_id
            )
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            # Fallback to simple echo (Feature 213 - minimal fallback)
            return f"Error processing request: {str(e)}. System in fallback mode."
    
    async def _generate_response_internal(
        self,
        prompt: str,
        agent_type: str,
        max_tokens: Optional[int],
        temperature: Optional[float],
        use_memory: bool,
        user_id: Optional[int],
        session_id: Optional[int]
    ) -> str:
        """Internal response generation with circuit breaker protection."""
        
        # Select appropriate model for agent type
        model_name = self.agent_models.get(agent_type, settings.llm.base_model)
        
        if model_name not in self.models:
            logger.warning(f"Model {model_name} not loaded, using base model")
            model_name = settings.llm.base_model
            if model_name not in self.models:
                raise Exception("No models available")
        
        model = self.models[model_name]
        tokenizer = self.tokenizers[model_name]
        
        # Enhance prompt with memory if enabled (Feature 10)
        if use_memory and user_id and self.memory_manager:
            enhanced_prompt = await self._enhance_with_memory(prompt, user_id)
        else:
            enhanced_prompt = prompt
        
        # Set defaults
        max_tokens = max_tokens or settings.llm.max_tokens
        temperature = temperature or settings.llm.temperature
        
        # Generate response
        inputs = tokenizer.encode(enhanced_prompt, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = model.generate(
                inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
                repetition_penalty=1.1
            )
        
        # Decode response
        response = tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
        
        # Store interaction for learning (Features 76, 91)
        if self.learning_enabled:
            await self._store_interaction(prompt, response, agent_type, user_id, session_id)
        
        self.stats['interactions'] += 1
        return response.strip()
    
    async def _enhance_with_memory(self, prompt: str, user_id: int) -> str:
        """Enhance prompt with relevant memories (Feature 10)."""
        try:
            # Search for relevant memories
            from core.database import User
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return prompt
            
            memories = self.memory_manager.search_memories(
                query=prompt,
                user=user,
                k=3,
                min_similarity=0.7
            )
            
            if not memories:
                return prompt
            
            # Build enhanced prompt
            memory_context = "\n".join([
                f"- {memory.content}" 
                for memory, score in memories
            ])
            
            enhanced_prompt = f"""Context from previous interactions:
{memory_context}

Current query: {prompt}

Please consider the context when responding."""
            
            return enhanced_prompt
            
        except Exception as e:
            logger.error(f"Memory enhancement failed: {e}")
            return prompt
    
    async def _store_interaction(
        self,
        prompt: str,
        response: str,
        agent_type: str,
        user_id: Optional[int],
        session_id: Optional[int]
    ):
        """Store interaction for learning (Features 76, 91)."""
        interaction = {
            'timestamp': datetime.now(),
            'prompt': prompt,
            'response': response,
            'agent_type': agent_type,
            'user_id': user_id,
            'session_id': session_id
        }
        
        self.interaction_buffer.append(interaction)
        
        # Store in memory if user provided
        if user_id and self.memory_manager:
            try:
                from core.database import User
                user = self.db.query(User).filter(User.id == user_id).first()
                if user:
                    # Store the conversation
                    conversation = f"User: {prompt}\nAssistant: {response}"
                    self.memory_manager.add_memory(
                        user=user,
                        content=conversation,
                        source="conversation",
                        metadata={
                            'agent_type': agent_type,
                            'session_id': session_id
                        }
                    )
            except Exception as e:
                logger.error(f"Failed to store memory: {e}")
        
        # Trigger fine-tuning if buffer is full
        if len(self.interaction_buffer) >= 100:  # Batch size
            await self._schedule_fine_tuning()
    
    async def _schedule_fine_tuning(self):
        """Schedule fine-tuning based on accumulated interactions (Features 93, 97)."""
        if not self.learning_enabled:
            return
        
        now = datetime.now()
        hours_since_last = (now - self.last_fine_tune).total_seconds() / 3600
        
        if hours_since_last >= settings.llm.fine_tune_interval_hours:
            # Run fine-tuning in background
            asyncio.create_task(self._fine_tune_models())
    
    async def _fine_tune_models(self):
        """Fine-tune models based on recent interactions (Features 93, 97)."""
        try:
            logger.info("Starting fine-tuning process...")
            
            # Prepare training data
            training_data = []
            for interaction in self.interaction_buffer[-1000:]:  # Use last 1000 interactions
                training_data.append({
                    'text': f"User: {interaction['prompt']}\nAssistant: {interaction['response']}"
                })
            
            if len(training_data) < 10:
                logger.warning("Not enough training data for fine-tuning")
                return
            
            # Create dataset
            dataset = Dataset.from_list(training_data)
            
            # Fine-tune each model
            for model_name, model in self.models.items():
                if hasattr(model, 'peft_config'):  # Only fine-tune LoRA models
                    await self._fine_tune_single_model(model_name, model, dataset)
            
            self.last_fine_tune = datetime.now()
            self.stats['learning_cycles'] += 1
            self.stats['model_improvements'] += 1
            
            # Clear processed interactions
            self.interaction_buffer = self.interaction_buffer[-100:]  # Keep some for next cycle
            
            logger.info("Fine-tuning completed successfully")
            
        except Exception as e:
            logger.error(f"Fine-tuning failed: {e}")
            self.stats['error_corrections'] += 1
    
    async def _fine_tune_single_model(self, model_name: str, model, dataset):
        """Fine-tune a single model with LoRA."""
        tokenizer = self.tokenizers[model_name]
        
        def tokenize_function(examples):
            return tokenizer(
                examples['text'],
                truncation=True,
                padding='max_length',
                max_length=512
            )
        
        tokenized_dataset = dataset.map(tokenize_function, batched=True)
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=f"./fine_tuned_{model_name.replace('/', '_')}",
            overwrite_output_dir=True,
            num_train_epochs=1,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=8,
            warmup_steps=10,
            logging_steps=10,
            save_steps=100,
            learning_rate=5e-5,
            fp16=True if self.device == 'cuda' else False,
            remove_unused_columns=False,
        )
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=tokenizer,
            mlm=False
        )
        
        # Trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_dataset,
            data_collator=data_collator,
        )
        
        # Train
        trainer.train()
        
        # Save the LoRA adapters
        model.save_pretrained(f"./lora_adapters_{model_name.replace('/', '_')}")
    
    def switch_agent_model(self, agent_type: str, model_name: str):
        """Switch model for specific agent type (Features 193, 201)."""
        if model_name in self.models:
            self.agent_models[agent_type] = model_name
            logger.info(f"Switched {agent_type} agent to {model_name}")
        else:
            logger.error(f"Model {model_name} not available")
    
    def get_model_stats(self) -> Dict[str, Any]:
        """Get learning and performance statistics (Feature 29)."""
        return {
            'loaded_models': list(self.models.keys()),
            'agent_assignments': self.agent_models,
            'learning_enabled': self.learning_enabled,
            'interactions_processed': self.stats['interactions'],
            'learning_cycles_completed': self.stats['learning_cycles'],
            'model_improvements': self.stats['model_improvements'],
            'error_corrections': self.stats['error_corrections'],
            'last_fine_tune': self.last_fine_tune.isoformat(),
            'interaction_buffer_size': len(self.interaction_buffer),
            'device': self.device,
            'cuda_available': torch.cuda.is_available(),
            'gpu_memory_used': torch.cuda.memory_allocated() / 1e9 if torch.cuda.is_available() else 0
        }
    
    async def self_debug_and_correct(self, prompt: str, response: str, error_feedback: str) -> str:
        """Self-debugging mechanism (Feature 184)."""
        try:
            debug_prompt = f"""
System: Analyze the following interaction and correct any errors.

Original Query: {prompt}
AI Response: {response}
Error Feedback: {error_feedback}

Please provide a corrected response that addresses the feedback:
"""
            
            corrected_response = await self.generate_response(
                debug_prompt,
                agent_type="researcher",
                use_memory=False
            )
            
            # Store the correction for learning
            if self.learning_enabled:
                correction_data = {
                    'timestamp': datetime.now(),
                    'original_prompt': prompt,
                    'original_response': response,
                    'error_feedback': error_feedback,
                    'corrected_response': corrected_response,
                    'correction_type': 'self_debug'
                }
                self.fine_tune_buffer.append(correction_data)
            
            self.stats['error_corrections'] += 1
            return corrected_response
            
        except Exception as e:
            logger.error(f"Self-debugging failed: {e}")
            return response  # Return original if debugging fails
    
    def cleanup_resources(self):
        """Clean up GPU resources (Feature 177)."""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        
        logger.info("GPU resources cleaned up")
    
    def __del__(self):
        """Cleanup on destruction."""
        self.cleanup_resources()

def get_codellama_engine(db: Session, memory_manager: MemoryManager) -> CodeLlamaEngine:
    """Factory function to create CodeLlama engine."""
    return CodeLlamaEngine(db, memory_manager)
