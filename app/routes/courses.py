from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Language, Topic, TopicType
from app.schemas.course import LanguageCreate, LanguageResponse, TopicCreate, TopicResponse, TopicWithTestResponse

router = APIRouter(prefix="/languages", tags=["courses"])


@router.get("", response_model=list[LanguageResponse])
def get_languages(db: Session = Depends(get_db)):
    """Get all available programming languages"""
    languages = db.query(Language).all()
    return languages


@router.post("", response_model=LanguageResponse)
def create_language(language: LanguageCreate, db: Session = Depends(get_db)):
    """Create a new language (admin only)"""
    existing = db.query(Language).filter(Language.name == language.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Language already exists"
        )
    
    new_language = Language(name=language.name, description=language.description)
    db.add(new_language)
    db.commit()
    db.refresh(new_language)
    return new_language


@router.get("/{language_id}/topics", response_model=list[TopicWithTestResponse])
def get_language_topics(language_id: int, db: Session = Depends(get_db)):
    """Get all topics for a language"""
    language = db.query(Language).filter(Language.id == language_id).first()
    if not language:
        raise HTTPException(status_code=404, detail="Language not found")
    
    topics = db.query(Topic).filter(Topic.language_id == language_id).order_by(Topic.order).all()
    return topics


@router.post("/{language_id}/topics", response_model=TopicResponse)
def create_topic(language_id: int, topic: TopicCreate, db: Session = Depends(get_db)):
    """Create a new topic for a language (admin only)"""
    language = db.query(Language).filter(Language.id == language_id).first()
    if not language:
        raise HTTPException(status_code=404, detail="Language not found")
    
    new_topic = Topic(
        language_id=language_id,
        title=topic.title,
        description=topic.description,
        type=topic.type,
        order=topic.order,
        content=topic.content
    )
    db.add(new_topic)
    db.commit()
    db.refresh(new_topic)
    return new_topic


@router.get("/topics/{topic_id}", response_model=TopicResponse)
def get_topic(topic_id: int, db: Session = Depends(get_db)):
    """Get a specific topic"""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.patch("/topics/{topic_id}", response_model=TopicResponse)
def update_topic(topic_id: int, topic_data: TopicCreate, db: Session = Depends(get_db)):
    """Update a topic (admin only)"""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    topic.title = topic_data.title
    topic.description = topic_data.description
    topic.type = topic_data.type
    topic.order = topic_data.order
    if topic_data.content:
        topic.content = topic_data.content
    
    db.commit()
    db.refresh(topic)
    return topic
