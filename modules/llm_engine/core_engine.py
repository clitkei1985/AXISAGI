from typing import List, Dict, Optional, Union, Any, Iterator
import asyncio
from datetime import datetime
import logging
import openai
import torch
from openai import OpenAI

from core.config import settings
from core.database import Session, Message, User
from .schemas import ModelStats

logger = logging.getLogger(__name__)

class CoreLLMEngine:
    """Core LLM operations handling both OpenAI and local model inference."""
    
    def __init__(self):
        self.openai_client = self._setup_openai()
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        if self.device == 'cuda':
            logger.info(f"Core LLM Engine initializing with CUDA on {torch.cuda.get_device_name()}")
        else:
            logger.info("Core LLM Engine initializing with CPU")

    def _get_openai_api_key(self):
        """Get OpenAI API key from multiple sources."""
        # Check settings first
        if settings.llm.openai_api_key:
            logger.info("Found OpenAI API key in settings")
            return settings.llm.openai_api_key
        
        # Check environment variables directly
        import os
        api_key = os.environ.get('LLM_OPENAI_API_KEY') or os.environ.get('OPENAI_API_KEY')
        if api_key:
            logger.info("Found OpenAI API key in environment variables")
            return api_key
        
        logger.warning("No OpenAI API key found in settings or environment")
        return None

    def _setup_openai(self):
        """Setup OpenAI client if API key is available."""
        api_key = self._get_openai_api_key()
        if api_key:
            return OpenAI(api_key=api_key)
        return None

    async def _generate_openai_response(
        self,
        messages: List[Dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float,
        stream: bool
    ) -> Union[str, Iterator[str]]:
        """Generate response using OpenAI API."""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")
        
        try:
            if stream:
                response = self.openai_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=True
                )
                
                async def response_generator():
                    for chunk in response:
                        if chunk.choices[0].delta.content:
                            yield chunk.choices[0].delta.content
                
                return response_generator()
            else:
                response = self.openai_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    async def _generate_local_response(
        self,
        messages: List[Dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float,
        stream: bool,
        local_models: Dict,
        tokenizers: Dict
    ) -> Union[str, Iterator[str]]:
        """Generate response using local model."""
        if model not in local_models:
            raise ValueError(f"Model {model} not loaded")
        
        try:
            model_instance = local_models[model]
            tokenizer = tokenizers[model]
            
            # Format messages for local model
            prompt = self._format_messages_for_local_model(messages, tokenizer)
            
            # Tokenize input
            inputs = tokenizer.encode(prompt, return_tensors="pt")
            if self.device == 'cuda':
                inputs = inputs.to(self.device)
            
            # Generate
            with torch.no_grad():
                if stream:
                    # Streaming generation
                    generated = inputs.clone()
                    max_new_tokens = min(max_tokens, 512)
                    
                    async def stream_generator():
                        nonlocal generated
                        for _ in range(max_new_tokens):
                            outputs = model_instance(generated)
                            next_token_logits = outputs.logits[0, -1, :]
                            
                            # Apply temperature
                            if temperature > 0:
                                next_token_logits = next_token_logits / temperature
                            
                            # Sample next token
                            probabilities = torch.softmax(next_token_logits, dim=-1)
                            next_token = torch.multinomial(probabilities, num_samples=1)
                            
                            # Check for end token
                            if next_token.item() == tokenizer.eos_token_id:
                                break
                            
                            # Decode and yield token
                            token_text = tokenizer.decode(next_token, skip_special_tokens=True)
                            yield token_text
                            
                            # Update generated sequence
                            generated = torch.cat([generated, next_token.unsqueeze(0)], dim=-1)
                            
                            await asyncio.sleep(0.01)  # Small delay for responsiveness
                    
                    return stream_generator()
                else:
                    # Non-streaming generation
                    outputs = model_instance.generate(
                        inputs,
                        max_new_tokens=max_tokens,
                        temperature=temperature,
                        do_sample=temperature > 0,
                        pad_token_id=tokenizer.eos_token_id,
                        attention_mask=torch.ones_like(inputs)
                    )
                    
                    # Decode response
                    response = tokenizer.decode(
                        outputs[0][inputs.shape[1]:], 
                        skip_special_tokens=True
                    )
                    return response.strip()
                    
        except Exception as e:
            logger.error(f"Local model generation error: {e}")
            raise

    def _format_messages_for_local_model(self, messages: List[Dict[str, str]], tokenizer) -> str:
        """Format conversation messages for local model input."""
        prompt = ""
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if role == "system":
                prompt += f"System: {content}\n"
            elif role == "user":
                prompt += f"Human: {content}\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n"
        
        prompt += "Assistant: "
        return prompt

    def is_openai_available(self) -> bool:
        """Check if OpenAI client is available."""
        return self.openai_client is not None

    async def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of text using available model."""
        try:
            if self.openai_client:
                # Use OpenAI for sentiment analysis
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Analyze the sentiment of the following text. Return only a JSON object with 'positive', 'negative', and 'neutral' scores between 0 and 1."},
                        {"role": "user", "content": text}
                    ],
                    max_tokens=100,
                    temperature=0
                )
                
                import json
                try:
                    return json.loads(response.choices[0].message.content)
                except:
                    return {"positive": 0.5, "negative": 0.5, "neutral": 0.0}
            else:
                # Fallback to simple sentiment analysis
                positive_words = ["good", "great", "excellent", "happy", "positive", "love", "like"]
                negative_words = ["bad", "terrible", "awful", "sad", "negative", "hate", "dislike"]
                
                words = text.lower().split()
                positive_count = sum(1 for word in words if word in positive_words)
                negative_count = sum(1 for word in words if word in negative_words)
                total = len(words)
                
                if total == 0:
                    return {"positive": 0.0, "negative": 0.0, "neutral": 1.0}
                
                positive_score = positive_count / total
                negative_score = negative_count / total
                neutral_score = 1.0 - positive_score - negative_score
                
                return {
                    "positive": positive_score,
                    "negative": negative_score,
                    "neutral": max(0.0, neutral_score)
                }
                
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {"positive": 0.0, "negative": 0.0, "neutral": 1.0} 