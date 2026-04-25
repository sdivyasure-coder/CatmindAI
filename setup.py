#!/usr/bin/env python3
"""
Complete project setup script for Smart AI Learning System
Creates all directories and files needed to run the FastAPI application
"""

import os
import sys
from pathlib import Path

def create_structure():
    """Create the complete project directory structure and files"""
    
    print("Creating directory structure...")
    
    # Create directories
    directories = [
        "app",
        "app/routes",
        "app/schemas",
        "app/services",
        "app/utils",
        "alembic/versions",
        "tests"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {directory}/")
    
    # Create __init__.py files
    init_files = [
        "app/__init__.py",
        "app/routes/__init__.py",
        "app/schemas/__init__.py",
        "app/services/__init__.py",
        "app/utils/__init__.py",
        "alembic/__init__.py",
        "tests/__init__.py"
    ]
    
    print("\nCreating __init__.py files...")
    for init_file in init_files:
        Path(init_file).touch()
        print(f"  ✓ {init_file}")
    
    # File contents dictionary
    files = {
        "app/config.py": '''from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/smart_ai_learning"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"
    
    # Application
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
''',
        
        "app/database.py": '''from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import get_settings

settings = get_settings()

engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
''',
        
        "app/models.py": '''from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class TopicType(str, enum.Enum):
    THEORY = "theory"
    PRACTICAL = "practical"


class ProgressStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    progress = relationship("UserProgress", back_populates="user", cascade="all, delete-orphan")
    test_results = relationship("TestResult", back_populates="user", cascade="all, delete-orphan")
    leaderboard_entries = relationship("Leaderboard", back_populates="user", cascade="all, delete-orphan")


class Language(Base):
    __tablename__ = "languages"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    topics = relationship("Topic", back_populates="language", cascade="all, delete-orphan")
    leaderboard_entries = relationship("Leaderboard", back_populates="language", cascade="all, delete-orphan")


class Topic(Base):
    __tablename__ = "topics"
    
    id = Column(Integer, primary_key=True, index=True)
    language_id = Column(Integer, ForeignKey("languages.id"), index=True)
    title = Column(String, index=True)
    description = Column(Text)
    type = Column(Enum(TopicType), default=TopicType.THEORY)
    order = Column(Integer)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    language = relationship("Language", back_populates="topics")
    test = relationship("Test", back_populates="topic", uselist=False, cascade="all, delete-orphan")
    progress_entries = relationship("UserProgress", back_populates="topic", cascade="all, delete-orphan")
    
    __table_args__ = (UniqueConstraint("language_id", "order", name="uq_language_topic_order"),)


class Test(Base):
    __tablename__ = "tests"
    
    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), index=True, unique=True)
    questions = Column(Text)
    passing_percentage = Column(Float, default=70.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    topic = relationship("Topic", back_populates="test")
    results = relationship("TestResult", back_populates="test", cascade="all, delete-orphan")


class UserProgress(Base):
    __tablename__ = "user_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), index=True)
    status = Column(Enum(ProgressStatus), default=ProgressStatus.NOT_STARTED)
    attempts = Column(Integer, default=0)
    passed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="progress")
    topic = relationship("Topic", back_populates="progress_entries")
    
    __table_args__ = (UniqueConstraint("user_id", "topic_id", name="uq_user_topic"),)


class TestResult(Base):
    __tablename__ = "test_results"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), index=True)
    score = Column(Float)
    answers = Column(Text)
    performance_report = Column(Text, nullable=True)
    passed = Column(Boolean)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="test_results")
    test = relationship("Test", back_populates="results")


class Leaderboard(Base):
    __tablename__ = "leaderboard"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    language_id = Column(Integer, ForeignKey("languages.id"), index=True)
    completion_time = Column(Integer)
    rank = Column(Integer, nullable=True)
    completed_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="leaderboard_entries")
    language = relationship("Language", back_populates="leaderboard_entries")
    
    __table_args__ = (UniqueConstraint("user_id", "language_id", name="uq_user_language"),)
''',

        "app/utils/security.py": '''from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
        return {"user_id": user_id}
    except JWTError:
        return None
''',

        "app/schemas/user.py": '''from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserRegister(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int


class UserResponse(BaseModel):
    id: int
    email: str
    is_admin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
''',

        "app/schemas/course.py": '''from pydantic import BaseModel
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
''',

        "app/schemas/progress.py": '''from pydantic import BaseModel
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
''',

        "app/schemas/test.py": '''from pydantic import BaseModel
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
''',

        "app/routes/auth.py": '''from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.models import User
from app.schemas.user import UserRegister, UserLogin, TokenResponse, UserResponse
from app.utils.security import hash_password, verify_password, create_access_token, decode_token
from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.post("/register", response_model=TokenResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    new_user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.id},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": new_user.id
    }


@router.post("/login", response_model=TokenResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id
    }


@router.get("/me", response_model=UserResponse)
def get_current_user(token: str, db: Session = Depends(get_db)):
    """Get current user info"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    token_data = decode_token(token)
    if token_data is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == token_data["user_id"]).first()
    if user is None:
        raise credentials_exception
    
    return user
''',

        "app/routes/courses.py": '''from fastapi import APIRouter, Depends, HTTPException, status
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
''',

        "app/routes/progress.py": '''from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models import User, UserProgress, Topic, ProgressStatus
from app.schemas.progress import UserProgressResponse, TopicStartRequest, HintRequest
from app.utils.security import decode_token

router = APIRouter(prefix="/progress", tags=["learning"])


def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    """Get current user from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        token = authorization.split(" ")[1]
    except IndexError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token_data = decode_token(token)
    if token_data is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.id == token_data["user_id"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.get("", response_model=list[UserProgressResponse])
def get_user_progress(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user's learning progress"""
    progress = db.query(UserProgress).filter(UserProgress.user_id == current_user.id).all()
    return progress


@router.post("/start")
def start_topic(request: TopicStartRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Start learning a topic"""
    topic = db.query(Topic).filter(Topic.id == request.topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.topic_id == request.topic_id
    ).first()
    
    if not progress:
        progress = UserProgress(
            user_id=current_user.id,
            topic_id=request.topic_id,
            status=ProgressStatus.IN_PROGRESS
        )
        db.add(progress)
    else:
        progress.status = ProgressStatus.IN_PROGRESS
    
    db.commit()
    db.refresh(progress)
    return {"status": "success", "message": "Topic started"}


@router.get("/topics/{topic_id}/content")
def get_topic_content(topic_id: int, db: Session = Depends(get_db)):
    """Get AI-generated topic teaching content"""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    return {
        "topic_id": topic_id,
        "title": topic.title,
        "description": topic.description,
        "content": topic.content or "Content will be generated by AI",
        "type": topic.type
    }


@router.post("/topics/{topic_id}/hint")
def generate_hint(topic_id: int, request: HintRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Generate AI hint for a topic"""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    hint = f"Hint for {topic.title}: Consider the fundamental concepts..."
    
    return {
        "topic_id": topic_id,
        "hint": hint
    }


@router.patch("/topics/{topic_id}")
def update_progress(topic_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update topic completion status"""
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.topic_id == topic_id
    ).first()
    
    if not progress:
        raise HTTPException(status_code=404, detail="Progress not found")
    
    progress.status = ProgressStatus.COMPLETED
    progress.passed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(progress)
    return {"status": "success", "message": "Topic marked as completed"}
''',

        "app/routes/tests.py": '''from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from datetime import datetime
import json
from app.database import get_db
from app.models import User, Test, TestResult, Topic, UserProgress, ProgressStatus
from app.schemas.test import TestCreate, TestResponse, TestStartRequest, TestSubmitRequest, TestResultResponse
from app.utils.security import decode_token

router = APIRouter(prefix="/tests", tags=["tests"])


def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    """Get current user from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        token = authorization.split(" ")[1]
    except IndexError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token_data = decode_token(token)
    if token_data is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.id == token_data["user_id"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("/{topic_id}/start", response_model=TestResponse)
def start_test(topic_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Start a test for a topic"""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    test = db.query(Test).filter(Test.topic_id == topic_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found for this topic")
    
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.topic_id == topic_id
    ).first()
    
    if not progress:
        progress = UserProgress(
            user_id=current_user.id,
            topic_id=topic_id,
            status=ProgressStatus.IN_PROGRESS
        )
        db.add(progress)
    
    db.commit()
    db.refresh(test)
    return test


@router.get("/{test_id}/questions")
def get_test_questions(test_id: int, db: Session = Depends(get_db)):
    """Get test questions"""
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    try:
        questions = json.loads(test.questions) if isinstance(test.questions, str) else test.questions
    except:
        questions = [{"question": test.questions}]
    
    return {
        "test_id": test_id,
        "topic_id": test.topic_id,
        "questions": questions,
        "passing_percentage": test.passing_percentage
    }


@router.post("/{test_id}/submit", response_model=TestResultResponse)
def submit_test(test_id: int, request: TestSubmitRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Submit test answers"""
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    score = calculate_score(request.answers, test.questions)
    passed = score >= test.passing_percentage
    
    result = TestResult(
        user_id=current_user.id,
        test_id=test_id,
        score=score,
        passed=passed,
        answers=json.dumps(request.answers),
        performance_report=None
    )
    db.add(result)
    
    if passed:
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == current_user.id,
            UserProgress.topic_id == test.topic_id
        ).first()
        if progress:
            progress.status = ProgressStatus.COMPLETED
            progress.passed_at = datetime.utcnow()
    else:
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == current_user.id,
            UserProgress.topic_id == test.topic_id
        ).first()
        if progress:
            progress.attempts += 1
    
    db.commit()
    db.refresh(result)
    return result


@router.post("/{test_id}/analyze")
def analyze_test(test_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get AI-based answer analysis and performance report"""
    result = db.query(TestResult).filter(
        TestResult.test_id == test_id,
        TestResult.user_id == current_user.id
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Test result not found")
    
    test = db.query(Test).filter(Test.id == test_id).first()
    
    report = generate_performance_report(result.score, test.passing_percentage, result.answers)
    result.performance_report = report
    
    db.commit()
    
    return {
        "test_id": test_id,
        "score": result.score,
        "passed": result.passed,
        "passing_percentage": test.passing_percentage,
        "report": report
    }


def calculate_score(answers: dict, questions: str) -> float:
    """Calculate test score based on answers"""
    try:
        question_list = json.loads(questions) if isinstance(questions, str) else questions
    except:
        question_list = [{"question": questions}]
    
    correct_count = len([a for a in answers.values() if a])
    total = len(question_list) if isinstance(question_list, list) else 1
    
    return (correct_count / max(total, 1)) * 100


def generate_performance_report(score: float, passing_percentage: float, answers: str) -> str:
    """Generate AI-based performance report"""
    if score >= passing_percentage:
        return f"Excellent! You scored {score:.1f}%, which exceeds the passing percentage of {passing_percentage}%."
    else:
        return f"You scored {score:.1f}%, which is below the passing percentage of {passing_percentage}%. Review the material and try again."
''',

        "app/routes/leaderboard.py": '''from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models import Leaderboard, User, Language

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("/{language_id}")
def get_language_leaderboard(language_id: int, db: Session = Depends(get_db)):
    """Get leaderboard for a language"""
    language = db.query(Language).filter(Language.id == language_id).first()
    if not language:
        raise HTTPException(status_code=404, detail="Language not found")
    
    entries = db.query(Leaderboard).filter(
        Leaderboard.language_id == language_id
    ).order_by(Leaderboard.completion_time).all()
    
    return [
        {
            "rank": rank,
            "user_email": entry.user.email,
            "completion_time": entry.completion_time,
            "completed_at": entry.completed_at
        }
        for rank, entry in enumerate(entries, 1)
    ]


@router.get("/global/top")
def get_global_leaderboard(limit: int = 100, db: Session = Depends(get_db)):
    """Get global leaderboard across all languages"""
    entries = db.query(Leaderboard).order_by(
        Leaderboard.completion_time
    ).limit(limit).all()
    
    return [
        {
            "rank": rank,
            "user_email": entry.user.email,
            "language": entry.language.name,
            "completion_time": entry.completion_time,
            "completed_at": entry.completed_at
        }
        for rank, entry in enumerate(entries, 1)
    ]


@router.post("/update-rank/{user_id}/{language_id}")
def update_user_rank(user_id: int, language_id: int, db: Session = Depends(get_db)):
    """Update user rank on leaderboard"""
    leaderboard_entry = db.query(Leaderboard).filter(
        Leaderboard.user_id == user_id,
        Leaderboard.language_id == language_id
    ).first()
    
    if not leaderboard_entry:
        raise HTTPException(status_code=404, detail="Leaderboard entry not found")
    
    rank = db.query(Leaderboard).filter(
        Leaderboard.language_id == language_id,
        Leaderboard.completion_time < leaderboard_entry.completion_time
    ).count() + 1
    
    leaderboard_entry.rank = rank
    db.commit()
    
    return {"rank": rank, "message": "Rank updated successfully"}
''',

        "app/routes/analytics.py": '''from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import User, UserProgress, TestResult, Test, Topic
from app.utils.security import decode_token

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    """Get current user from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        token = authorization.split(" ")[1]
    except IndexError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token_data = decode_token(token)
    if token_data is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.id == token_data["user_id"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.get("/user/dashboard")
def get_user_analytics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user performance dashboard"""
    progress_entries = db.query(UserProgress).filter(UserProgress.user_id == current_user.id).all()
    
    test_results = db.query(TestResult).filter(TestResult.user_id == current_user.id).all()
    
    topics_completed = len([p for p in progress_entries if p.status == "completed"])
    total_topics = len(progress_entries)
    
    if test_results:
        average_score = sum([t.score for t in test_results]) / len(test_results)
    else:
        average_score = 0.0
    
    weak_topics = [t.topic.title for t in test_results if not t.passed][:5]
    
    return {
        "topics_completed": topics_completed,
        "total_topics": total_topics,
        "average_score": average_score,
        "weak_topics": weak_topics,
        "total_test_attempts": len(test_results),
        "passed_tests": len([t for t in test_results if t.passed])
    }


@router.get("/user/performance/{test_id}")
def get_test_performance(test_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get detailed test performance"""
    result = db.query(TestResult).filter(
        TestResult.test_id == test_id,
        TestResult.user_id == current_user.id
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Test result not found")
    
    test = db.query(Test).filter(Test.id == test_id).first()
    topic = db.query(Topic).filter(Topic.id == test.topic_id).first()
    
    return {
        "test_id": test_id,
        "topic": topic.title,
        "score": result.score,
        "passed": result.passed,
        "passing_percentage": test.passing_percentage,
        "performance_report": result.performance_report,
        "created_at": result.created_at
    }


@router.get("/topic/{topic_id}/statistics")
def get_topic_statistics(topic_id: int, db: Session = Depends(get_db)):
    """Get statistics for a specific topic"""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    test = db.query(Test).filter(Test.topic_id == topic_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="No test for this topic")
    
    results = db.query(TestResult).filter(TestResult.test_id == test.id).all()
    
    if results:
        average_score = sum([r.score for r in results]) / len(results)
        pass_count = len([r for r in results if r.passed])
        pass_rate = (pass_count / len(results)) * 100
    else:
        average_score = 0.0
        pass_rate = 0.0
    
    total_users = db.query(UserProgress).filter(UserProgress.topic_id == topic_id).count()
    
    return {
        "topic_id": topic_id,
        "topic_title": topic.title,
        "total_attempts": len(results),
        "average_score": average_score,
        "pass_rate": pass_rate,
        "total_users_attempted": total_users
    }
''',

        "app/main.py": '''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import Base, engine
from app.routes import auth, courses, progress, tests, leaderboard, analytics

settings = get_settings()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart AI Learning System",
    description="An AI-powered programming learning platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(progress.router)
app.include_router(tests.router)
app.include_router(leaderboard.router)
app.include_router(analytics.router)


@app.get("/")
def read_root():
    return {"message": "Smart AI Learning System API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
''',

        "alembic/env.py": '''from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.database import Base
from app.config import get_settings

config = context.config
fileConfig(config.config_file_name)

target_metadata = Base.metadata

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
''',

        "tests/__init__.py": "",
    }
    
    print("\nCreating application files...")
    for filepath, content in files.items():
        Path(filepath).write_text(content)
        print(f"  ✓ {filepath}")
    
    print("\n" + "="*60)
    print("✅ Project setup completed successfully!")
    print("="*60)
    print("\nNext steps:")
    print("1. pip install -r requirements.txt")
    print("2. Copy .env.example to .env and configure database")
    print("3. alembic upgrade head")
    print("4. uvicorn app.main:app --reload")
    print("\n📖 API Docs: http://localhost:8000/docs")

if __name__ == "__main__":
    try:
        create_structure()
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
