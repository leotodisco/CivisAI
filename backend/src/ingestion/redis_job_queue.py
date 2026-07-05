import redis
from rq import Queue
from rq.job import Job, Retry
from src.ingestion.ingestion_pipeline import DocumentIngestionPipeline
from src.db.qdrant_store import QdrantStore
import logging

_logger = logging.getLogger(__name__)

def ingest_job(base_url: str):
    from src.ai_engines.embeddings_model import EmbeddingModel
    embedding = EmbeddingModel()
    qdrant = QdrantStore(collection_name="rag", embedding_model=embedding)

    pipeline = DocumentIngestionPipeline(
        base_url=base_url,
        embedding_model=embedding,
        vector_store=qdrant
    )

    pipeline.run_pipeline()


class RedisJobsQueue:
    def __init__(self, redis_client: redis.Redis):
        self.redis_store = redis_client
        self.queue = Queue(name='JobsQueue', 
                        connection=self.redis_store)
        
    
    def enqueue_job(self, base_url: str) -> dict:
        try:
            _logger.info(f"Ingest job with {base_url=} is starting")
            job = self.queue.enqueue(ingest_job, base_url, retry=Retry(max=3, interval=[10, 30, 60]))
            job_status = job.get_status()
            _logger.info(f"Enqueued ingest job with {base_url=} and {job_status=}")
        except Exception as e:
            _logger.error(f"Cannot ingest job with {base_url=}, error= {str(e)}")
            raise e
        return {"job_status": job_status, "job_id": job.id}


    def get_job_status(self, job_id: str) -> str:
        job = Job.fetch(job_id, connection=self.redis_store)
        return job.get_status()