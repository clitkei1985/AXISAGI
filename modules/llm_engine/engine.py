from typing import List, Dict, Optional, Union, Any, Iterator
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from core.config import settings
from core.database import Message, User
from .core_engine import CoreLLMEngine
from .model_manager import ModelManager
from .memory_integration import MemoryIntegration
from .statistics import LLMStatistics
from .llama_integration import get_llama_manager, LlamaManager
from .schemas import ModelStats

logger = logging.getLogger(__name__)

class LLMEngine:
    """Advanced LLM engine with GPU acceleration, memory integration, and offline LLaMA intelligence. (Features: 71-91)"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Initialize modular components
        self.core_engine = CoreLLMEngine()
        self.model_manager = ModelManager()
        self.memory_integration = MemoryIntegration(db)
        self.statistics = LLMStatistics()
        self.llama_manager = get_llama_manager()
        
        # Offline-first configuration
        self.offline_mode = not self.core_engine.is_openai_available()
        self.prefer_local = True  # Prefer local models for better privacy and offline capability
        
        logger.info("LLM Engine initialized with modular components and offline intelligence")
        
        # Auto-load LLaMA if no OpenAI key
        if self.offline_mode:
            logger.info("🔄 No OpenAI API key detected - initializing offline mode with Code Llama")
            # Don't await here since __init__ can't be async, will load on first use

    async def ensure_local_model_loaded(self):
        """Ensure a local model is loaded for offline operation."""
        if not self.llama_manager.is_loaded:
            logger.info("🤖 Loading Code Llama 13B for offline coding intelligence...")
            success = await self.llama_manager.load_llama_model("code-llama-13b")
            if success:
                logger.info("✅ Code Llama model loaded successfully - ready for coding!")
            else:
                logger.warning("❌ Failed to load Code Llama model - trying fallback...")
                # Try regular LLaMA as fallback
                fallback_success = await self.llama_manager.load_llama_model("llama-3-13b")
                if not fallback_success:
                    logger.warning("❌ All model loading failed - limited offline capabilities")
                    return False
        return True

    async def generate_response(
        self,
        prompt: str,
        model: str = None,
        user: Optional[User] = None,
        session_id: Optional[int] = None,
        max_tokens: int = 512,
        temperature: float = 0.7,
        stream: bool = False,
        use_memory: bool = True,
        force_offline: bool = False
    ) -> Union[str, Iterator[str]]:
        """Generate intelligent response with automatic model selection and memory enhancement."""
        start_time = datetime.utcnow()
        
        try:
            # Enhance prompt with memory if enabled and user provided
            enhanced_prompt = prompt
            enhanced_context = None
            
            if use_memory and user:
                enhanced_prompt = await self.memory_integration.enhance_prompt(
                    prompt, user, k=5  # Get more context for better responses
                )
                # Get rich context for LLaMA
                memories = self.memory_integration.memory_manager.search_memories(
                    query=prompt, user=user, k=3, min_similarity=0.6
                )
                if memories:
                    enhanced_context = "\n".join([
                        f"- {memory.content[:200]}..." for memory, _ in memories
                    ])
            
            # Intelligent model selection
            selected_model = self._select_best_model(prompt, model, force_offline)
            
            # Generate response based on model type
            if selected_model.startswith("llama") or force_offline or self.offline_mode:
                # Use LLaMA for offline/local generation
                await self.ensure_local_model_loaded()
                
                if self.llama_manager.is_loaded:
                    response = await self.llama_manager.generate_intelligent_response(
                        prompt=prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        stream=stream,
                        enhanced_context=enhanced_context
                    )
                    model_used = "llama-3-13b-local"
                else:
                    # Fallback to basic response if LLaMA fails
                    response = self._generate_fallback_response(prompt)
                    model_used = "fallback"
                    
            elif selected_model.startswith(("gpt-", "claude-")) and self.core_engine.is_openai_available():
                # Use OpenAI API
                messages = [{"role": "user", "content": enhanced_prompt}]
                response = await self.core_engine._generate_openai_response(
                    messages, selected_model, max_tokens, temperature, stream
                )
                model_used = selected_model
                
            else:
                # Try local models first, then fallback
                if self.model_manager.local_models:
                    messages = [{"role": "user", "content": enhanced_prompt}]
                    response = await self.core_engine._generate_local_response(
                        messages, selected_model, max_tokens, temperature, stream,
                        self.model_manager.local_models,
                        self.model_manager.tokenizers
                    )
                    model_used = selected_model
                else:
                    # Last resort - LLaMA
                    await self.ensure_local_model_loaded()
                    if self.llama_manager.is_loaded:
                        response = await self.llama_manager.generate_intelligent_response(
                            prompt=prompt,
                            max_tokens=max_tokens,
                            temperature=temperature,
                            stream=stream,
                            enhanced_context=enhanced_context
                        )
                        model_used = "llama-3-13b-local"
                    else:
                        response = self._generate_fallback_response(prompt)
                        model_used = "fallback"
            
            # Automatically save to database and memory
            if session_id and user and not stream:
                await self._save_message(prompt, "user", session_id)
                await self._save_message(str(response), "assistant", session_id)
                
                # Always save to memory for continuous learning
                await self.memory_integration.save_conversation_to_memory(
                    user, prompt, str(response), session_id
                )
            
            # Update statistics
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            token_count = len(str(response).split()) if not stream else 0
            self.statistics.update_stats(
                latency=latency,
                tokens=token_count,
                success=True,
                model_name=model_used
            )
            
            logger.info(f"Generated response using {model_used} (offline: {force_offline or self.offline_mode})")
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            
            # Update error statistics
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.statistics.update_stats(
                latency=latency,
                error=str(e),
                success=False,
                model_name=model or "unknown"
            )
            
            # Try fallback response in case of error
            if not stream:
                return self._generate_fallback_response(prompt, error=str(e))
            raise

    def _select_best_model(self, prompt: str, requested_model: str = None, force_offline: bool = False) -> str:
        """Intelligently select the best model based on prompt characteristics and availability."""
        
        # Force offline mode
        if force_offline or self.offline_mode:
            return "code-llama-13b"
        
        # User requested specific model
        if requested_model:
            return requested_model
        
        # Analyze prompt to determine best model
        prompt_lower = prompt.lower()
        
        # Coding tasks - always prefer Code Llama
        if any(keyword in prompt_lower for keyword in [
            'code', 'programming', 'function', 'class', 'debug', 'python', 'javascript', 
            'algorithm', 'script', 'syntax', 'api', 'database', 'sql', 'html', 'css',
            'react', 'vue', 'angular', 'node', 'express', 'django', 'flask', 'spring',
            'variable', 'method', 'object', 'array', 'loop', 'condition', 'exception',
            'import', 'export', 'package', 'library', 'framework', 'repository', 'git',
            'compile', 'build', 'deploy', 'test', 'unit test', 'integration', 'dev',
            'software', 'application', 'system', 'architecture', 'design pattern'
        ]):
            return "code-llama-13b"
        
        # Technical analysis and problem solving - prefer Code Llama
        if any(keyword in prompt_lower for keyword in [
            'analyze', 'debug', 'optimize', 'refactor', 'review', 'fix', 'improve',
            'algorithm', 'data structure', 'complexity', 'performance', 'efficiency'
        ]):
            return "code-llama-13b"
        
        # File extensions mentioned - definitely coding
        if any(ext in prompt_lower for ext in [
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.go', '.rs', '.php',
            '.rb', '.swift', '.kt', '.html', '.css', '.sql', '.json', '.xml', '.yaml'
        ]):
            return "code-llama-13b"
        
        # General tasks - still prefer Code Llama for technical users
        if self.prefer_local:
            return "code-llama-13b"
        
        # Fallback to online models for non-technical tasks
        return "gpt-4"

    def _generate_fallback_response(self, prompt: str, error: str = None) -> str:
        """Generate a fallback response when all models fail."""
        if error:
            return f"I apologize, but I'm experiencing technical difficulties right now. Error details: {error}. Please try again in a moment, or rephrase your question."
        
        # Simple pattern matching for basic responses
        prompt_lower = prompt.lower()
        
        if any(greeting in prompt_lower for greeting in ['hello', 'hi', 'hey']):
            return "Hello! I'm AXIS AI. I'm currently operating in limited mode. How can I help you today?"
        
        if 'how are you' in prompt_lower:
            return "I'm functioning well, thank you! I'm an AI assistant designed to help with various tasks. What would you like to know?"
        
        if any(keyword in prompt_lower for keyword in ['help', 'what can you do']):
            return """I'm AXIS AI, your intelligent assistant. I can help with:
            
🧠 **Reasoning & Analysis** - Complex problem solving
💻 **Programming & Code** - Writing, debugging, explaining code  
📚 **Research & Learning** - Information analysis and synthesis
🎯 **Memory & Context** - I remember our conversations and learn over time
🌐 **Offline Operation** - I work completely offline for privacy

I'm currently operating in limited mode, but I'll do my best to assist you. What would you like to work on?"""
        
        return "I understand you're asking about: " + prompt[:100] + "... I'm currently in limited mode, but I'll do my best to help. Could you please rephrase your question or be more specific about what you need assistance with?"

    async def perform_deep_research(self, topic: str, user: User) -> str:
        """Perform deep research using memory and reasoning capabilities."""
        # Search memory for relevant information
        memories = self.memory_integration.memory_manager.search_memories(
            query=topic, user=user, k=10, min_similarity=0.5
        )
        
        context = "\n".join([
            f"Memory {i+1}: {memory.content[:300]}..." 
            for i, (memory, _) in enumerate(memories[:5])
        ])
        
        # Use LLaMA for deep reasoning
        await self.ensure_local_model_loaded()
        
        if self.llama_manager.is_loaded:
            research_result = await self.llama_manager.perform_reasoning_task(
                task=f"Research and analyze: {topic}",
                context=context
            )
            
            # Save research result to memory
            await self.memory_integration.memory_manager.add_memory(
                user=user,
                content=f"Research on {topic}: {research_result}",
                metadata={"type": "research", "topic": topic},
                source="deep_research",
                tags=["research", "analysis", topic.lower()],
                privacy_level="private"
            )
            
            return research_result
        else:
            return f"I'd like to research {topic} for you, but I'm having trouble accessing my research capabilities right now. Please try again in a moment."

    async def _save_message(self, content: str, role: str, session_id: int):
        """Save message to database."""
        try:
            message = Message(
                session_id=session_id,
                role=role,
                content=content,
                timestamp=datetime.utcnow()
            )
            self.db.add(message)
            self.db.commit()
        except Exception as e:
            logger.error(f"Error saving message: {e}")

    # Enhanced capabilities
    async def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment using the best available method."""
        # Try LLaMA first for better offline capability
        await self.ensure_local_model_loaded()
        
        if self.llama_manager.is_loaded:
            try:
                prompt = f"Analyze the sentiment of this text and respond with only a JSON object containing 'positive', 'negative', and 'neutral' scores between 0 and 1:\n\n{text}"
                response = await self.llama_manager.generate_intelligent_response(
                    prompt, temperature=0.1, max_tokens=100
                )
                
                import json
                return json.loads(response)
            except:
                pass
        
        # Fallback to core engine
        return await self.core_engine.analyze_sentiment(text)

    def get_system_status(self) -> Dict:
        """Get comprehensive system status."""
        return {
            "offline_mode": self.offline_mode,
            "openai_available": self.core_engine.is_openai_available(),
            "llama_loaded": self.llama_manager.is_loaded,
            "llama_info": self.llama_manager.get_model_info(),
            "local_models": self.model_manager.list_loaded_models(),
            "memory_enabled": self.memory_integration.is_memory_enabled(),
            "prefer_local": self.prefer_local
        }

    def enable_offline_mode(self):
        """Enable offline-only mode."""
        self.offline_mode = True
        self.prefer_local = True
        logger.info("🌐 Offline mode enabled - will use local models only")

    def disable_offline_mode(self):
        """Disable offline mode (allow online models)."""
        self.offline_mode = False
        logger.info("🌐 Offline mode disabled - online models allowed")

    def set_local_preference(self, prefer_local: bool):
        """Set preference for local vs online models."""
        self.prefer_local = prefer_local
        logger.info(f"Model preference updated: {'Local' if prefer_local else 'Online'} models preferred")

    # Existing methods with enhancements
    async def load_model(self, model_path: str, model_name: str = None) -> bool:
        """Load a new model (supports both traditional and LLaMA models)."""
        if "llama" in model_path.lower():
            return await self.llama_manager.load_llama_model()
        else:
            try:
                self.model_manager.load_model(model_path, model_name)
                return True
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                return False

    def switch_model(self, model_name: str) -> bool:
        """Switch to a different loaded model."""
        return self.model_manager.switch_model(model_name)

    def get_stats(self) -> ModelStats:
        """Get current model statistics."""
        return self.statistics.get_stats()

    def get_detailed_stats(self) -> Dict:
        """Get detailed statistics."""
        return self.statistics.get_detailed_stats()

    def get_loaded_models(self) -> List[str]:
        """Get list of loaded models."""
        return self.model_manager.list_loaded_models()

    def get_model_info(self, model_name: str) -> Dict:
        """Get information about a specific model."""
        return self.model_manager.get_model_info(model_name)

    async def unload_model(self, model_name: str) -> bool:
        """Unload a model."""
        return self.model_manager.unload_model(model_name)

    def enable_memory(self):
        """Enable memory integration."""
        self.memory_integration.enable_memory()

    def disable_memory(self):
        """Disable memory integration."""
        self.memory_integration.disable_memory()

    def is_memory_enabled(self) -> bool:
        """Check if memory integration is enabled."""
        return self.memory_integration.is_memory_enabled()

    async def get_conversation_history(self, user: User, session_id: int = None) -> List[Dict]:
        """Get conversation history from memory."""
        return await self.memory_integration.get_conversation_history(user, session_id)

    async def get_user_interests(self, user: User) -> Dict:
        """Get user's interests from memory analysis."""
        return await self.memory_integration.summarize_user_interests(user)

    def optimize_memory(self):
        """Optimize system memory usage."""
        self.model_manager.optimize_memory()

    def get_memory_usage(self) -> Dict:
        """Get current memory usage."""
        return self.model_manager.get_memory_usage()

    def check_model_compatibility(self, model_path: str) -> Dict:
        """Check if a model is compatible with current hardware."""
        return self.model_manager.check_model_compatibility(model_path)

    def reset_statistics(self):
        """Reset all statistics."""
        self.statistics.reset_stats()

    def export_stats(self) -> Dict:
        """Export statistics for backup."""
        return self.statistics.export_stats()

    def import_stats(self, stats_data: Dict):
        """Import previously exported statistics."""
        self.statistics.import_stats(stats_data)


def get_llm_engine(db: Session) -> LLMEngine:
    """Get or create the LLM engine singleton instance."""
    # This could be enhanced with proper singleton pattern if needed
    return LLMEngine(db) 