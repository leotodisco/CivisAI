from fastapi import Request
from src.ai_engines.embeddings_model import EmbeddingModel
from src.db.qdrant_store import QdrantStore
from src.db.redis_history_store import RedisHistoryStore
import redis

def get_redis_job_queue(request: Request):
    return request.app.state.redis_queue

def get_qdrant(request: Request) -> QdrantStore:
    return request.app.state.qdrant


def get_embedding(request: Request) -> EmbeddingModel:
    return request.app.state.embedding_model


def get_redis_client(request: Request) -> redis.Redis:
    return request.app.state.redis_client


def get_redis_rq_client(request: Request) -> redis.Redis:
    return request.app.state.redis_rq_client


def get_redis_history_store(request: Request) -> RedisHistoryStore:
    return request.app.state.redis_history_store
