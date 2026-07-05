from pydantic import BaseModel, Field
from typing import List, Optional

class IndexRequest(BaseModel):
    url: str


class ChatRequest(BaseModel):
    query: str
