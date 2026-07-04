from uuid import uuid4
from src.core.settings import get_settings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, Payload, VectorParams
from src.ai_engines.embeddings_model import EmbeddingModel
import numpy as np
import logging


class QdrantStore:
    def __init__(self,
                 url: str = None,
                 collection_name: str = None,
                 embedding_model: EmbeddingModel = None
                 ):
        self.url = get_settings().db_url or url
        self.client = QdrantClient(url=self.url,
                                   local_inference_batch_size=16)
        self.collection = collection_name
        self.embedder = embedding_model or EmbeddingModel()
        self._ensure_collection()

    def _ensure_collection(self):
        existing = [c.name for c in self.client.get_collections().collections]
        if self.collection not in existing:
            vector_size = self.embedder.embedding_dim

            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            logging.info(
                f"Collection '{self.collection}' creata (dim={vector_size})")

    def insert(self, text: str, vector: np.ndarray, metadata: dict) -> None:
        id = str(uuid4())
        point_payload: Payload = {
            "text": text,
            **metadata
        }
        points = PointStruct(id=id, vector=vector, payload=point_payload)
        try:
            self.client.upsert(
                collection_name=self.collection,
                points=[
                    points
                ]
            )
        except Exception as e:
            logging.error(
                f"Exception occurred while inserting in qdrant: {str(e)}")

    def search(self, query: str, k: int = 20):
        query_embedding = self.embedder.embed(query)
        try:
            return self.client.query_points(
                collection_name=self.collection,
                query=query_embedding,
                limit=k,
                with_vectors=False,
                timeout=None,
                with_payload=True
            )
        except Exception as e:
            logging.error(
                f"Exception occurred while searching in qdrant: {str(e)}")
