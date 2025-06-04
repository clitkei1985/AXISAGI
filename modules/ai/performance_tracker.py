import logging
from typing import Dict, List, Tuple
from datetime import datetime
from .domain_detection import TaskDomain

logger = logging.getLogger(__name__)

class PerformanceTracker:
    """Tracks model performance for adaptive selection"""
    
    def __init__(self):
        self.performance_history: Dict[str, List[Tuple[TaskDomain, float, datetime]]] = {}
    
    def record_performance(self, model_name: str, domain: TaskDomain, 
                          performance_score: float):
        """Record model performance for future selection"""
        if model_name not in self.performance_history:
            self.performance_history[model_name] = []
        
        self.performance_history[model_name].append(
            (domain, performance_score, datetime.utcnow())
        )
        
        # Keep only recent history (last 100 records per model)
        if len(self.performance_history[model_name]) > 100:
            self.performance_history[model_name] = \
                self.performance_history[model_name][-100:]
        
        logger.info(f"Recorded performance for {model_name}: {performance_score:.2f}")
    
    def get_historical_performance(self, model_name: str, domain: TaskDomain) -> float:
        """Get historical performance score for a model and domain"""
        if model_name not in self.performance_history:
            return 0.0
        
        domain_history = [
            perf for d, perf, _ in self.performance_history[model_name]
            if d == domain
        ]
        
        if not domain_history:
            return 0.0
        
        return sum(domain_history) / len(domain_history)
    
    def adjust_score_with_history(self, base_score: float, model_name: str, 
                                 domain: TaskDomain, weight: float = 0.3) -> float:
        """Adjust base score with historical performance"""
        historical_score = self.get_historical_performance(model_name, domain)
        if historical_score == 0.0:
            return base_score
        
        return base_score * (1 - weight) + historical_score * weight
    
    def get_performance_summary(self, model_name: str) -> Dict:
        """Get performance summary for a model"""
        if model_name not in self.performance_history:
            return {}
        
        history = self.performance_history[model_name]
        domain_stats = {}
        
        for domain, score, timestamp in history:
            if domain not in domain_stats:
                domain_stats[domain] = []
            domain_stats[domain].append(score)
        
        summary = {}
        for domain, scores in domain_stats.items():
            summary[domain.value] = {
                "average": sum(scores) / len(scores),
                "count": len(scores),
                "best": max(scores),
                "worst": min(scores)
            }
        
        return summary 