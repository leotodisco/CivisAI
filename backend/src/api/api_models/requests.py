from pydantic import BaseModel, Field
from typing import List, Optional

class IndexRequest(BaseModel):
    urls: List[str]


class ChatRequest(BaseModel):
    query: str
