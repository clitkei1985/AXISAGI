"""
Multi-Agent Collaboration System for AXIS AI
Features: 186, 201, 64-65, 68-69
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import json

from core.config import settings
from core.database import Session, User
from modules.memory.memory_manager import MemoryManager
from .local_llm import CodeLlamaEngine

logger = logging.getLogger(__name__)

class AgentRole(Enum):
    """Available agent roles for specialized tasks."""
    CODER = "coder"           # Code generation and analysis
    RESEARCHER = "researcher"  # Information gathering and analysis
    ANALYST = "analyst"       # Data analysis and Python tasks
    CREATIVE = "creative"     # Creative writing and ideation
    COORDINATOR = "coordinator"  # Multi-agent coordination

@dataclass
class AgentTask:
    """Task structure for agent communication."""
    id: str
    role: AgentRole
    prompt: str
    context: Dict[str, Any]
    priority: int = 1
    dependencies: List[str] = None
    result: Optional[str] = None
    completed: bool = False
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class ChainOfThought:
    """Chain of thought tracking for reasoning visualization."""
    step: int
    agent: str
    thought: str
    action: str
    result: str
    confidence: float
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class MultiAgentSystem:
    """
    Multi-agent collaboration system with chain-of-thought reasoning.
    Features: 186, 64-65, 68-69, 201
    """
    
    def __init__(self, db: Session, memory_manager: MemoryManager, codellama_engine: CodeLlamaEngine):
        self.db = db
        self.memory_manager = memory_manager
        self.codellama_engine = codellama_engine
        
        # Agent specializations and personalities
        self.agent_configs = {
            AgentRole.CODER: {
                "model": settings.llm.agents.coder,
                "system_prompt": """You are a specialized coding agent. You excel at:
- Writing clean, efficient code
- Code analysis and debugging
- Architecture design
- Performance optimization
- Following best practices
Focus on technical accuracy and code quality.""",
                "temperature": 0.3,
                "max_tokens": 2048
            },
            AgentRole.RESEARCHER: {
                "model": settings.llm.agents.researcher,
                "system_prompt": """You are a research specialist agent. You excel at:
- Gathering and analyzing information
- Fact-checking and verification
- Academic and technical research
- Synthesizing complex information
- Critical thinking and analysis
Focus on accuracy and thorough investigation.""",
                "temperature": 0.4,
                "max_tokens": 2048
            },
            AgentRole.ANALYST: {
                "model": settings.llm.agents.analyst,
                "system_prompt": """You are a data analysis specialist. You excel at:
- Python data analysis and visualization
- Statistical analysis
- Pattern recognition
- Mathematical modeling
- Data interpretation
Focus on quantitative insights and data-driven conclusions.""",
                "temperature": 0.2,
                "max_tokens": 2048
            },
            AgentRole.CREATIVE: {
                "model": settings.llm.agents.creative,
                "system_prompt": """You are a creative thinking agent. You excel at:
- Creative writing and storytelling
- Brainstorming and ideation
- Innovative problem-solving
- Artistic and creative tasks
- Out-of-the-box thinking
Focus on originality and creative solutions.""",
                "temperature": 0.8,
                "max_tokens": 2048
            },
            AgentRole.COORDINATOR: {
                "model": settings.llm.base_model,
                "system_prompt": """You are the coordination agent. You excel at:
- Breaking down complex tasks
- Coordinating between specialists
- Synthesizing diverse perspectives
- Project management
- Decision making
Focus on efficiency and collaboration.""",
                "temperature": 0.5,
                "max_tokens": 1024
            }
        }
        
        # Active tasks and reasoning chains
        self.active_tasks: Dict[str, AgentTask] = {}
        self.reasoning_chains: Dict[str, List[ChainOfThought]] = {}
        self.collaboration_history: List[Dict] = []
        
        # Performance tracking
        self.stats = {
            "collaborative_sessions": 0,
            "tasks_completed": 0,
            "successful_collaborations": 0,
            "reasoning_steps": 0
        }
    
    async def process_collaborative_request(
        self,
        prompt: str,
        user: User,
        session_id: Optional[int] = None,
        require_agents: Optional[List[AgentRole]] = None,
        use_chain_of_thought: bool = True
    ) -> Dict[str, Any]:
        """
        Process a request using multi-agent collaboration.
        Features: 186, 64-65
        """
        session_uuid = f"collab_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.collaboration_history)}"
        
        logger.info(f"Starting collaborative session {session_uuid}")
        
        try:
            # Step 1: Analyze the request and determine required agents
            required_agents = require_agents or await self._determine_required_agents(prompt)
            
            # Step 2: Break down the task into subtasks
            subtasks = await self._decompose_task(prompt, required_agents)
            
            # Step 3: Execute subtasks with agent collaboration
            results = await self._execute_collaborative_tasks(
                subtasks, user, session_id, session_uuid, use_chain_of_thought
            )
            
            # Step 4: Synthesize final response
            final_response = await self._synthesize_results(prompt, results, session_uuid)
            
            # Step 5: Store collaboration for learning
            await self._store_collaboration(session_uuid, prompt, required_agents, results, final_response, user)
            
            self.stats["collaborative_sessions"] += 1
            self.stats["successful_collaborations"] += 1
            
            return {
                "response": final_response,
                "session_id": session_uuid,
                "agents_used": [agent.value for agent in required_agents],
                "subtask_results": results,
                "reasoning_chain": self.reasoning_chains.get(session_uuid, []),
                "performance_metrics": self._get_session_metrics(session_uuid)
            }
            
        except Exception as e:
            logger.error(f"Collaborative session {session_uuid} failed: {e}")
            
            # Fallback to single agent
            fallback_response = await self.codellama_engine.generate_response(
                prompt,
                agent_type="coder",
                user_id=user.id,
                session_id=session_id
            )
            
            return {
                "response": fallback_response,
                "session_id": session_uuid,
                "agents_used": ["coder"],
                "fallback_mode": True,
                "error": str(e)
            }
    
    async def _determine_required_agents(self, prompt: str) -> List[AgentRole]:
        """Analyze prompt to determine which agents are needed."""
        analysis_prompt = f"""
Analyze this request and determine which specialized agents would be most helpful:

Request: {prompt}

Available agents:
- CODER: Code generation, debugging, architecture
- RESEARCHER: Information gathering, fact-checking, analysis
- ANALYST: Data analysis, statistics, Python data science
- CREATIVE: Creative writing, brainstorming, innovative solutions

Respond with a JSON list of agent names that should collaborate on this task.
Example: ["CODER", "RESEARCHER"]
"""
        
        try:
            response = await self.codellama_engine.generate_response(
                analysis_prompt,
                agent_type="researcher",
                temperature=0.3,
                use_memory=False
            )
            
            # Extract agent names from response
            import re
            agent_pattern = r'\["([^"]+)"(?:,\s*"([^"]+)")*\]'
            match = re.search(agent_pattern, response)
            
            if match:
                agent_names = [name.strip() for name in response.split('"') if name.strip() and name.strip() != ',']
                return [AgentRole(name.lower()) for name in agent_names if name.upper() in [role.name for role in AgentRole]]
            
            # Default fallback
            if "code" in prompt.lower() or "program" in prompt.lower():
                return [AgentRole.CODER]
            elif "data" in prompt.lower() or "analysis" in prompt.lower():
                return [AgentRole.ANALYST]
            elif "research" in prompt.lower() or "find" in prompt.lower():
                return [AgentRole.RESEARCHER]
            else:
                return [AgentRole.CREATIVE, AgentRole.RESEARCHER]
                
        except Exception as e:
            logger.error(f"Agent determination failed: {e}")
            return [AgentRole.CODER, AgentRole.RESEARCHER]  # Safe default
    
    async def _decompose_task(self, prompt: str, agents: List[AgentRole]) -> List[AgentTask]:
        """Break down complex task into agent-specific subtasks."""
        decomposition_prompt = f"""
Break down this complex task into specific subtasks for different specialized agents:

Main Task: {prompt}

Available Agents: {[agent.value for agent in agents]}

For each agent, create a specific subtask they should handle. Respond in JSON format:
{{
    "subtasks": [
        {{
            "agent": "coder",
            "task": "specific task description",
            "priority": 1
        }}
    ]
}}
"""
        
        try:
            response = await self.codellama_engine.generate_response(
                decomposition_prompt,
                agent_type="coordinator",
                temperature=0.4,
                use_memory=False
            )
            
            # Parse JSON response
            import json
            import re
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                subtasks = []
                
                for i, subtask_data in enumerate(data.get("subtasks", [])):
                    agent_role = AgentRole(subtask_data["agent"])
                    task = AgentTask(
                        id=f"task_{i}",
                        role=agent_role,
                        prompt=subtask_data["task"],
                        context={"main_prompt": prompt},
                        priority=subtask_data.get("priority", 1)
                    )
                    subtasks.append(task)
                
                return subtasks
            
        except Exception as e:
            logger.error(f"Task decomposition failed: {e}")
        
        # Fallback: Create simple subtasks
        subtasks = []
        for i, agent in enumerate(agents):
            task = AgentTask(
                id=f"task_{i}",
                role=agent,
                prompt=f"Handle the {agent.value} aspects of: {prompt}",
                context={"main_prompt": prompt},
                priority=1
            )
            subtasks.append(task)
        
        return subtasks
    
    async def _execute_collaborative_tasks(
        self,
        subtasks: List[AgentTask],
        user: User,
        session_id: Optional[int],
        session_uuid: str,
        use_chain_of_thought: bool
    ) -> Dict[str, Any]:
        """Execute subtasks with inter-agent collaboration."""
        results = {}
        
        # Initialize reasoning chain for this session
        if use_chain_of_thought:
            self.reasoning_chains[session_uuid] = []
        
        # Sort tasks by priority
        subtasks.sort(key=lambda x: x.priority)
        
        for task in subtasks:
            try:
                # Add reasoning step
                if use_chain_of_thought:
                    thought = ChainOfThought(
                        step=len(self.reasoning_chains[session_uuid]) + 1,
                        agent=task.role.value,
                        thought=f"Processing task: {task.prompt[:100]}...",
                        action="generate_response",
                        result="",
                        confidence=0.8
                    )
                    self.reasoning_chains[session_uuid].append(thought)
                
                # Build context from previous results
                context_prompt = self._build_context_prompt(task, results)
                
                # Generate response using appropriate agent
                config = self.agent_configs[task.role]
                full_prompt = f"{config['system_prompt']}\n\nTask: {context_prompt}"
                
                response = await self.codellama_engine.generate_response(
                    full_prompt,
                    agent_type=task.role.value,
                    temperature=config['temperature'],
                    max_tokens=config['max_tokens'],
                    user_id=user.id,
                    session_id=session_id
                )
                
                task.result = response
                task.completed = True
                results[task.role.value] = response
                
                # Update reasoning chain
                if use_chain_of_thought and self.reasoning_chains[session_uuid]:
                    self.reasoning_chains[session_uuid][-1].result = response[:200] + "..."
                    self.reasoning_chains[session_uuid][-1].confidence = 0.9
                
                self.stats["tasks_completed"] += 1
                
                logger.info(f"Completed task for {task.role.value} agent")
                
            except Exception as e:
                logger.error(f"Task execution failed for {task.role.value}: {e}")
                task.result = f"Error: {str(e)}"
                results[task.role.value] = task.result
        
        return results
    
    def _build_context_prompt(self, current_task: AgentTask, previous_results: Dict[str, Any]) -> str:
        """Build context-aware prompt incorporating previous agent results."""
        base_prompt = current_task.prompt
        
        if not previous_results:
            return base_prompt
        
        context_parts = [f"Previous agent contributions:"]
        for agent, result in previous_results.items():
            context_parts.append(f"\n{agent.upper()}: {result[:300]}...")
        
        context_parts.append(f"\nYour specific task: {base_prompt}")
        context_parts.append("\nConsider the previous contributions while completing your task.")
        
        return "\n".join(context_parts)
    
    async def _synthesize_results(self, original_prompt: str, results: Dict[str, Any], session_uuid: str) -> str:
        """Synthesize individual agent results into coherent final response."""
        synthesis_prompt = f"""
Synthesize the following agent contributions into a comprehensive, coherent response:

Original Request: {original_prompt}

Agent Contributions:
"""
        
        for agent, result in results.items():
            synthesis_prompt += f"\n{agent.upper()}:\n{result}\n"
        
        synthesis_prompt += """
Please create a unified, well-structured response that integrates all the valuable insights from each specialist agent. Maintain clarity and avoid redundancy.
"""
        
        try:
            final_response = await self.codellama_engine.generate_response(
                synthesis_prompt,
                agent_type="coordinator",
                temperature=0.5,
                use_memory=False
            )
            
            # Add synthesis to reasoning chain
            if session_uuid in self.reasoning_chains:
                synthesis_thought = ChainOfThought(
                    step=len(self.reasoning_chains[session_uuid]) + 1,
                    agent="coordinator",
                    thought="Synthesizing all agent contributions",
                    action="synthesize",
                    result=final_response[:200] + "...",
                    confidence=0.95
                )
                self.reasoning_chains[session_uuid].append(synthesis_thought)
            
            return final_response
            
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            # Fallback: concatenate results
            return "\n\n".join([f"**{agent.upper()}:**\n{result}" for agent, result in results.items()])
    
    async def _store_collaboration(
        self,
        session_uuid: str,
        prompt: str,
        agents: List[AgentRole],
        results: Dict[str, Any],
        final_response: str,
        user: User
    ):
        """Store collaboration session for learning and analysis."""
        collaboration_data = {
            "session_id": session_uuid,
            "timestamp": datetime.now(),
            "user_id": user.id,
            "original_prompt": prompt,
            "agents_used": [agent.value for agent in agents],
            "individual_results": results,
            "final_response": final_response,
            "reasoning_chain": [
                {
                    "step": thought.step,
                    "agent": thought.agent,
                    "thought": thought.thought,
                    "action": thought.action,
                    "confidence": thought.confidence,
                    "timestamp": thought.timestamp.isoformat()
                }
                for thought in self.reasoning_chains.get(session_uuid, [])
            ]
        }
        
        self.collaboration_history.append(collaboration_data)
        
        # Store in memory for future reference
        if self.memory_manager:
            try:
                memory_content = f"Multi-agent collaboration: {prompt}\n\nFinal result: {final_response[:500]}..."
                self.memory_manager.add_memory(
                    user=user,
                    content=memory_content,
                    source="multi_agent_collaboration",
                    metadata={
                        "session_id": session_uuid,
                        "agents_used": [agent.value for agent in agents],
                        "collaboration_type": "multi_agent"
                    }
                )
            except Exception as e:
                logger.error(f"Failed to store collaboration memory: {e}")
    
    def _get_session_metrics(self, session_uuid: str) -> Dict[str, Any]:
        """Get performance metrics for a collaboration session."""
        reasoning_chain = self.reasoning_chains.get(session_uuid, [])
        
        return {
            "total_reasoning_steps": len(reasoning_chain),
            "average_confidence": sum(step.confidence for step in reasoning_chain) / len(reasoning_chain) if reasoning_chain else 0,
            "completion_time": (reasoning_chain[-1].timestamp - reasoning_chain[0].timestamp).total_seconds() if len(reasoning_chain) > 1 else 0
        }
    
    def get_collaboration_stats(self) -> Dict[str, Any]:
        """Get overall collaboration system statistics."""
        return {
            **self.stats,
            "active_sessions": len(self.reasoning_chains),
            "total_reasoning_steps": sum(len(chain) for chain in self.reasoning_chains.values()),
            "collaboration_history_size": len(self.collaboration_history)
        }
    
    async def explain_reasoning(self, session_uuid: str) -> str:
        """Explain the reasoning process for a collaboration session (Feature 69)."""
        if session_uuid not in self.reasoning_chains:
            return "No reasoning chain found for this session."
        
        chain = self.reasoning_chains[session_uuid]
        explanation = "**Reasoning Chain:**\n\n"
        
        for step in chain:
            explanation += f"**Step {step.step} - {step.agent.upper()}:**\n"
            explanation += f"Thought: {step.thought}\n"
            explanation += f"Action: {step.action}\n"
            explanation += f"Confidence: {step.confidence:.1%}\n"
            explanation += f"Result: {step.result}\n\n"
        
        return explanation
    
    def generate_counterarguments(self, topic: str, position: str) -> List[str]:
        """Generate counterarguments for a position (Feature 65, 84)."""
        # This would be implemented with the creative and researcher agents
        # working together to generate opposing viewpoints
        pass

def get_multi_agent_system(
    db: Session, 
    memory_manager: MemoryManager, 
    codellama_engine: CodeLlamaEngine
) -> MultiAgentSystem:
    """Factory function to create multi-agent system."""
    return MultiAgentSystem(db, memory_manager, codellama_engine)
