from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from core.database import get_db, User
from core.security import get_current_user
from modules.ai.persona_manager import get_persona_manager
from .schemas import PersonaSwitchRequest, CreatePersonaRequest

router = APIRouter(prefix="/personas", tags=["persona-management"])

@router.get("")
async def list_personas(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List available personas"""
    persona_manager = get_persona_manager(db)
    personas = persona_manager.list_available_personas()
    
    return {"personas": personas}

@router.post("/switch")
async def switch_persona(
    request: PersonaSwitchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Switch to a different persona"""
    persona_manager = get_persona_manager(db)
    success = persona_manager.switch_persona(request.persona_name, current_user.id)
    
    if not success:
        raise HTTPException(status_code=400, detail=f"Persona '{request.persona_name}' not found")
    
    current_persona = persona_manager.get_current_persona()
    return {
        "message": f"Switched to {current_persona.name}",
        "persona": {
            "name": current_persona.name,
            "type": current_persona.persona_type.value,
            "description": current_persona.description
        }
    }

@router.get("/current")
async def get_current_persona(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get currently active persona"""
    persona_manager = get_persona_manager(db)
    current_persona = persona_manager.get_current_persona()
    
    if not current_persona:
        return {"persona": None}
    
    return {
        "persona": {
            "name": current_persona.name,
            "type": current_persona.persona_type.value,
            "description": current_persona.description,
            "expertise": current_persona.expertise_areas,
            "style": current_persona.communication_style
        }
    }

@router.get("/suggestions")
async def get_persona_suggestions(
    query: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get persona suggestions for a query"""
    persona_manager = get_persona_manager(db)
    suggestions = persona_manager.get_persona_suggestions(query)
    
    return {
        "query": query,
        "suggestions": [
            {
                "persona_id": persona_id,
                "score": score,
                "explanation": explanation
            }
            for persona_id, score, explanation in suggestions
        ]
    }

@router.post("/custom")
async def create_custom_persona(
    request: CreatePersonaRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a custom persona"""
    persona_manager = get_persona_manager(db)
    persona_id = persona_manager.create_custom_persona(request.persona_data, current_user.id)
    
    return {
        "persona_id": persona_id,
        "message": "Custom persona created successfully"
    } 