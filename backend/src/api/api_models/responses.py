from pydantic import BaseModel
from typing import List, Optional

class ConversationResponseModel(BaseModel):
    conversation: List

class IndexResponseModel(BaseModel):
    status: str
    job_id: Optional[str] = None