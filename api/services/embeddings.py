"""
Embeddings Service - Generate text embeddings using sentence transformers
"""
import hashlib
import logging
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from api.config import settings

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """Service for generating text embeddings"""

    def __init__(self):
        self.model_name = settings.embedding_model
        self.device = settings.embedding_device
        self._model = None

    @property
    def model(self):
        """Lazy load the model"""
        if self._model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name, device=self.device)
        return self._model

    def encode(self, texts: list[str], **kwargs) -> np.ndarray:
        """
        Encode texts to embeddings

        Args:
            texts: List of texts to encode
            **kwargs: Additional arguments for encode

        Returns:
            numpy array of embeddings
        """
        if isinstance(texts, str):
            texts = [texts]

        embeddings = self.model.encode(texts, **kwargs)
        return embeddings

    def encode_single(self, text: str) -> np.ndarray:
        """Encode a single text"""
        return self.encode([text])[0]

    def get_text_hash(self, text: str) -> str:
        """Get a hash of the text for caching"""
        return hashlib.md5(text.encode()).hexdigest()

    def similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts"""
        emb1 = self.encode_single(text1)
        emb2 = self.encode_single(text2)

        # Cosine similarity
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)

        return float(dot_product / (norm1 * norm2))


# Singleton instance
embeddings_service = EmbeddingsService()


def get_embeddings_service() -> EmbeddingsService:
    """Get embeddings service instance"""
    return embeddings_service