from pydantic import BaseModel
from datetime import datetime


class LanguageCreate(BaseModel):
    name: str
    description: str


class LanguageResponse(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class TopicCreate(BaseModel):
    title: str
    description: str
    type: str
    order: int
    content: str = None


class TopicResponse(BaseModel):
    id: int
    language_id: int
    title: str
    description: str
    type: str
    order: int
    content: str = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class TopicWithTestResponse(TopicResponse):
    test_id: int = None
