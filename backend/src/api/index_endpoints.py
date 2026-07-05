from fastapi import APIRouter, Depends, Response, Query
from src.api.api_models.responses import IndexResponseModel
from src.api.api_models.requests import IndexRequest
import logging
from src.api.container import get_redis_job_queue
from src.ingestion.redis_job_queue import RedisJobsQueue

_logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/index", response_model=IndexResponseModel, status_code=202)
def index_endpoint(request: IndexRequest,
                         redis_job_queue: RedisJobsQueue = Depends(get_redis_job_queue)):
    try:
        job_status_info = redis_job_queue.enqueue_job(request.url)
    except Exception as e:
        return IndexResponseModel(status="Cannot execute ingest")
    _logger.info(f"Ingestion started for {request.url=}")
    job_status = job_status_info.get("job_status","")
    job_id = job_status_info.get("job_id",None)
    return IndexResponseModel(status=job_status, job_id=job_id)


@router.get("/status/{job_id}")
def index_status_endpoint(
    job_id: str,
    redis_job_queue: RedisJobsQueue = Depends(get_redis_job_queue)
):
    logging.info(f"Request received with {job_id=}")
    try:
        return {"status": redis_job_queue.get_job_status(job_id)}
    except Exception as e:
        _logger.error(f"Error occurred while reading status for job {job_id}: {e}")
        return {"status": "UNKNOWN"}
    
