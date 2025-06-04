import numpy as np
from typing import List, Dict, Optional, Union, Tuple
from datetime import datetime
import json
import base64
from sqlalchemy.orm import Session
import faiss
from sentence_transformers import SentenceTransformer
from core.config import settings
from core.database import Memory, User
from core.security import encrypt_sensitive_data, decrypt_sensitive_data
import logging
import os
import pickle
from pathlib import Path
import torch

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self, db: Session):
        self.db = db
        
        # Configure device for embedding model only - disable FAISS GPU due to compatibility issues
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f"Initializing MemoryManager with device: {self.device} (FAISS GPU disabled)")
        
        # Load embedding model with GPU support
        self.embedding_model = SentenceTransformer(
            settings.memory.embedding_model,
            device=self.device
        )
        self.vector_dimension = self.embedding_model.get_sentence_embedding_dimension()
        
        # Use CPU-only FAISS to avoid CUDA compatibility issues
        self.index = self._load_or_create_index()
        self.memory_map: Dict[int, int] = {}  # Maps memory_id to faiss index
        self._load_existing_memories()

    def _load_or_create_index(self) -> faiss.IndexFlatL2:
        """Load existing FAISS index or create a new one (CPU only for stability)."""
        index_path = Path(settings.memory.vector_db_path) / "memory.index"
        map_path = Path(settings.memory.vector_db_path) / "memory_map.pkl"
        
        if index_path.exists() and map_path.exists():
            try:
                # Always use CPU index for stability
                self.index = faiss.read_index(str(index_path))
                logger.info(f"Loaded CPU index with {self.index.ntotal} vectors")
                
                with open(map_path, 'rb') as f:
                    self.memory_map = pickle.load(f)
                return self.index
            except Exception as e:
                logger.error(f"Error loading index: {e}")
        
        # Create new CPU-only index
        logger.info("Creating new CPU FAISS index")
        return faiss.IndexFlatL2(self.vector_dimension)

    def _save_index(self):
        """Save FAISS index and memory map to disk."""
        index_path = Path(settings.memory.vector_db_path) / "memory.index"
        map_path = Path(settings.memory.vector_db_path) / "memory_map.pkl"
        
        index_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save CPU index directly
        faiss.write_index(self.index, str(index_path))
        
        with open(map_path, 'wb') as f:
            pickle.dump(self.memory_map, f)

    def _load_existing_memories(self):
        """Load existing memories from database into FAISS index."""
        memories = self.db.query(Memory).all()
        if not memories:
            return
            
        logger.info(f"Loading {len(memories)} existing memories into index")
        
        # Batch process for efficiency
        vectors = []
        for memory in memories:
            if memory.embedding_vector:
                vector = np.frombuffer(
                    base64.b64decode(memory.embedding_vector), 
                    dtype=np.float32
                ).reshape(1, -1)
                vectors.append(vector[0])
                self.memory_map[memory.id] = len(vectors) - 1
        
        if vectors:
            vectors_array = np.array(vectors, dtype=np.float32)
            self.index.add(vectors_array)
            logger.info(f"Added {len(vectors)} vectors to FAISS index")

    def add_memory(
        self,
        user: User,
        content: str,
        metadata: Optional[Dict] = None,
        source: Optional[str] = None,
        privacy_level: str = "private",
        tags: Optional[List[str]] = None,
        project_id: Optional[int] = None
    ) -> Memory:
        """Add a new memory to the system with embedding generation."""
        # Generate embedding (model may use GPU if available)
        embedding = self.embedding_model.encode([content])[0]
        
        # Ensure embedding is on CPU for storage
        if hasattr(embedding, 'cpu'):
            embedding = embedding.cpu().numpy()
        
        embedding_bytes = base64.b64encode(embedding.astype(np.float32).tobytes()).decode()
        
        # Create memory entry
        memory = Memory(
            user_id=user.id,
            content=content,
            embedding_vector=embedding_bytes,
            metadata=metadata or {},
            source=source,
            privacy_level=privacy_level,
            tags=tags or [],
            project_id=project_id
        )
        
        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)
        
        # Add to FAISS index
        self.memory_map[memory.id] = self.index.ntotal
        self.index.add(embedding.astype(np.float32).reshape(1, -1))
        self._save_index()
        
        return memory

    def search_memories(
        self,
        query: str,
        user: User,
        k: int = 5,
        privacy_levels: Optional[List[str]] = None,
        project_id: Optional[int] = None,
        min_similarity: float = 0.7
    ) -> List[Tuple[Memory, float]]:
        """Search for similar memories using embedding similarity."""
        # Generate query embedding (model may use GPU if available)
        query_vector = self.embedding_model.encode([query])[0]
        
        # Ensure vector is proper numpy array
        if hasattr(query_vector, 'cpu'):
            query_vector = query_vector.cpu().numpy()
        
        # Search in FAISS CPU index
        search_k = min(k * 3, self.index.ntotal)  # Get more candidates for filtering
        D, I = self.index.search(query_vector.astype(np.float32).reshape(1, -1), search_k)
        D, I = D[0], I[0]  # Flatten results
        
        results = []
        seen_ids = set()
        
        for dist, idx in zip(D, I):
            if idx == -1:  # No more results
                break
                
            similarity = 1 / (1 + dist)  # Convert distance to similarity score
            if similarity < min_similarity:
                continue
            
            # Find memory_id for this index
            memory_id = None
            for mid, fidx in self.memory_map.items():
                if fidx == idx:
                    memory_id = mid
                    break
            
            if not memory_id or memory_id in seen_ids:
                continue
                
            memory = self.db.query(Memory).filter(Memory.id == memory_id).first()
            if not memory:
                continue
                
            # Check access permissions
            if privacy_levels and memory.privacy_level not in privacy_levels:
                continue
                
            if memory.privacy_level == "private" and memory.user_id != user.id:
                continue
                
            if project_id and memory.project_id != project_id:
                continue
            
            seen_ids.add(memory_id)
            results.append((memory, similarity))
            
            if len(results) >= k:
                break
        
        return results

    def update_memory(
        self,
        memory_id: int,
        user: User,
        content: Optional[str] = None,
        metadata: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
        privacy_level: Optional[str] = None
    ) -> Memory:
        """Update an existing memory."""
        memory = self.db.query(Memory).filter(Memory.id == memory_id).first()
        if not memory:
            raise ValueError(f"Memory {memory_id} not found")
            
        if memory.user_id != user.id and not user.is_admin:
            raise ValueError("Not authorized to update this memory")
        
        if content:
            # Update embedding
            embedding = self.embedding_model.encode([content])[0]
            memory.embedding_vector = base64.b64encode(
                embedding.astype(np.float32).tobytes()
            ).decode()
            memory.content = content
            
            # Update FAISS index
            if memory_id in self.memory_map:
                idx = self.memory_map[memory_id]
                self.index.remove_ids(np.array([idx]))
                self.memory_map[memory_id] = self.index.ntotal
                self.index.add(embedding.reshape(1, -1))
        
        if metadata:
            memory.metadata.update(metadata)
        
        if tags:
            memory.tags = tags
            
        if privacy_level:
            memory.privacy_level = privacy_level
            
        memory.last_accessed = datetime.utcnow()
        self.db.commit()
        self._save_index()
        
        return memory

    def delete_memory(self, memory_id: int, user: User):
        """Delete a memory."""
        memory = self.db.query(Memory).filter(Memory.id == memory_id).first()
        if not memory:
            raise ValueError(f"Memory {memory_id} not found")
            
        if memory.user_id != user.id and not user.is_admin:
            raise ValueError("Not authorized to delete this memory")
        
        # Remove from FAISS index
        if memory_id in self.memory_map:
            idx = self.memory_map[memory_id]
            self.index.remove_ids(np.array([idx]))
            del self.memory_map[memory_id]
        
        self.db.delete(memory)
        self.db.commit()
        self._save_index()

    def list_memories(
        self,
        user: User,
        page: int = 1,
        limit: int = 50,
        privacy_levels: Optional[List[str]] = None,
        project_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        source: Optional[str] = None
    ) -> List[Memory]:
        """List memories with pagination and filtering."""
        query = self.db.query(Memory).filter(Memory.user_id == user.id)
        
        # Apply filters
        if privacy_levels:
            query = query.filter(Memory.privacy_level.in_(privacy_levels))
        
        if project_id is not None:
            query = query.filter(Memory.project_id == project_id)
        
        if source:
            query = query.filter(Memory.source == source)
        
        if tags:
            # Filter memories that have any of the specified tags
            for tag in tags:
                query = query.filter(Memory.tags.contains([tag]))
        
        # Order by timestamp (newest first) and paginate
        offset = (page - 1) * limit
        memories = query.order_by(Memory.timestamp.desc()).offset(offset).limit(limit).all()
        
        return memories

    def get_stats(self, user: User) -> Dict:
        """Get memory statistics for a user."""
        try:
            from sqlalchemy import func
            
            # Total memories
            total_memories = self.db.query(Memory).filter(Memory.user_id == user.id).count()
            
            # Memories by privacy level
            privacy_stats = self.db.query(
                Memory.privacy_level, func.count(Memory.id)
            ).filter(Memory.user_id == user.id).group_by(Memory.privacy_level).all()
            
            # Memories by source
            source_stats = self.db.query(
                Memory.source, func.count(Memory.id)
            ).filter(Memory.user_id == user.id).group_by(Memory.source).all()
            
            # Recent activity (last 7 days)
            from datetime import datetime, timedelta
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_memories = self.db.query(Memory).filter(
                Memory.user_id == user.id,
                Memory.timestamp >= week_ago
            ).count()
            
            # Memory size estimation
            all_memories = self.db.query(Memory).filter(Memory.user_id == user.id).all()
            total_size = sum(len(m.content.encode('utf-8')) for m in all_memories)
            
            return {
                "total_memories": total_memories,
                "recent_memories_7d": recent_memories,
                "privacy_distribution": dict(privacy_stats),
                "source_distribution": dict(source_stats),
                "total_size_bytes": total_size,
                "avg_size_bytes": total_size / max(total_memories, 1)
            }
            
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {"error": str(e)}

    def cleanup_old_memories(self, max_age_days: int = 30):
        """Clean up old, unpinned memories."""
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
        
        old_memories = self.db.query(Memory).filter(
            Memory.timestamp < cutoff_date,
            Memory.is_pinned == False
        ).all()
        
        for memory in old_memories:
            self.delete_memory(memory.id, memory.user)

    def export_memories(
        self,
        user: User,
        format: str = "json",
        privacy_levels: Optional[List[str]] = None
    ) -> Union[str, bytes]:
        """Export memories in specified format."""
        memories = self.db.query(Memory).filter(
            Memory.user_id == user.id
        )
        
        if privacy_levels:
            memories = memories.filter(Memory.privacy_level.in_(privacy_levels))
            
        memories = memories.all()
        
        if format == "json":
            export_data = []
            for memory in memories:
                memory_dict = {
                    "content": memory.content,
                    "metadata": memory.metadata,
                    "source": memory.source,
                    "timestamp": memory.timestamp.isoformat(),
                    "tags": memory.tags,
                    "privacy_level": memory.privacy_level
                }
                export_data.append(memory_dict)
            return json.dumps(export_data, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def import_memories(
        self,
        user: User,
        import_data: Union[str, bytes],
        format: str = "json"
    ) -> List[Memory]:
        """Import memories from specified format."""
        if format == "json":
            memories_data = json.loads(import_data)
            imported_memories = []
            
            for memory_data in memories_data:
                memory = self.add_memory(
                    user=user,
                    content=memory_data["content"],
                    metadata=memory_data.get("metadata"),
                    source=memory_data.get("source"),
                    privacy_level=memory_data.get("privacy_level", "private"),
                    tags=memory_data.get("tags", [])
                )
                imported_memories.append(memory)
                
            return imported_memories
        else:
            raise ValueError(f"Unsupported import format: {format}")

# Singleton instance
_memory_manager = None

def get_memory_manager(db: Session) -> MemoryManager:
    """Get or create the memory manager instance"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager(db)
    return _memory_manager

async def initialize_memory_system():
    """Initialize the memory system on startup"""
    try:
        logger.info("Initializing memory system...")
        # This would contain any startup-specific memory system initialization
        # For now, we'll just log that it's ready
        logger.info("Memory system ready")
    except Exception as e:
        logger.error(f"Memory system initialization failed: {e}")
        raise

async def cleanup_memory_system():
    """Cleanup memory system on shutdown"""
    try:
        logger.info("Cleaning up memory system...")
        global _memory_manager
        if _memory_manager:
            _memory_manager._save_index()
            _memory_manager = None
        logger.info("Memory system cleanup complete")
    except Exception as e:
        logger.error(f"Memory cleanup failed: {e}")
        raise 