from typing import Dict, Any, List
from datetime import datetime
from .lineage_models import LineageTrace

class LineageValidator:
    """Validates lineage traces for completeness and consistency"""
    
    def validate_lineage(self, trace: LineageTrace) -> Dict[str, Any]:
        """Validate the completeness and consistency of lineage"""
        errors = []
        warnings = []
        
        # Check for orphaned reasoning steps
        source_ids = {s.id for s in trace.sources}
        reasoning_ids = {r.id for r in trace.reasoning_steps}
        
        for step in trace.reasoning_steps:
            for input_id in step.input_sources:
                if input_id not in source_ids and input_id not in reasoning_ids:
                    errors.append(f"Reasoning step {step.id} references unknown source {input_id}")
        
        # Check confidence scores
        low_confidence_items = []
        for source in trace.sources:
            if source.confidence < 0.5:
                low_confidence_items.append(f"Source: {source.description}")
        
        for step in trace.reasoning_steps:
            if step.confidence < 0.5:
                low_confidence_items.append(f"Reasoning: {step.reasoning_text[:50]}...")
        
        if low_confidence_items:
            warnings.append(f"Low confidence items: {', '.join(low_confidence_items)}")
        
        # Check temporal consistency
        timestamps = [s.timestamp for s in trace.sources] + [r.timestamp for r in trace.reasoning_steps]
        if not all(t <= trace.created_at for t in timestamps):
            errors.append("Some sources/reasoning steps have future timestamps")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "completeness_score": self._calculate_completeness_score(trace),
            "consistency_score": self._calculate_consistency_score(trace)
        }
    
    def _calculate_completeness_score(self, trace: LineageTrace) -> float:
        """Calculate how complete the lineage trace is"""
        score = 0.0
        
        # Has sources
        if trace.sources:
            score += 0.3
        
        # Has reasoning steps
        if trace.reasoning_steps:
            score += 0.3
        
        # Has final answer
        if trace.final_answer:
            score += 0.2
        
        # Sources are well-documented
        well_documented_sources = sum(1 for s in trace.sources if len(s.description) > 10)
        if trace.sources:
            score += 0.1 * (well_documented_sources / len(trace.sources))
        
        # Reasoning steps are well-documented
        well_documented_reasoning = sum(1 for r in trace.reasoning_steps if len(r.reasoning_text) > 20)
        if trace.reasoning_steps:
            score += 0.1 * (well_documented_reasoning / len(trace.reasoning_steps))
        
        return score
    
    def _calculate_consistency_score(self, trace: LineageTrace) -> float:
        """Calculate how consistent the lineage trace is"""
        score = 1.0  # Start with perfect score, subtract for inconsistencies
        
        # Check timestamp consistency
        all_timestamps = ([s.timestamp for s in trace.sources] + 
                         [r.timestamp for r in trace.reasoning_steps] + 
                         [trace.created_at])
        
        if not all(t1 <= t2 for t1, t2 in zip(all_timestamps[:-1], all_timestamps[1:])):
            score -= 0.2
        
        # Check confidence consistency
        confidence_values = ([s.confidence for s in trace.sources] + 
                            [r.confidence for r in trace.reasoning_steps])
        
        if any(c < 0 or c > 1 for c in confidence_values):
            score -= 0.3
        
        # Check source references in reasoning
        source_ids = {s.id for s in trace.sources}
        reasoning_ids = {r.id for r in trace.reasoning_steps}
        
        for step in trace.reasoning_steps:
            for input_id in step.input_sources:
                if input_id not in source_ids and input_id not in reasoning_ids:
                    score -= 0.1
        
        return max(0.0, score)
    
    def calculate_data_freshness(self, trace: LineageTrace) -> float:
        """Calculate how fresh the data sources are"""
        if not trace.sources:
            return 0.0
        
        now = datetime.utcnow()
        freshness_scores = []
        
        for source in trace.sources:
            age_hours = (now - source.timestamp).total_seconds() / 3600
            # Fresher data gets higher score (exponential decay)
            freshness = max(0.0, 1.0 - (age_hours / 168))  # 1 week half-life
            freshness_scores.append(freshness)
        
        return sum(freshness_scores) / len(freshness_scores)
    
    def calculate_trust_score(self, trace: LineageTrace) -> float:
        """Calculate overall trust score for the trace"""
        source_confidence = sum(s.confidence for s in trace.sources) / len(trace.sources) if trace.sources else 0
        reasoning_confidence = sum(r.confidence for r in trace.reasoning_steps) / len(trace.reasoning_steps) if trace.reasoning_steps else 0
        freshness_score = self.calculate_data_freshness(trace)
        
        # Weighted combination
        trust_score = (source_confidence * 0.4 + 
                      reasoning_confidence * 0.4 + 
                      freshness_score * 0.2)
        
        return min(1.0, max(0.0, trust_score)) 