import os
import sys

# Create directories
os.makedirs("app", exist_ok=True)
os.makedirs("alembic/versions", exist_ok=True)
os.makedirs("tests", exist_ok=True)

# Create app/__init__.py
open("app/__init__.py", "w").close()

# Create app/config.py
with open("app/config.py", "w") as f:
    f.write("""from pydantic_settings import BaseSettings
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
""")

# Create app/database.py
with open("app/database.py", "w") as f:
    f.write("""from sqlalchemy import create_engine
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
""")

# Create app/models.py
with open("app/models.py", "w") as f:
    f.write('''from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, Float, UniqueConstraint
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
''')

# Create app/main.py
with open("app/main.py", "w") as f:
    f.write('''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import Base, engine

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


@app.get("/")
def read_root():
    return {"message": "Smart AI Learning System API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
''')

# Create alembic files
open("alembic/__init__.py", "w").close()
open("alembic/versions/.gitkeep", "w").close()

print("✓ Project structure created successfully!")
print("✓ Run: pip install -r requirements.txt")
print("✓ Copy .env.example to .env and configure your database")
print("✓ Then run: uvicorn app.main:app --reload")
