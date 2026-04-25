from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserProgressResponse(BaseModel):
    id: int
    user_id: int
    topic_id: int
    status: str
    attempts: int
    passed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class TopicStartRequest(BaseModel):
    topic_id: int


class HintRequest(BaseModel):
    topic_id: int
    question: str
