# modules/memory/memory.py

from typing import List, Optional
from uuid import UUID
from datetime import datetime
import threading

from core.audit import audit_log
from core.config import Config
from core.rules import Rules, RuleViolation
from modules.memory.models import MemoryEntry
from modules.memory.vector_index import VectorIndex
import logging

logger = logging.getLogger("axis.memory.memory")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(Config.LOG_PATH)
fh.setFormatter(logging.Formatter("%(asctime)s | MEMORY_MODULE | %(levelname)s | %(message)s"))
logger.addHandler(fh)

# In‐memory store of MemoryEntry objects by session
# Note: For persistence, we rely on VectorIndex’s pickle of text_store; 
# but MemoryEntry metadata (tags, pinned, confidence) is currently only kept in‐RAM.
# In a production build, you'd want to serialize all MemoryEntry fields to disk (e.g. SQLite).
_memory_lock = threading.Lock()
_memory_store: dict = {}  # session_id -> List[MemoryEntry]

class AIMemory:
    """
    Facade for managing MemoryEntry lists and the VectorIndex.
    """

    def __init__(self, session_id: str):
        Rules.enforce("GOVERNED_BY_IMMUTABLE_REQUIREMENTS")
        self.session_id = session_id
        self.vector = VectorIndex(session_id)
        with _memory_lock:
            if session_id not in _memory_store:
                # Initialize store with any existing texts
                existing_texts = self.vector.get_all_texts()
                entries = []
                for txt in existing_texts:
                    entry = MemoryEntry(session_id=session_id, text=txt)
                    entries.append(entry)
                _memory_store[session_id] = entries
                logger.info(f"Initialized in‐RAM memory list for session '{session_id}'.")
            self.entries: List[MemoryEntry] = _memory_store[session_id]

    def add_memory(self, text: str, tags: Optional[List[str]] = None, pinned: bool = False) -> UUID:
        """
        Create a new MemoryEntry, add to in‐RAM list, and insert text into FAISS index.
        Returns entry_id.
        """
        try:
            entry = MemoryEntry(
                session_id=self.session_id,
                text=text,
                tags=tags or [],
                pinned=pinned
            )
            # Add to FAISS index
            idx = self.vector.add_text(text)
            with _memory_lock:
                self.entries.append(entry)
            audit_log(user_id=self.session_id, module="memory", action="add_memory", status="OK", details=str(entry.entry_id))
            logger.info(f"Added memory {entry.entry_id} for session '{self.session_id}'.")
            return entry.entry_id
        except RuleViolation as rv:
            audit_log(user_id=self.session_id, module="memory", action="add_memory", status="RULE_VIOLATION", details=str(rv))
            raise
        except Exception as e:
            audit_log(user_id=self.session_id, module="memory", action="add_memory", status="ERROR", details=str(e))
            logger.exception(f"Failed to add memory for session '{self.session_id}': {e}")
            raise

    def search_memory(self, query: str, top_k: int = 5) -> List[MemoryEntry]:
        """
        Search FAISS index for top_k similar texts. Then return corresponding MemoryEntry objects.
        """
        try:
            # Enforce Rule: NO_CODE_SIMPLIFICATION (example of rule check)
            Rules.enforce("NO_RULE_CIRCUMVENTION")

            texts = self.vector.search(query, top_k)
            found_entries = []
            with _memory_lock:
                for entry in self.entries:
                    if entry.text in texts:
                        found_entries.append(entry)
                        if len(found_entries) >= top_k:
                            break
            audit_log(user_id=self.session_id, module="memory", action="search_memory", status="OK", details=query)
            return found_entries
        except RuleViolation as rv:
            audit_log(user_id=self.session_id, module="memory", action="search_memory", status="RULE_VIOLATION", details=str(rv))
            raise
        except Exception as e:
            audit_log(user_id=self.session_id, module="memory", action="search_memory", status="ERROR", details=str(e))
            logger.exception(f"Search failed for session '{self.session_id}': {e}")
            return []

    def get_all(self) -> List[MemoryEntry]:
        """
        Return all in‐RAM MemoryEntry objects for this session.
        """
        try:
            audit_log(user_id=self.session_id, module="memory", action="get_all", status="OK", details=f"count={len(self.entries)}")
            return list(self.entries)
        except Exception as e:
            audit_log(user_id=self.session_id, module="memory", action="get_all", status="ERROR", details=str(e))
            logger.exception(f"Error fetching all memories for session '{self.session_id}': {e}")
            return []

    def delete_memory(self, entry_id: UUID) -> bool:
        """
        Delete a MemoryEntry by its UUID. Also delete from FAISS index and rebuild.
        Returns True if deleted.
        """
        try:
            with _memory_lock:
                idx_to_delete = None
                for idx, entry in enumerate(self.entries):
                    if entry.entry_id == entry_id:
                        idx_to_delete = idx
                        break
                if idx_to_delete is None:
                    return False
                # Remove from vector index and rebuild
                deleted = self.vector.delete_at(idx_to_delete)
                if not deleted:
                    return False
                # Remove from in‐RAM store
                del self.entries[idx_to_delete]
            audit_log(user_id=self.session_id, module="memory", action="delete_memory", status="OK", details=str(entry_id))
            logger.info(f"Deleted memory {entry_id} for session '{self.session_id}'.")
            return True
        except Exception as e:
            audit_log(user_id=self.session_id, module="memory", action="delete_memory", status="ERROR", details=str(e))
            logger.exception(f"Error deleting memory {entry_id} in session '{self.session_id}': {e}")
            return False

    def update_memory(self, entry_id: UUID, new_text: Optional[str] = None, tags: Optional[List[str]] = None, pinned: Optional[bool] = None) -> bool:
        """
        Update fields of a MemoryEntry. If text changes, re‐index entire session.
        """
        try:
            with _memory_lock:
                target_entry = None
                for entry in self.entries:
                    if entry.entry_id == entry_id:
                        target_entry = entry
                        break
                if not target_entry:
                    return False

                if new_text:
                    target_entry.text = new_text
                    # Rebuild entire index with updated texts
                    for idx, e in enumerate(self.entries):
                        # Replace all texts in VectorIndex
                        pass
                    self.vector.reindex()

                if tags is not None:
                    target_entry.tags = tags
                if pinned is not None:
                    target_entry.pinned = pinned

            audit_log(user_id=self.session_id, module="memory", action="update_memory", status="OK", details=str(entry_id))
            logger.info(f"Updated memory {entry_id} for session '{self.session_id}'.")
            return True
        except Exception as e:
            audit_log(user_id=self.session_id, module="memory", action="update_memory", status="ERROR", details=str(e))
            logger.exception(f"Error updating memory {entry_id} in session '{self.session_id}': {e}")
            return False

    def reindex(self):
        """
        Force FAISS index rebuild based on current in‐RAM entries.
        """
        try:
            with _memory_lock:
                texts = [e.text for e in self.entries]
            # VectorIndex.reindex() rebuilds from its own text_store, so first sync text_store
            self.vector.text_store = texts
            self.vector.reindex()
            audit_log(user_id=self.session_id, module="memory", action="reindex", status="OK")
            logger.info(f"Reindexed session '{self.session_id}'.")
        except Exception as e:
            audit_log(user_id=self.session_id, module="memory", action="reindex", status="ERROR", details=str(e))
            logger.exception(f"Reindex failed for session '{self.session_id}': {e}")
