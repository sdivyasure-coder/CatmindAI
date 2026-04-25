#!/usr/bin/env python3
"""
Complete project setup with Phase 6: AI Integration
"""

import os
from pathlib import Path

def create_structure():
    """Create the complete project directory structure and files"""
    
    print("Creating directory structure...")
    
    directories = [
        "app", "app/routes", "app/schemas", "app/services", "app/utils",
        "alembic/versions", "tests"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {directory}/")
    
    init_files = [
        "app/__init__.py", "app/routes/__init__.py", "app/schemas/__init__.py",
        "app/services/__init__.py", "app/utils/__init__.py",
        "alembic/__init__.py", "tests/__init__.py"
    ]
    
    print("\nCreating __init__.py files...")
    for init_file in init_files:
        Path(init_file).touch()
        print(f"  ✓ {init_file}")
    
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

        "app/services/ai_service.py": '''import asyncio
import json
from typing import Optional
try:
    import openai
except ImportError:
    openai = None
from app.config import get_settings

settings = get_settings()


class AIService:
    """Service for AI-powered content generation and analysis"""
    
    @staticmethod
    async def generate_topic_content(topic_title: str, topic_description: str, topic_type: str) -> str:
        """Generate comprehensive teaching content for a topic"""
        prompt = f"""You are an expert programming instructor. Generate clear, beginner-friendly teaching content for:

Topic: {topic_title}
Description: {topic_description}
Type: {topic_type}

Create structured content with:
1. Introduction (2-3 sentences)
2. Key Concepts (3-5 bullet points)
3. Example Code (if applicable)
4. Common Mistakes (2-3 items)
5. Practice Tips

Format the response as structured text suitable for learning."""

        try:
            response = await AIService._call_gpt(prompt)
            return response
        except Exception as e:
            return f"Error generating content: {str(e)}"
    
    @staticmethod
    async def generate_test_questions(topic_title: str, topic_description: str, topic_type: str, num_questions: int = 5) -> list:
        """Generate test questions for a topic"""
        if topic_type == "theory":
            prompt = f"""Generate {num_questions} theory-based questions for the topic: {topic_title}

Description: {topic_description}

Format each question as JSON with fields:
- "question": the question text
- "type": "multiple_choice" or "short_answer"
- "difficulty": "beginner", "intermediate", or "advanced"
- "keywords": list of keywords for answer validation

Return a JSON array of questions."""
        else:  # practical
            prompt = f"""Generate {num_questions} practical coding questions for the topic: {topic_title}

Description: {topic_description}

Format each question as JSON with fields:
- "question": the problem statement
- "type": "coding"
- "difficulty": "beginner", "intermediate", or "advanced"
- "starter_code": a code template to start with
- "expected_output": example of expected output

Return a JSON array of questions."""

        try:
            response = await AIService._call_gpt(prompt)
            questions = json.loads(response)
            return questions
        except Exception as e:
            return [{"error": str(e)}]
    
    @staticmethod
    async def generate_hint(topic_title: str, question: str, difficulty: str = "beginner") -> str:
        """Generate a hint for a user struggling with a question"""
        prompt = f"""Provide a helpful hint for someone struggling with this question:

Topic: {topic_title}
Difficulty: {difficulty}
Question: {question}

Guidelines:
- Don't give away the answer
- Point them in the right direction
- Be encouraging
- 2-3 sentences maximum"""

        try:
            response = await AIService._call_gpt(prompt)
            return response
        except Exception as e:
            return f"Unable to generate hint: {str(e)}"
    
    @staticmethod
    async def analyze_answer(topic_title: str, question: str, user_answer: str, correct_answer: Optional[str] = None) -> dict:
        """Analyze and score a user's answer"""
        prompt = f"""Evaluate the following answer to a programming question:

Topic: {topic_title}
Question: {question}
User's Answer: {user_answer}
"""
        if correct_answer:
            prompt += f"Expected/Reference Answer: {correct_answer}\\n"
        
        prompt += """
Provide feedback in JSON format with:
- "is_correct": boolean
- "score": percentage (0-100)
- "feedback": detailed feedback (2-3 sentences)
- "improvements": list of suggested improvements
- "explanation": brief explanation of the correct concept

Be constructive and encouraging."""

        try:
            response = await AIService._call_gpt(prompt)
            analysis = json.loads(response)
            return analysis
        except Exception as e:
            return {
                "is_correct": False,
                "score": 0,
                "feedback": f"Error analyzing answer: {str(e)}",
                "improvements": [],
                "explanation": ""
            }
    
    @staticmethod
    async def generate_performance_report(topic_title: str, user_score: float, attempts: int, test_answers: list) -> str:
        """Generate a comprehensive performance report for a user"""
        prompt = f"""Generate a personalized performance report for a student:

Topic: {topic_title}
Score: {user_score}%
Attempts: {attempts}
Answers Submitted: {len(test_answers)}

Create a report with:
1. Performance Summary (1 sentence)
2. Strengths (1-2 sentences)
3. Areas for Improvement (1-2 sentences)
4. Recommended Next Steps (2-3 specific actions)
5. Encouragement (1 sentence)

Be specific, constructive, and motivating."""

        try:
            response = await AIService._call_gpt(prompt)
            return response
        except Exception as e:
            return f"Performance Report\\nScore: {user_score}%\\nAttempts: {attempts}\\n\\nError generating detailed report: {str(e)}"
    
    @staticmethod
    async def _call_gpt(prompt: str, max_tokens: int = 1000) -> str:
        """Internal method to call OpenAI API"""
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "sk-xxx":
            return "[AI Service Disabled - Configure OPENAI_API_KEY in .env]"
        
        if not openai:
            return "[OpenAI library not installed]"
        
        try:
            openai.api_key = settings.OPENAI_API_KEY
            response = await asyncio.to_thread(
                lambda: openai.ChatCompletion.create(
                    model=settings.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are an expert programming educator."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=0.7
                )
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"OpenAI API Error: {str(e)}")
''',

        "app/routes/ai.py": '''from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Topic
from app.services.ai_service import AIService
from app.utils.security import decode_token

router = APIRouter(prefix="/ai", tags=["ai"])


def get_current_user(authorization: str = Header(None)):
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
    
    return token_data


@router.post("/topics/{topic_id}/generate-content")
async def generate_topic_content(topic_id: int, db: Session = Depends(get_db)):
    """Generate AI-powered content for a topic"""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    content = await AIService.generate_topic_content(
        topic_title=topic.title,
        topic_description=topic.description,
        topic_type=topic.type
    )
    
    topic.content = content
    db.commit()
    db.refresh(topic)
    
    return {
        "topic_id": topic_id,
        "content": content,
        "generated": True
    }


@router.post("/topics/{topic_id}/generate-questions")
async def generate_test_questions(topic_id: int, num_questions: int = 5, db: Session = Depends(get_db)):
    """Generate AI-powered test questions for a topic"""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    questions = await AIService.generate_test_questions(
        topic_title=topic.title,
        topic_description=topic.description,
        topic_type=topic.type,
        num_questions=num_questions
    )
    
    return {
        "topic_id": topic_id,
        "questions": questions,
        "count": len(questions)
    }


@router.post("/hints/{topic_id}")
async def generate_hint(topic_id: int, question: str, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """Generate an AI hint for a question"""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    hint = await AIService.generate_hint(
        topic_title=topic.title,
        question=question,
        difficulty="intermediate"
    )
    
    return {
        "topic_id": topic_id,
        "hint": hint
    }


@router.post("/analyze-answer/{topic_id}")
async def analyze_answer(
    topic_id: int,
    question: str,
    user_answer: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI analysis of a user's answer"""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    analysis = await AIService.analyze_answer(
        topic_title=topic.title,
        question=question,
        user_answer=user_answer
    )
    
    return {
        "topic_id": topic_id,
        "analysis": analysis
    }


@router.post("/performance-report/{topic_id}")
async def generate_performance_report(
    topic_id: int,
    user_score: float,
    attempts: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate an AI-powered performance report"""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    report = await AIService.generate_performance_report(
        topic_title=topic.title,
        user_score=user_score,
        attempts=attempts,
        test_answers=[]
    )
    
    return {
        "topic_id": topic_id,
        "report": report
    }
''',

        "app/main.py": '''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import Base, engine
from app.routes import auth, courses, progress, tests, leaderboard, analytics, ai

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
app.include_router(ai.router)


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
    }
    
    print("\nCreating application files...")
    for filepath, content in files.items():
        Path(filepath).write_text(content)
        print(f"  ✓ {filepath}")
    
    print("\n" + "="*60)
    print("✅ Phase 6: AI Integration Setup Complete!")
    print("="*60)
    print("\nNew AI Endpoints:")
    print("  POST /ai/topics/{topic_id}/generate-content")
    print("  POST /ai/topics/{topic_id}/generate-questions")
    print("  POST /ai/hints/{topic_id}")
    print("  POST /ai/analyze-answer/{topic_id}")
    print("  POST /ai/performance-report/{topic_id}")

if __name__ == "__main__":
    create_structure()
