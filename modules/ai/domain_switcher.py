import logging
from typing import Dict, Optional, List, Tuple
from core.config import settings
from modules.llm_engine.engine import get_llm_engine
from core.database import Session
from .domain_detection import TaskDomain, DomainDetector
from .model_capabilities import ModelCapabilityManager
from .performance_tracker import PerformanceTracker

logger = logging.getLogger(__name__)

class DomainSwitcher:
    """Intelligent LLM switching based on task domain (Feature 193)"""
    
    def __init__(self, db: Session):
        self.db = db
        self.llm_engine = get_llm_engine(db)
        self.domain_detector = DomainDetector()
        self.capability_manager = ModelCapabilityManager()
        self.performance_tracker = PerformanceTracker()
        
    def detect_task_domain(self, prompt: str, context: Optional[str] = None) -> TaskDomain:
        """Detect the primary task domain from prompt content"""
        return self.domain_detector.detect_task_domain(prompt, context)
    
    def select_best_model(self, domain: TaskDomain, 
                         preference: str = "balanced") -> str:
        """Select the best model for a given domain and preference"""
        
        suitable_models = self.capability_manager.get_suitable_models(domain)
        
        if not suitable_models:
            return settings.llm.default_model
        
        # Score models based on preference and history
        scored_models = []
        for name, capability in suitable_models:
            base_score = self.capability_manager.score_model(capability, preference)
            
            # Adjust with historical performance
            adjusted_score = self.performance_tracker.adjust_score_with_history(
                base_score, name, domain
            )
            
            scored_models.append((name, adjusted_score))
        
        # Return best scoring model
        best_model = max(scored_models, key=lambda x: x[1])[0]
        logger.info(f"Selected model {best_model} for domain {domain.value}")
        return best_model
    
    def auto_select_model(self, prompt: str, context: Optional[str] = None,
                         preference: str = "balanced") -> str:
        """Automatically select the best model for a prompt"""
        domain = self.detect_task_domain(prompt, context)
        return self.select_best_model(domain, preference)
    
    def record_performance(self, model_name: str, domain: TaskDomain, 
                          performance_score: float):
        """Record model performance for future selection"""
        self.performance_tracker.record_performance(model_name, domain, performance_score)
    
    def get_model_recommendations(self, prompt: str) -> List[Tuple[str, float, str]]:
        """Get ranked model recommendations with explanations"""
        domain = self.detect_task_domain(prompt)
        recommendations = []
        
        suitable_models = self.capability_manager.get_suitable_models(domain)
        
        for name, capability in suitable_models:
            score = self.capability_manager.score_model(capability)
            
            # Generate explanation
            strengths = []
            if capability.performance_score > 0.8:
                strengths.append("high performance")
            if capability.speed_score > 0.8:
                strengths.append("fast response")
            if capability.cost_score > 0.7:
                strengths.append("cost effective")
            
            explanation = f"Suitable for {domain.value} tasks. " + \
                        f"Strengths: {', '.join(strengths)}"
            
            recommendations.append((name, score, explanation))
        
        # Sort by score descending
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations
    
    def add_custom_model(self, name: str, domains: List[TaskDomain],
                        performance: float, cost: float, speed: float):
        """Add a custom model configuration"""
        self.capability_manager.add_custom_model(name, domains, performance, cost, speed)
        logger.info(f"Added custom model: {name}")
    
    def update_model_capability(self, name: str, **kwargs):
        """Update model capability parameters"""
        self.capability_manager.update_model_capability(name, **kwargs)
        logger.info(f"Updated model capability: {name}")
    
    def get_performance_summary(self, model_name: str) -> Dict:
        """Get performance summary for a model"""
        return self.performance_tracker.get_performance_summary(model_name)

# Singleton instance
_domain_switcher = None

def get_domain_switcher(db: Session) -> DomainSwitcher:
    """Get or create the domain switcher instance"""
    global _domain_switcher
    if _domain_switcher is None:
        _domain_switcher = DomainSwitcher(db)
    return _domain_switcher 