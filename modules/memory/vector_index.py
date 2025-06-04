# modules/memory/vector_index.py

import os
import pickle
import faiss
from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np
from core.config import Config
import logging

logger = logging.getLogger("axis.memory.vector_index")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(Config.LOG_PATH)
fh.setFormatter(logging.Formatter("%(asctime)s | MEMORY_INDEX | %(levelname)s | %(message)s"))
logger.addHandler(fh)

class VectorIndex:
    """
    Maintain one FAISS index per session. 
    On disk:
      - {Config.MEMORY_PATH}_{session_id}.faiss
      - {Config.MEMORY_PATH}_{session_id}.pkl  (pickle of text_store list)
    """
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.model = SentenceTransformer(Config.VECTOR_MODEL)
        self.index = None  # type: faiss.IndexFlatL2
        self.text_store: List[str] = []
        self.index_dir = os.path.dirname(Config.MEMORY_PATH) or "db"
        os.makedirs(self.index_dir, exist_ok=True)
        self.index_path = os.path.join(self.index_dir, f"memory_{session_id}")
        self._load_index()

    def _index_file(self) -> str:
        return self.index_path + ".faiss"

    def _pkl_file(self) -> str:
        return self.index_path + ".pkl"

    def _load_index(self):
        """
        If FAISS index exists, load it along with the pickled text_store.
        Otherwise, start fresh.
        """
        try:
            if os.path.exists(self._index_file()):
                self.index = faiss.read_index(self._index_file())
                with open(self._pkl_file(), "rb") as f:
                    self.text_store = pickle.load(f)
                logger.info(f"Loaded existing index for session '{self.session_id}' ({len(self.text_store)} entries).")
            else:
                logger.info(f"No existing index for session '{self.session_id}'. Creating new.")
                self.index = None
                self.text_store = []
        except Exception as e:
            logger.exception(f"Failed to load index for session '{self.session_id}': {e}")
            self.index = None
            self.text_store = []

    def _save_index(self):
        """
        Write FAISS index and text_store to disk.
        """
        try:
            if self.index is not None:
                faiss.write_index(self.index, self._index_file())
                with open(self._pkl_file(), "wb") as f:
                    pickle.dump(self.text_store, f)
                logger.info(f"Saved index for session '{self.session_id}' ({len(self.text_store)} entries).")
        except Exception as e:
            logger.exception(f"Error saving index for session '{self.session_id}': {e}")

    def embed(self, text: str) -> np.ndarray:
        """
        Return a single embedding vector (dim = model dimension).
        """
        try:
            emb = self.model.encode([text])[0]
            return np.array(emb, dtype="float32")
        except Exception as e:
            logger.exception(f"Embedding error for session '{self.session_id}': {e}")
            raise

    def add_text(self, text: str) -> int:
        """
        Embed and add a new piece of text to the index.
        Returns the new entry's index position (int).
        """
        vec = self.embed(text)
        if self.index is None:
            dim = vec.shape[0]
            self.index = faiss.IndexFlatL2(dim)
        self.index.add(vec.reshape(1, -1))
        self.text_store.append(text)
        new_id = len(self.text_store) - 1
        self._save_index()
        return new_id

    def search(self, query: str, top_k: int = 5) -> List[str]:
        """
        Given a text query, embed and search the index, returning up to top_k matched texts.
        """
        if self.index is None or len(self.text_store) == 0:
            return []
        try:
            q_vec = self.embed(query).reshape(1, -1)
            distances, indices = self.index.search(q_vec, top_k)
            results = []
            for idx in indices[0]:
                if idx < len(self.text_store):
                    results.append(self.text_store[idx])
            return results
        except Exception as e:
            logger.exception(f"Search error for session '{self.session_id}': {e}")
            return []

    def get_all_texts(self) -> List[str]:
        return list(self.text_store)

    def delete_at(self, idx: int) -> bool:
        """
        Delete the text at index idx. Rebuild index from scratch.
        Returns True if deletion succeeded.
        """
        if 0 <= idx < len(self.text_store):
            try:
                del self.text_store[idx]
                # Rebuild index
                if len(self.text_store) > 0:
                    dim = self.embed(self.text_store[0]).shape[0]
                    self.index = faiss.IndexFlatL2(dim)
                    for t in self.text_store:
                        v = self.embed(t)
                        self.index.add(v.reshape(1, -1))
                else:
                    self.index = None
                self._save_index()
                logger.info(f"Deleted entry {idx} from session '{self.session_id}'.")
                return True
            except Exception as e:
                logger.exception(f"Error deleting entry {idx} in session '{self.session_id}': {e}")
                return False
        return False

    def reindex(self):
        """
        Force a complete rebuild of the index from text_store (useful if underlying FAISS gets corrupted).
        """
        try:
            if len(self.text_store) == 0:
                self.index = None
            else:
                first_emb = self.embed(self.text_store[0])
                dim = first_emb.shape[0]
                self.index = faiss.IndexFlatL2(dim)
                for t in self.text_store:
                    v = self.embed(t)
                    self.index.add(v.reshape(1, -1))
            self._save_index()
            logger.info(f"Rebuilt index for session '{self.session_id}'.")
        except Exception as e:
            logger.exception(f"Error reindexing session '{self.session_id}': {e}")
