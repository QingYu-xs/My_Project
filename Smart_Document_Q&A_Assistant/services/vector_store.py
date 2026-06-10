"""
FAISS vector store service.
Handles building, saving, loading and searching the vector index.
"""
import os
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document


FAISS_INDEX_DIR = Path(__file__).resolve().parent.parent / "faiss_index"


class VectorStoreService:
    """Manage FAISS vector store with remote API embeddings."""

    def __init__(self, embeddings):
        self.embeddings = embeddings
        self.vector_store = None
        self._load_index()

    def _load_index(self):
        """Load existing FAISS index from disk if available."""
        index_file = FAISS_INDEX_DIR / "index.faiss"
        if index_file.exists():
            try:
                self.vector_store = FAISS.load_local(
                    str(FAISS_INDEX_DIR),
                    self.embeddings,
                    allow_dangerous_deserialization=True,
                )
            except Exception:
                self.vector_store = None

    def save_index(self):
        """Save FAISS index to disk."""
        if self.vector_store is not None:
            self.vector_store.save_local(str(FAISS_INDEX_DIR))

    def add_documents(self, documents):
        """Add documents to the vector store."""
        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(documents, self.embeddings)
        else:
            self.vector_store.add_documents(documents)
        self.save_index()

    def similarity_search(self, query, k=4):
        """Search for similar documents."""
        if self.vector_store is None:
            return []
        return self.vector_store.similarity_search(query, k=k)

    def clear(self):
        """Clear the vector store and delete index files."""
        self.vector_store = None
        if FAISS_INDEX_DIR.exists():
            for f in FAISS_INDEX_DIR.iterdir():
                f.unlink()

    def has_documents(self):
        """Check if the vector store contains documents."""
        if self.vector_store is None:
            return False
        try:
            return self.vector_store.index.ntotal > 0
        except Exception:
            return False

    def document_count(self):
        """Return number of indexed documents."""
        if self.vector_store is None:
            return 0
        try:
            return self.vector_store.index.ntotal
        except Exception:
            return 0
