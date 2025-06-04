import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from core.database import Session
from .persona_definitions import PersonaType, PersonaProfile, PersonaProfileFactory
from .persona_analyzer import PersonaAnalyzer, PersonaStyleAdapter

logger = logging.getLogger(__name__)

class PersonaManager:
    """Role/persona switching system (Feature 201)"""
    
    def __init__(self, db: Session):
        self.db = db
        self.current_persona: Optional[PersonaProfile] = None
        self.personas: Dict[str, PersonaProfile] = PersonaProfileFactory.create_default_personas()
        self.user_preferences: Dict[int, Dict[str, Any]] = {}
        self.analyzer = PersonaAnalyzer(self.personas)
        
    def switch_persona(self, persona_name: str, user_id: Optional[int] = None) -> bool:
        """Switch to a different persona"""
        if persona_name not in self.personas:
            logger.warning(f"Persona '{persona_name}' not found")
            return False
            
        self.current_persona = self.personas[persona_name]
        logger.info(f"Switched to persona: {self.current_persona.name}")
        
        # Store user preference
        if user_id:
            if user_id not in self.user_preferences:
                self.user_preferences[user_id] = {}
            self.user_preferences[user_id]["current_persona"] = persona_name
            self.user_preferences[user_id]["last_switch"] = datetime.utcnow()
        
        return True
    
    def get_current_persona(self) -> Optional[PersonaProfile]:
        """Get the currently active persona"""
        return self.current_persona
    
    def get_persona_prompt(self, base_prompt: str) -> str:
        """Enhance prompt with current persona context"""
        if not self.current_persona:
            return base_prompt
        
        return PersonaStyleAdapter.get_persona_prompt(base_prompt, self.current_persona)
    
    def get_preferred_model(self) -> Optional[str]:
        """Get the preferred model for current persona"""
        if not self.current_persona or not self.current_persona.preferred_models:
            return None
        return self.current_persona.preferred_models[0]
    
    def create_custom_persona(self, persona_data: Dict[str, Any], user_id: Optional[int] = None) -> str:
        """Create a custom persona profile"""
        persona_id = f"custom_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        persona = PersonaProfile(
            name=persona_data.get("name", "Custom Persona"),
            persona_type=PersonaType(persona_data.get("type", "general")),
            description=persona_data.get("description", "Custom persona"),
            personality_traits=persona_data.get("traits", []),
            expertise_areas=persona_data.get("expertise", []),
            communication_style=persona_data.get("style", "balanced"),
            preferred_models=persona_data.get("models", ["gpt-3.5-turbo"]),
            system_prompt=persona_data.get("system_prompt", "You are a helpful assistant."),
            response_template=persona_data.get("template", "{content}"),
            knowledge_focus=persona_data.get("knowledge_focus", []),
            interaction_patterns=persona_data.get("patterns", {}),
            voice_tone=persona_data.get("voice_tone", "neutral"),
            formality_level=persona_data.get("formality", "balanced"),
            humor_level=persona_data.get("humor", "moderate")
        )
        
        self.personas[persona_id] = persona
        # Update analyzer with new persona
        self.analyzer = PersonaAnalyzer(self.personas)
        
        logger.info(f"Created custom persona: {persona_id}")
        return persona_id
    
    def list_available_personas(self) -> List[Dict[str, Any]]:
        """Get list of available personas"""
        return [
            {
                "id": pid,
                "name": persona.name,
                "type": persona.persona_type.value,
                "description": persona.description,
                "expertise": persona.expertise_areas,
                "style": persona.communication_style
            }
            for pid, persona in self.personas.items()
        ]
    
    def get_persona_suggestions(self, query: str) -> List[Tuple[str, float, str]]:
        """Suggest best personas for a given query"""
        return self.analyzer.get_persona_suggestions(query)
    
    def update_persona_preferences(self, user_id: int, preferences: Dict[str, Any]):
        """Update user's persona preferences"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}
        
        self.user_preferences[user_id].update(preferences)
        self.user_preferences[user_id]["updated_at"] = datetime.utcnow()
    
    def get_user_persona_history(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's persona usage history"""
        # In a real implementation, this would query the database
        # For now, return empty list
        return []
    
    def adapt_response_style(self, content: str) -> str:
        """Adapt response content to current persona style"""
        if not self.current_persona:
            return content
        
        return PersonaStyleAdapter.adapt_response_style(content, self.current_persona)

# Singleton instance
_persona_manager = None

def get_persona_manager(db: Session) -> PersonaManager:
    """Get or create the persona manager instance"""
    global _persona_manager
    if _persona_manager is None:
        _persona_manager = PersonaManager(db)
    return _persona_manager 