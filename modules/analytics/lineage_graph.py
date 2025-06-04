import networkx as nx
from typing import List, Dict, Any
from .lineage_models import LineageTrace, DataSource, ReasoningStep

class LineageGraphManager:
    """Manages lineage graph operations and analysis"""
    
    def __init__(self):
        self.lineage_graph = nx.DiGraph()
    
    def build_trace_graph(self, trace: LineageTrace):
        """Build graph representation for a lineage trace"""
        # Add source nodes
        for source in trace.sources:
            self.lineage_graph.add_node(source.id, 
                                       type="source", 
                                       source_type=source.source_type.value,
                                       description=source.description)
        
        # Add reasoning nodes and connections
        for step in trace.reasoning_steps:
            self.lineage_graph.add_node(step.id, 
                                       type="reasoning", 
                                       step_type=step.step_type,
                                       reasoning=step.reasoning_text)
            
            # Connect input sources to this reasoning step
            for source_id in step.input_sources:
                self.lineage_graph.add_edge(source_id, step.id)
        
        # Add final answer node
        answer_id = f"{trace.trace_id}_answer"
        self.lineage_graph.add_node(answer_id, 
                                   type="answer", 
                                   content=trace.final_answer)
        
        # Connect reasoning steps to final answer
        for step in trace.reasoning_steps:
            self.lineage_graph.add_edge(step.id, answer_id)
    
    def get_lineage_paths(self, trace: LineageTrace) -> List[List[str]]:
        """Build all lineage paths from sources to answer"""
        paths = []
        answer_id = f"{trace.trace_id}_answer"
        
        # Find all paths from sources to the final answer
        for source in trace.sources:
            try:
                source_paths = list(nx.all_simple_paths(
                    self.lineage_graph, source.id, answer_id
                ))
                paths.extend(source_paths)
            except nx.NetworkXNoPath:
                # Source not connected to answer
                pass
        
        return paths
    
    def export_graphml(self, trace: LineageTrace) -> str:
        """Export lineage graph as GraphML"""
        subgraph = self.lineage_graph.subgraph(
            [s.id for s in trace.sources] + 
            [r.id for r in trace.reasoning_steps] + 
            [f"{trace.trace_id}_answer"]
        )
        return "\n".join(nx.generate_graphml(subgraph))
    
    def analyze_graph_structure(self, trace: LineageTrace) -> Dict[str, Any]:
        """Analyze the structure of the lineage graph"""
        graph_nodes = ([s.id for s in trace.sources] + 
                      [r.id for r in trace.reasoning_steps] + 
                      [f"{trace.trace_id}_answer"])
        
        subgraph = self.lineage_graph.subgraph(graph_nodes)
        
        return {
            "total_nodes": len(graph_nodes),
            "total_edges": subgraph.number_of_edges(),
            "source_nodes": len(trace.sources),
            "reasoning_nodes": len(trace.reasoning_steps),
            "is_connected": nx.is_weakly_connected(subgraph),
            "has_cycles": not nx.is_directed_acyclic_graph(subgraph),
            "depth": self._calculate_graph_depth(trace),
            "branching_factor": self._calculate_branching_factor(trace)
        }
    
    def _calculate_graph_depth(self, trace: LineageTrace) -> int:
        """Calculate the maximum depth of the reasoning graph"""
        if not trace.reasoning_steps:
            return 1  # Just sources to answer
        
        max_depth = 0
        for source in trace.sources:
            try:
                answer_id = f"{trace.trace_id}_answer"
                shortest_path = nx.shortest_path_length(
                    self.lineage_graph, source.id, answer_id
                )
                max_depth = max(max_depth, shortest_path)
            except nx.NetworkXNoPath:
                pass
        
        return max_depth
    
    def _calculate_branching_factor(self, trace: LineageTrace) -> float:
        """Calculate average branching factor of reasoning steps"""
        if not trace.reasoning_steps:
            return 0.0
        
        total_inputs = sum(len(step.input_sources) for step in trace.reasoning_steps)
        return total_inputs / len(trace.reasoning_steps) 