from src.api.api_models.requests import ChatRequest
from src.api.api_models.responses import ConversationResponseModel
from src.core.settings import get_settings
from fastapi import FastAPI, Depends
from src.rag.retrieval_pipeline import RAGPipeline
from fastapi import Request, Response
from fastapi.responses import StreamingResponse
from src.db.qdrant_store import QdrantStore
from src.db.redis_history_store import RedisHistoryStore
from src.ai_engines.embeddings_model import EmbeddingModel
from contextlib import asynccontextmanager
from uuid import uuid4
from fastapi.middleware.cors import CORSMiddleware
import logging
import redis
from src.api.container import get_qdrant, get_redis_history_store
from src.ingestion.redis_job_queue import RedisJobsQueue
from src.api.index_endpoints import router as indexing_router
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    app.state.embedding_model = EmbeddingModel()
    app.state.qdrant = QdrantStore(collection_name='rag')
    app.state.settings = get_settings()
    app.state.redis_client = redis.Redis(
        host=get_settings().redis_db_url,
        port=int(get_settings().redis_db_port or 6379),
        decode_responses=True
    )
    app.state.redis_history_store = RedisHistoryStore(redis_client=app.state.redis_client)

    app.state.redis_rq_client = redis.Redis(
        host=get_settings().redis_db_url,
        port=int(get_settings().redis_db_port or 6379),
        decode_responses=False
    )
    app.state.redis_queue = RedisJobsQueue(redis_client=app.state.redis_rq_client)
    logger.info("both redis clients created")
    
    try:
        yield
    finally:
        logging.info("Shutting down backend application...")
        del app.state.embedding_model


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(indexing_router)

@app.post("/chat")
async def chat_endpoint(request: ChatRequest,
                        http_request: Request,
                        qdrant: QdrantStore = Depends(get_qdrant),
                        redis: RedisHistoryStore = Depends(get_redis_history_store)):
    chat_id = http_request.headers.get("X-chat_id") or str(uuid4())

    rag = RAGPipeline(vector_store=qdrant, redis_store=redis)
    headers = {
        "X-Accel-Buffering": "no",
        "X-chat_id": chat_id,
        "Access-Control-Expose-Headers": "X-chat_id"
    }

    return StreamingResponse(
        rag.run_pipeline(request.query, chat_id=chat_id), media_type="text/event-stream", headers=headers
    )


@app.post("/full_history")
async def history_endpoint(chat_id: str,
                           redis: RedisHistoryStore = Depends(get_redis_history_store)):
    logger.info(f'METHOD INVOKED')
    history = redis.get_full_history(str(chat_id))
    serialized = [
        {"role": msg.type, "content": msg.content}
        for msg in history
    ]

    return ConversationResponseModel(conversation=serialized)
