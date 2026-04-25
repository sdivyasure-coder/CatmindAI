from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TestCreate(BaseModel):
    topic_id: int
    questions: str
    passing_percentage: float = 70.0


class TestResponse(BaseModel):
    id: int
    topic_id: int
    questions: str
    passing_percentage: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class TestStartRequest(BaseModel):
    topic_id: int


class TestSubmitRequest(BaseModel):
    test_id: int
    answers: dict


class TestResultResponse(BaseModel):
    id: int
    user_id: int
    test_id: int
    score: float
    passed: bool
    answers: str
    performance_report: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
