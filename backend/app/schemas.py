from pydantic import BaseModel
from typing import Optional, List

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str

class ChatResponse(BaseModel):
    session_id: str
    reply: str
    agent: str
    citations: List[str] = []
    source_type: str = "kb"
