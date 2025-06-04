import logging
import json
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import asdict
from sqlalchemy.orm import Session
from core.database import get_db
from .lineage_models import SourceType, DataSource, ReasoningStep, LineageTrace
from .lineage_graph import LineageGraphManager
from .lineage_validator import LineageValidator

logger = logging.getLogger(__name__)

class LineageTracker:
    """Full data lineage tracking system (Feature 196)"""
    
    def __init__(self, db: Session):
        self.db = db
        self.active_traces: Dict[str, LineageTrace] = {}
        self.graph_manager = LineageGraphManager()
        self.validator = LineageValidator()
        
    def start_trace(self, query: str, user_id: Optional[int] = None, 
                   session_id: Optional[int] = None) -> str:
        """Start a new lineage trace"""
        trace_id = str(uuid.uuid4())
        
        trace = LineageTrace(
            trace_id=trace_id,
            query=query,
            final_answer="",
            sources=[],
            reasoning_steps=[],
            metadata={},
            created_at=datetime.utcnow(),
            user_id=user_id,
            session_id=session_id
        )
        
        self.active_traces[trace_id] = trace
        logger.info(f"Started lineage trace: {trace_id}")
        return trace_id
    
    def add_source(self, trace_id: str, source_type: SourceType, 
                  description: str, content: str, metadata: Dict[str, Any] = None,
                  confidence: float = 1.0) -> str:
        """Add a data source to the lineage trace"""
        if trace_id not in self.active_traces:
            raise ValueError(f"No active trace found: {trace_id}")
        
        source_id = str(uuid.uuid4())
        trace = self.active_traces[trace_id]
        
        source = DataSource(
            id=source_id,
            source_type=source_type,
            description=description,
            content=content,
            metadata=metadata or {},
            timestamp=datetime.utcnow(),
            confidence=confidence,
            user_id=trace.user_id,
            session_id=trace.session_id
        )
        
        trace.sources.append(source)
        logger.debug(f"Added source {source_id} to trace {trace_id}")
        return source_id
    
    def add_reasoning_step(self, trace_id: str, step_type: str, 
                          input_sources: List[str], output_data: str,
                          reasoning_text: str, confidence: float = 1.0,
                          model_used: Optional[str] = None) -> str:
        """Add a reasoning step to the lineage trace"""
        if trace_id not in self.active_traces:
            raise ValueError(f"No active trace found: {trace_id}")
        
        step_id = str(uuid.uuid4())
        trace = self.active_traces[trace_id]
        
        step = ReasoningStep(
            id=step_id,
            step_type=step_type,
            input_sources=input_sources,
            output_data=output_data,
            reasoning_text=reasoning_text,
            confidence=confidence,
            timestamp=datetime.utcnow(),
            model_used=model_used
        )
        
        trace.reasoning_steps.append(step)
        logger.debug(f"Added reasoning step {step_id} to trace {trace_id}")
        return step_id
    
    def add_metadata(self, trace_id: str, key: str, value: Any):
        """Add metadata to the trace"""
        if trace_id not in self.active_traces:
            raise ValueError(f"No active trace found: {trace_id}")
        
        self.active_traces[trace_id].metadata[key] = value
    
    def finalize_trace(self, trace_id: str, final_answer: str) -> LineageTrace:
        """Finalize the lineage trace with the final answer"""
        if trace_id not in self.active_traces:
            raise ValueError(f"No active trace found: {trace_id}")
        
        trace = self.active_traces[trace_id]
        trace.final_answer = final_answer
        
        # Build graph representation
        self.graph_manager.build_trace_graph(trace)
        
        # Store in persistent storage
        self._save_trace(trace)
        
        # Remove from active traces
        del self.active_traces[trace_id]
        
        logger.info(f"Finalized lineage trace: {trace_id}")
        return trace
    
    def get_trace_summary(self, trace_id: str) -> Dict[str, Any]:
        """Get a summary of the lineage trace"""
        trace = self._load_trace(trace_id)
        if not trace:
            return {}
        
        return {
            "trace_id": trace.trace_id,
            "query": trace.query,
            "final_answer": trace.final_answer,
            "num_sources": len(trace.sources),
            "num_reasoning_steps": len(trace.reasoning_steps),
            "source_types": list(set(s.source_type.value for s in trace.sources)),
            "confidence_scores": [s.confidence for s in trace.sources] + 
                               [r.confidence for r in trace.reasoning_steps],
            "created_at": trace.created_at.isoformat(),
            "metadata": trace.metadata
        }
    
    def get_detailed_lineage(self, trace_id: str) -> Dict[str, Any]:
        """Get detailed lineage information"""
        trace = self._load_trace(trace_id)
        if not trace:
            return {}
        
        # Build lineage paths using graph manager
        lineage_paths = self.graph_manager.get_lineage_paths(trace)
        
        return {
            "trace": asdict(trace),
            "lineage_paths": lineage_paths,
            "source_confidence_avg": sum(s.confidence for s in trace.sources) / len(trace.sources) if trace.sources else 0,
            "reasoning_confidence_avg": sum(r.confidence for r in trace.reasoning_steps) / len(trace.reasoning_steps) if trace.reasoning_steps else 0,
            "data_freshness": self.validator.calculate_data_freshness(trace),
            "trust_score": self.validator.calculate_trust_score(trace),
            "graph_analysis": self.graph_manager.analyze_graph_structure(trace)
        }
    
    def find_traces_by_source(self, source_content: str, source_type: Optional[SourceType] = None) -> List[str]:
        """Find all traces that used a specific source"""
        matching_traces = []
        
        for trace_id, trace in self.active_traces.items():
            for source in trace.sources:
                if source.content == source_content:
                    if source_type is None or source.source_type == source_type:
                        matching_traces.append(trace_id)
                        break
        
        return matching_traces
    
    def validate_lineage(self, trace_id: str) -> Dict[str, Any]:
        """Validate the completeness and consistency of lineage"""
        trace = self._load_trace(trace_id)
        if not trace:
            return {"valid": False, "errors": ["Trace not found"]}
        
        return self.validator.validate_lineage(trace)
    
    def export_lineage(self, trace_id: str, format: str = "json") -> str:
        """Export lineage trace in specified format"""
        trace = self._load_trace(trace_id)
        if not trace:
            return ""
        
        if format == "json":
            return json.dumps(asdict(trace), default=str, indent=2)
        elif format == "graphml":
            return self.graph_manager.export_graphml(trace)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _save_trace(self, trace: LineageTrace):
        """Save trace to persistent storage"""
        # In a real implementation, save to database
        # For now, we'll keep in memory
        pass
    
    def _load_trace(self, trace_id: str) -> Optional[LineageTrace]:
        """Load trace from persistent storage"""
        # Check active traces first
        if trace_id in self.active_traces:
            return self.active_traces[trace_id]
        
        # In a real implementation, load from database
        return None

# Singleton instance
_lineage_tracker = None

def get_lineage_tracker(db: Session) -> LineageTracker:
    """Get or create the lineage tracker instance"""
    global _lineage_tracker
    if _lineage_tracker is None:
        _lineage_tracker = LineageTracker(db)
    return _lineage_tracker 