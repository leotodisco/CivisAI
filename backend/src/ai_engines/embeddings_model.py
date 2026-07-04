from sentence_transformers import SentenceTransformer
from src.core.settings import get_settings
import numpy as np

class EmbeddingModel:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.model = SentenceTransformer(
                get_settings().embeddings_model_name
            )
            cls.embedding_dim = cls._instance.model.get_embedding_dimension()
        return cls._instance

    def embed(self, texts: list[str]) -> np.ndarray:
        return self.model.encode(
            texts,
            batch_size=16,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

    def embed_one(self, text: str) -> list[float]:
        return self.model.encode(
            text,
            normalize_embeddings=True,
            convert_to_numpy=True
        ).tolist()