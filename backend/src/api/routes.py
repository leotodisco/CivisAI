from backend.src.api.api_models.requests import IndexRequest, ChatRequest
from backend.src.core.settings import get_settings
from fastapi import FastAPI, Depends
from backend.src.rag.retrieval_pipeline import RAGPipeline
from fastapi import Request, Response
from fastapi.responses import StreamingResponse
from backend.src.db.qdrant_store import QdrantStore
from backend.src.db.redis_history_store import RedisHistoryStore
from backend.src.ingestion.ingestion_pipeline import DocumentIngestionPipeline
from backend.src.ai_engines.embeddings_model import EmbeddingModel
from contextlib import asynccontextmanager
from uuid import uuid4
from logging import Logger

logger = Logger(name="API Logger")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    app.state.qdrant = QdrantStore(collection_name='rag')
    app.state.redis = RedisHistoryStore()
    app.state.embedding_model = EmbeddingModel()
    app.state.settings = get_settings()
    yield

app = FastAPI(lifespan=lifespan)


def get_qdrant(request: Request) -> QdrantStore:
    return request.app.state.qdrant


def get_embedding(request: Request) -> EmbeddingModel:
    return request.app.state.embedding_model


def get_redis(request: Request) -> RedisHistoryStore:
    return request.app.state.redis


@app.post("/index_urls",)
def index_endpoint(request: IndexRequest,
                   qdrant: QdrantStore = Depends(get_qdrant),
                   embedding: EmbeddingModel = Depends(get_embedding)):
    print(f"This is the {request}")
    pipeline = DocumentIngestionPipeline(request.urls,
                                         vector_store=qdrant,
                                         embedding_model=embedding)
    pipeline.run_pipeline()
    return Response(content="The URLS have been indexed", status_code=200)


@app.post("/chat")
async def chat_endpoint(request: ChatRequest,
                        http_request: Request,
                        qdrant: QdrantStore = Depends(get_qdrant),
                        redis: RedisHistoryStore = Depends(get_redis)):
    chat_id = http_request.headers.get("X-chat_id") or str(uuid4())
    
    rag = RAGPipeline(vector_store=qdrant, redis_store=redis)
    headers = {
        "X-Accel-Buffering": "no",
        "X-chat_id": chat_id
    }

    return StreamingResponse(
        rag.run_pipeline(request.query, chat_id=chat_id), media_type="text/event-stream", headers=headers
    )


import logging
logger = logging.getLogger(__name__)
from pydantic import BaseModel
from typing import List

class testModel(BaseModel):
    lista: List

@app.post("/full_history")
async def history_endpoint(chat_id: str,
                        redis: RedisHistoryStore = Depends(get_redis)):
    logger.info(f'METHOD INVOKED')
    history = redis.get_full_history(str(chat_id))
    serialized = [
        {"role": msg.type, "content": msg.content}
        for msg in history
    ]
    logger.info(f'{serialized=}')

    return testModel(lista=serialized)