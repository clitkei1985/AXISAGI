from typing import List, Dict, Optional
import logging
from sqlalchemy.orm import Session

from core.database import User
from modules.memory.memory_manager import get_memory_manager

logger = logging.getLogger(__name__)

class MemoryIntegration:
    """Handles memory integration for context-aware LLM responses."""
    
    def __init__(self, db: Session):
        self.db = db
        self.memory_manager = get_memory_manager(db)
        self.memory_enabled = True

    async def enhance_prompt(
        self,
        prompt: str,
        user: User,
        k: int = 3,
        min_similarity: float = 0.7
    ) -> str:
        """Enhance prompt with relevant memories for better context."""
        if not self.memory_enabled:
            return prompt
        
        try:
            # Search for relevant memories
            relevant_memories = self.memory_manager.search_memories(
                query=prompt,
                user=user,
                k=k,
                min_similarity=min_similarity
            )
            
            if not relevant_memories:
                return prompt
            
            # Build context from memories
            context_parts = []
            for memory, similarity in relevant_memories:
                context_parts.append(f"Memory (similarity: {similarity:.2f}): {memory.content}")
            
            context = "\n".join(context_parts)
            
            # Enhance prompt with context
            enhanced_prompt = f"""Based on the following relevant memories:

{context}

Please respond to: {prompt}

Consider the context from memories when appropriate, but don't repeat information unnecessarily."""
            
            logger.info(f"Enhanced prompt with {len(relevant_memories)} memories")
            return enhanced_prompt
            
        except Exception as e:
            logger.error(f"Error enhancing prompt: {e}")
            return prompt

    async def save_conversation_to_memory(
        self,
        user: User,
        user_message: str,
        assistant_response: str,
        session_id: Optional[int] = None
    ):
        """Save conversation exchange to memory for future context."""
        if not self.memory_enabled:
            return
        
        try:
            # Save user message
            user_memory = self.memory_manager.add_memory(
                user=user,
                content=f"User asked: {user_message}",
                metadata={
                    "type": "user_message",
                    "session_id": session_id,
                    "message_type": "question"
                },
                source="chat",
                privacy_level="private",
                tags=["conversation", "user_input"],
                project_id=None
            )
            
            # Save assistant response
            assistant_memory = self.memory_manager.add_memory(
                user=user,
                content=f"Assistant responded: {assistant_response}",
                metadata={
                    "type": "assistant_response",
                    "session_id": session_id,
                    "message_type": "answer",
                    "user_memory_id": user_memory.id
                },
                source="chat",
                privacy_level="private",
                tags=["conversation", "assistant_response"],
                project_id=None
            )
            
            logger.info(f"Saved conversation to memory: user={user_memory.id}, assistant={assistant_memory.id}")
            
        except Exception as e:
            logger.error(f"Error saving conversation to memory: {e}")

    async def get_conversation_history(
        self,
        user: User,
        session_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Get recent conversation history from memory."""
        try:
            # Search for recent conversation memories
            memories = self.memory_manager.search_memories(
                query="conversation chat",
                user=user,
                k=limit * 2,  # Get more to filter
                privacy_levels=["private"]
            )
            
            # Filter by session if provided
            if session_id:
                memories = [
                    (memory, score) for memory, score in memories
                    if memory.metadata.get("session_id") == session_id
                ]
            
            # Sort by timestamp and limit
            memories.sort(key=lambda x: x[0].timestamp, reverse=True)
            memories = memories[:limit]
            
            # Format for conversation
            conversation = []
            for memory, _ in memories:
                if memory.metadata.get("type") == "user_message":
                    conversation.append({
                        "role": "user",
                        "content": memory.content.replace("User asked: ", ""),
                        "timestamp": memory.timestamp
                    })
                elif memory.metadata.get("type") == "assistant_response":
                    conversation.append({
                        "role": "assistant",
                        "content": memory.content.replace("Assistant responded: ", ""),
                        "timestamp": memory.timestamp
                    })
            
            # Sort chronologically (oldest first)
            conversation.sort(key=lambda x: x["timestamp"])
            
            return conversation
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []

    async def find_related_topics(
        self,
        user: User,
        topic: str,
        k: int = 5
    ) -> List[Dict]:
        """Find memories related to a specific topic."""
        try:
            memories = self.memory_manager.search_memories(
                query=topic,
                user=user,
                k=k,
                min_similarity=0.6
            )
            
            related_topics = []
            for memory, similarity in memories:
                related_topics.append({
                    "content": memory.content,
                    "similarity": similarity,
                    "timestamp": memory.timestamp,
                    "tags": memory.tags,
                    "source": memory.source
                })
            
            return related_topics
            
        except Exception as e:
            logger.error(f"Error finding related topics: {e}")
            return []

    async def summarize_user_interests(
        self,
        user: User,
        limit: int = 50
    ) -> Dict:
        """Analyze user's interests based on memory content."""
        try:
            # Get recent memories
            from sqlalchemy import desc
            from core.database import Memory
            
            memories = self.db.query(Memory).filter(
                Memory.user_id == user.id
            ).order_by(desc(Memory.timestamp)).limit(limit).all()
            
            if not memories:
                return {"interests": [], "topics": [], "summary": "No data available"}
            
            # Analyze content
            all_content = " ".join([m.content for m in memories])
            all_tags = []
            for m in memories:
                if m.tags:
                    all_tags.extend(m.tags)
            
            # Count tag frequency
            from collections import Counter
            tag_counts = Counter(all_tags)
            top_tags = tag_counts.most_common(10)
            
            # Simple keyword extraction
            words = all_content.lower().split()
            word_counts = Counter(words)
            # Filter out common words
            stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "can", "i", "you", "he", "she", "it", "we", "they", "this", "that", "these", "those"}
            filtered_words = {word: count for word, count in word_counts.items() if word not in stop_words and len(word) > 3}
            top_words = Counter(filtered_words).most_common(15)
            
            return {
                "interests": [word for word, _ in top_words[:10]],
                "topics": [tag for tag, _ in top_tags],
                "summary": f"User has {len(memories)} memories with interests in {', '.join([word for word, _ in top_words[:5]])}",
                "memory_count": len(memories),
                "top_tags": top_tags[:5]
            }
            
        except Exception as e:
            logger.error(f"Error summarizing user interests: {e}")
            return {"interests": [], "topics": [], "summary": "Error analyzing interests"}

    def enable_memory(self):
        """Enable memory integration."""
        self.memory_enabled = True
        logger.info("Memory integration enabled")

    def disable_memory(self):
        """Disable memory integration."""
        self.memory_enabled = False
        logger.info("Memory integration disabled")

    def is_memory_enabled(self) -> bool:
        """Check if memory integration is enabled."""
        return self.memory_enabled

    async def get_memory_stats(self, user: User) -> Dict:
        """Get memory statistics for user."""
        try:
            from core.database import Memory
            from sqlalchemy import func
            
            total_memories = self.db.query(Memory).filter(Memory.user_id == user.id).count()
            
            # Memories by source
            source_counts = self.db.query(
                Memory.source, func.count(Memory.id)
            ).filter(Memory.user_id == user.id).group_by(Memory.source).all()
            
            # Recent activity (last 7 days)
            from datetime import datetime, timedelta
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_memories = self.db.query(Memory).filter(
                Memory.user_id == user.id,
                Memory.timestamp >= week_ago
            ).count()
            
            return {
                "total_memories": total_memories,
                "recent_memories_7d": recent_memories,
                "memories_by_source": dict(source_counts),
                "memory_enabled": self.memory_enabled
            }
            
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {"error": str(e)} 