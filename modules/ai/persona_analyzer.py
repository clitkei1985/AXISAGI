from typing import List, Tuple, Dict
from .persona_definitions import PersonaProfile, PersonaType

class PersonaAnalyzer:
    """Analyzes queries to suggest appropriate personas"""
    
    def __init__(self, personas: Dict[str, PersonaProfile]):
        self.personas = personas
    
    def get_persona_suggestions(self, query: str) -> List[Tuple[str, float, str]]:
        """Suggest best personas for a given query"""
        suggestions = []
        query_lower = query.lower()
        
        for persona_id, persona in self.personas.items():
            score = 0.0
            
            # Check expertise match
            for expertise in persona.expertise_areas:
                if expertise.lower() in query_lower:
                    score += 0.3
            
            # Check knowledge focus match
            for knowledge in persona.knowledge_focus:
                if knowledge.lower() in query_lower:
                    score += 0.2
            
            # Check personality trait relevance
            trait_keywords = {
                "creative": ["design", "art", "creative", "imagine"],
                "analytical": ["analyze", "data", "research", "study"],
                "technical": ["code", "program", "debug", "develop"],
                "educational": ["explain", "learn", "teach", "understand"]
            }
            
            for trait in persona.personality_traits:
                keywords = trait_keywords.get(trait, [trait])
                for keyword in keywords:
                    if keyword in query_lower:
                        score += 0.1
            
            if score > 0:
                explanation = f"Matches expertise in {', '.join(persona.expertise_areas[:2])}"
                suggestions.append((persona_id, score, explanation))
        
        # Sort by score descending
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return suggestions[:3]  # Top 3 suggestions

class PersonaStyleAdapter:
    """Adapts response content to persona style"""
    
    @staticmethod
    def adapt_response_style(content: str, persona: PersonaProfile) -> str:
        """Adapt response content to current persona style"""
        # Apply persona-specific response template
        if "{content}" in persona.response_template:
            formatted_content = persona.response_template.format(
                content=content,
                confidence="high",  # Could be dynamic
                explanation="",
                insights="",
                language="python"  # Could be detected
            )
        else:
            formatted_content = content
        
        # Apply tone and formality adjustments
        if persona.voice_tone == "warm_encouraging":
            formatted_content = f"😊 {formatted_content}"
        elif persona.voice_tone == "confident_technical":
            formatted_content = f"💻 {formatted_content}"
        elif persona.voice_tone == "expressive_flowing":
            formatted_content = f"🎨 {formatted_content}"
        
        return formatted_content
    
    @staticmethod
    def get_persona_prompt(base_prompt: str, persona: PersonaProfile) -> str:
        """Enhance prompt with persona context"""
        enhanced_prompt = f"{persona.system_prompt}\n\nUser request: {base_prompt}"
        
        # Apply persona-specific formatting
        if "{content}" in persona.response_template:
            return enhanced_prompt
        else:
            return f"{enhanced_prompt}\n\nRespond in the style of {persona.name}." 