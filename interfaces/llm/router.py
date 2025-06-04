from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Union
import asyncio
import time
from datetime import datetime

from core.database import get_db, User
from core.security import get_current_active_user, get_current_admin_user
from modules.llm_engine.engine import get_llm_engine
from modules.llm_engine.schemas import (
    GenerationRequest,
    GenerationResponse,
    ModelConfig,
    SentimentAnalysis,
    ModelStats,
    ModelLoadRequest,
    SystemStatusResponse,
    ResearchRequest,
    ResearchResponse,
    SentimentRequest,
    SentimentResponse
)

router = APIRouter()

@router.post("/generate", response_model=GenerationResponse)
async def generate_response(
    request: GenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate intelligent response using the best available model with memory enhancement."""
    try:
        llm_engine = get_llm_engine(db)
        
        response = await llm_engine.generate_response(
            prompt=request.prompt,
            model=request.model,
            user=current_user,
            session_id=request.session_id,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stream=request.stream,
            use_memory=request.use_memory,
            force_offline=request.force_offline
        )
        
        return GenerationResponse(
            response=str(response),
            model_used=request.model or "auto-selected",
            tokens_used=len(str(response).split()),
            offline_mode=llm_engine.offline_mode,
            memory_enhanced=request.use_memory,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@router.post("/research", response_model=ResearchResponse)
async def perform_deep_research(
    request: ResearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Perform deep research using AI reasoning and memory analysis."""
    try:
        llm_engine = get_llm_engine(db)
        
        research_result = await llm_engine.perform_deep_research(
            topic=request.topic,
            user=current_user
        )
        
        return ResearchResponse(
            topic=request.topic,
            research_result=research_result,
            sources_consulted=["internal_memory", "ai_reasoning"],
            confidence_score=0.85,  # Could be enhanced with actual confidence scoring
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")

@router.post("/sentiment", response_model=SentimentResponse)
async def analyze_sentiment(
    request: SentimentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Analyze sentiment of text using AI models."""
    try:
        llm_engine = get_llm_engine(db)
        
        sentiment_scores = await llm_engine.analyze_sentiment(request.text)
        
        return SentimentResponse(
            text=request.text,
            sentiment_scores=sentiment_scores,
            dominant_sentiment=max(sentiment_scores.items(), key=lambda x: x[1])[0],
            confidence=max(sentiment_scores.values()),
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {str(e)}")

@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive LLM system status."""
    try:
        llm_engine = get_llm_engine(db)
        status = llm_engine.get_system_status()
        
        return SystemStatusResponse(
            offline_mode=status["offline_mode"],
            openai_available=status["openai_available"],
            llama_loaded=status["llama_loaded"],
            llama_info=status["llama_info"],
            local_models=status["local_models"],
            memory_enabled=status["memory_enabled"],
            prefer_local=status["prefer_local"],
            system_stats=llm_engine.get_detailed_stats(),
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@router.post("/models/load")
async def load_model(
    request: ModelLoadRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Load a new model (LLaMA or traditional)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        llm_engine = get_llm_engine(db)
        
        success = await llm_engine.load_model(
            model_path=request.model_path,
            model_name=request.model_name
        )
        
        if success:
            return {"message": f"Model {request.model_name or request.model_path} loaded successfully"}
        else:
            raise HTTPException(status_code=500, detail="Model loading failed")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model loading failed: {str(e)}")

@router.post("/models/unload/{model_name}")
async def unload_model(
    model_name: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Unload a model to free memory."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        llm_engine = get_llm_engine(db)
        
        success = await llm_engine.unload_model(model_name)
        
        if success:
            return {"message": f"Model {model_name} unloaded successfully"}
        else:
            raise HTTPException(status_code=404, detail="Model not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model unloading failed: {str(e)}")

@router.get("/models")
async def list_models(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all loaded models and their information."""
    try:
        llm_engine = get_llm_engine(db)
        
        models = {}
        
        # Local models
        for model_name in llm_engine.get_loaded_models():
            models[model_name] = llm_engine.get_model_info(model_name)
        
        # LLaMA model info
        llama_info = llm_engine.llama_manager.get_model_info()
        if llama_info.get("status") == "loaded":
            models["llama-3-13b"] = llama_info
        
        return {"models": models}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")

@router.post("/config/offline-mode")
async def set_offline_mode(
    enabled: bool = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Enable or disable offline-only mode."""
    try:
        llm_engine = get_llm_engine(db)
        
        if enabled:
            llm_engine.enable_offline_mode()
        else:
            llm_engine.disable_offline_mode()
        
        return {"message": f"Offline mode {'enabled' if enabled else 'disabled'}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set offline mode: {str(e)}")

@router.post("/config/local-preference")
async def set_local_preference(
    prefer_local: bool = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Set preference for local vs online models."""
    try:
        llm_engine = get_llm_engine(db)
        llm_engine.set_local_preference(prefer_local)
        
        return {"message": f"Local preference {'enabled' if prefer_local else 'disabled'}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set preference: {str(e)}")

@router.post("/llama/load")
async def load_llama_model(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Load LLaMA 3 13B model for offline operation."""
    try:
        llm_engine = get_llm_engine(db)
        
        success = await llm_engine.llama_manager.load_llama_model()
        
        if success:
            model_info = llm_engine.llama_manager.get_model_info()
            return {
                "message": "LLaMA model loaded successfully",
                "model_info": model_info
            }
        else:
            raise HTTPException(status_code=500, detail="LLaMA loading failed")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLaMA loading failed: {str(e)}")

@router.post("/llama/unload")
async def unload_llama_model(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Unload LLaMA model to free memory."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        llm_engine = get_llm_engine(db)
        llm_engine.llama_manager.unload_model()
        
        return {"message": "LLaMA model unloaded successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLaMA unloading failed: {str(e)}")

@router.get("/stats")
async def get_llm_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed LLM engine statistics."""
    try:
        llm_engine = get_llm_engine(db)
        
        return {
            "basic_stats": llm_engine.get_stats(),
            "detailed_stats": llm_engine.get_detailed_stats(),
            "system_status": llm_engine.get_system_status()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@router.post("/memory/toggle")
async def toggle_memory(
    enabled: bool = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Enable or disable memory integration."""
    try:
        llm_engine = get_llm_engine(db)
        
        if enabled:
            llm_engine.enable_memory()
        else:
            llm_engine.disable_memory()
        
        return {"message": f"Memory integration {'enabled' if enabled else 'disabled'}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle memory: {str(e)}")

@router.get("/conversation/history")
async def get_conversation_history(
    session_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get conversation history from memory."""
    try:
        llm_engine = get_llm_engine(db)
        
        history = await llm_engine.get_conversation_history(
            user=current_user,
            session_id=session_id
        )
        
        return {"conversation_history": history}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")

@router.get("/user/interests")
async def get_user_interests(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's interests based on memory analysis."""
    try:
        llm_engine = get_llm_engine(db)
        
        interests = await llm_engine.get_user_interests(current_user)
        
        return {"user_interests": interests}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get interests: {str(e)}") 