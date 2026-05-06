"""
Vector Store Service - FAISS-based vector storage for semantic search
"""
import json
import logging
import os
import pickle
from pathlib import Path
from typing import Any

import faiss
import numpy as np

from api.config import settings
from api.services.embeddings import get_embeddings_service

logger = logging.getLogger(__name__)


class VectorStore:
    """FAISS-based vector store for document embeddings"""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index: faiss.Index | None = None
        self.metadata: list[dict[str, Any]] = []
        self.embeddings_service = get_embeddings_service()
        self.store_path = Path(settings.vector_store_path)
        self._initialize()

    def _initialize(self):
        """Initialize the index"""
        self.store_path.mkdir(parents=True, exist_ok=True)

        index_path = self.store_path / "index.faiss"
        meta_path = self.store_path / "metadata.json"

        if index_path.exists() and meta_path.exists():
            try:
                self.index = faiss.read_index(str(index_path))
                with open(meta_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
                logger.info(f"Loaded existing index with {len(self.metadata)} documents")
            except Exception as e:
                logger.warning(f"Failed to load index: {e}, creating new one")
                self._create_index()
        else:
            self._create_index()

    def _create_index(self):
        """Create a new FAISS index"""
        # Use IVF index for better scalability
        quantizer = faiss.IndexFlatL2(self.dimension)
        self.index = faiss.IndexIVFFlat(quantizer, self.dimension, 100)
        self.metadata = []
        logger.info("Created new FAISS index")

    def add_documents(self, documents: list[dict[str, Any]]) -> int:
        """
        Add documents to the index

        Args:
            documents: List of document dicts with 'content', 'path', 'title'

        Returns:
            Number of documents added
        """
        if not documents:
            return 0

        # Prepare texts for embedding
        texts = [doc.get("content", "") for doc in documents]
        paths = [doc.get("path", "") for doc in documents]
        titles = [doc.get("title", "") for doc in documents]

        # Generate embeddings
        embeddings = self.embeddings_service.encode(texts)
        embeddings = embeddings.astype("float32")

        # Add to index
        if not self.index.is_trained:
            self.index.train(embeddings)

        self.index.add(embeddings)

        # Store metadata
        for i, (path, title) in enumerate(zip(paths, titles)):
            self.metadata.append({
                "path": path,
                "title": title,
                "content": texts[i][:500],  # Store preview
            })

        # Save to disk
        self._save()

        logger.info(f"Added {len(documents)} documents to index")
        return len(documents)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Search for similar documents

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of matching documents with scores
        """
        if self.index is None or self.index.ntotal == 0:
            return []

        # Generate query embedding
        query_embedding = self.embeddings_service.encode_single(query)
        query_embedding = query_embedding.reshape(1, -1).astype("float32")

        # Search
        distances, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.metadata):
                # Convert L2 distance to similarity score (0-1)
                score = 1 / (1 + dist)
                results.append({
                    **self.metadata[idx],
                    "score": float(score),
                    "distance": float(dist),
                })

        return results

    def _save(self):
        """Save index and metadata to disk"""
        if self.index is not None:
            faiss.write_index(self.index, str(self.store_path / "index.faiss"))
            with open(self.store_path / "metadata.json", "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
            logger.debug("Saved index to disk")

    def clear(self):
        """Clear the index"""
        self._create_index()
        self._save()
        logger.info("Cleared vector store")


# Singleton instance
vector_store = VectorStore()


def get_vector_store() -> VectorStore:
    """Get vector store instance"""
    return vector_store