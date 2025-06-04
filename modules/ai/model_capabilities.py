from typing import List
from .domain_detection import TaskDomain

class ModelCapability:
    """Model capability definition"""
    def __init__(self, model_name: str, domains: List[TaskDomain], 
                 performance_score: float, cost_score: float, speed_score: float):
        self.model_name = model_name
        self.domains = domains
        self.performance_score = performance_score  # 0-1, higher is better
        self.cost_score = cost_score  # 0-1, lower is better (cheaper)
        self.speed_score = speed_score  # 0-1, higher is faster

class ModelCapabilityManager:
    """Manages model capabilities and selection logic"""
    
    def __init__(self):
        self.model_capabilities = self._initialize_default_capabilities()
    
    def _initialize_default_capabilities(self):
        """Initialize default model capabilities"""
        return {
            "gpt-4": ModelCapability(
                "gpt-4",
                [TaskDomain.REASONING, TaskDomain.TECHNICAL, TaskDomain.SCIENTIFIC, 
                 TaskDomain.BUSINESS, TaskDomain.EDUCATIONAL],
                performance_score=0.95, cost_score=0.3, speed_score=0.6
            ),
            "gpt-3.5-turbo": ModelCapability(
                "gpt-3.5-turbo",
                [TaskDomain.CONVERSATIONAL, TaskDomain.GENERAL, TaskDomain.BUSINESS],
                performance_score=0.8, cost_score=0.8, speed_score=0.9
            ),
            "claude-3": ModelCapability(
                "claude-3",
                [TaskDomain.CREATIVE, TaskDomain.ANALYTICAL, TaskDomain.EDUCATIONAL],
                performance_score=0.9, cost_score=0.4, speed_score=0.7
            ),
            "local_code": ModelCapability(
                "local_code",
                [TaskDomain.CODE, TaskDomain.TECHNICAL],
                performance_score=0.85, cost_score=1.0, speed_score=0.8
            ),
            "local_general": ModelCapability(
                "local_general",
                [TaskDomain.GENERAL, TaskDomain.CONVERSATIONAL],
                performance_score=0.7, cost_score=1.0, speed_score=0.9
            )
        }
    
    def get_suitable_models(self, domain: TaskDomain):
        """Get models that support this domain"""
        suitable_models = [
            (name, cap) for name, cap in self.model_capabilities.items()
            if domain in cap.domains
        ]
        
        if not suitable_models:
            # Fallback to general-purpose models
            suitable_models = [
                (name, cap) for name, cap in self.model_capabilities.items()
                if TaskDomain.GENERAL in cap.domains
            ]
        
        return suitable_models
    
    def score_model(self, capability: ModelCapability, preference: str = "balanced"):
        """Score a model based on preference"""
        if preference == "performance":
            return capability.performance_score
        elif preference == "speed":
            return capability.speed_score
        elif preference == "cost":
            return 1.0 - capability.cost_score  # Invert cost (lower is better)
        else:  # balanced
            return (capability.performance_score + 
                   capability.speed_score + 
                   (1.0 - capability.cost_score)) / 3
    
    def add_custom_model(self, name: str, domains: List[TaskDomain],
                        performance: float, cost: float, speed: float):
        """Add a custom model configuration"""
        self.model_capabilities[name] = ModelCapability(
            name, domains, performance, cost, speed
        )
    
    def update_model_capability(self, name: str, **kwargs):
        """Update model capability parameters"""
        if name in self.model_capabilities:
            capability = self.model_capabilities[name]
            
            if 'domains' in kwargs:
                capability.domains = kwargs['domains']
            if 'performance_score' in kwargs:
                capability.performance_score = kwargs['performance_score']
            if 'cost_score' in kwargs:
                capability.cost_score = kwargs['cost_score']
            if 'speed_score' in kwargs:
                capability.speed_score = kwargs['speed_score'] 